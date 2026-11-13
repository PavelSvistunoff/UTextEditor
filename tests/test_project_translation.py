from threading import Event
from pathlib import Path

import pytest

from app.document.revisions import RevisionStore
import app.project.service as project_service
from app.project import Project, ProjectError
from app.project.translation import (
    commit_project_translation,
    run_project_translation,
)


class RecordingProvider:
    def __init__(self, responses=None):
        self.prompts = []
        self.options = []
        self.responses = list(responses or [])

    def generate_private(self, prompt, **options):
        self.prompts.append(prompt)
        self.options.append(options)
        if self.responses:
            response = self.responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        return f"Translated {len(self.prompts)}"


def test_translation_covers_project_titles_scene_and_note_text_and_snapshot(
    tmp_path,
):
    project = Project.create(tmp_path / "novel", "The Novel")
    chapter = project.add_chapter("First Chapter")
    scene = project.add_scene(
        "Opening", chapter_id=chapter.id, content="Disk version.\n"
    )
    note = project.add_note("Main Character", "character", content="A reference.")
    linked_note = project.add_note("Place", "setting", content="")
    project.link_note(note.id, scene.id)
    (project.root / scene.path).write_bytes(b"Disk version.\r\n")
    provider = RecordingProvider()

    translation = run_project_translation(
        provider,
        project,
        "English",
        "Ukrainian",
        {scene.id: "Unsaved scene version.\n"},
        is_cancelled=lambda: False,
    )

    assert len(provider.prompts) == 7
    assert any("The Novel" in prompt for prompt in provider.prompts)
    assert any("First Chapter" in prompt for prompt in provider.prompts)
    assert any("Opening" in prompt for prompt in provider.prompts)
    assert any("Main Character" in prompt for prompt in provider.prompts)
    assert any("Unsaved scene version." in prompt for prompt in provider.prompts)
    assert any("A reference." in prompt for prompt in provider.prompts)
    assert linked_note.id in translation.contents
    assert translation.contents[linked_note.id] == ""
    assert all(options["timeout"] == 300 for options in provider.options)

    snapshot = RevisionStore(project.root / ".utexteditor" / "revisions").read(
        translation.snapshot_path
    )
    assert snapshot.documents[scene.id] == "Unsaved scene version.\n"
    assert snapshot.documents[note.id] == "A reference."

    original_ids = {
        item.id for item in (*tuple(project.iter_scenes()), *project.manifest.notes)
    }
    original_paths = {
        item.id: item.path
        for item in (*tuple(project.iter_scenes()), *project.manifest.notes)
    }
    commit = commit_project_translation(project, translation)
    updated = commit.project

    assert updated.manifest.title == "Translated 1"
    assert next(
        item for item in updated.manifest.chapters if item.id == chapter.id
    ).title == "Translated 2"
    assert updated.get_scene(scene.id).title == "Translated 3"
    assert updated.get_note(note.id).title == "Translated 4"
    assert set(commit.persisted_contents) == original_ids
    assert updated.get_note(linked_note.id).title == "Translated 5"
    assert updated.read_scene(scene.id) == "Translated 6\r\n"
    assert updated.read_note(note.id) == "Translated 7"
    assert updated.get_scene(scene.id).path == original_paths[scene.id]
    assert updated.get_note(note.id).path == original_paths[note.id]
    assert updated.links_from(note.id)[0].target_id == scene.id


def test_translation_rejects_unsupported_directions(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")

    with pytest.raises(ProjectError, match="Only English-to-Ukrainian"):
        run_project_translation(
            RecordingProvider(),
            project,
            "French",
            "Ukrainian",
            {},
            is_cancelled=lambda: False,
        )


def test_translation_captures_grouped_and_ungrouped_scenes_in_order(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter")
    grouped = project.add_scene("Grouped", chapter_id=chapter.id, content="Saved grouped")
    ungrouped = project.add_scene("Ungrouped", content="Saved ungrouped")
    provider = RecordingProvider()

    translation = run_project_translation(
        provider, project, "English", "Ukrainian", {ungrouped.id: "Unsaved ungrouped"},
        is_cancelled=lambda: False,
    )

    snapshot = RevisionStore(project.root / ".utexteditor" / "revisions").read(translation.snapshot_path)
    assert snapshot.scene_order == (grouped.id, ungrouped.id)
    assert snapshot.documents == {grouped.id: "Saved grouped", ungrouped.id: "Unsaved ungrouped"}
    assert translation.expected_contents[ungrouped.id] == "Saved ungrouped"
    requested_text = [prompt.split("<text_to_translate>\n", 1)[1].split("\n</text_to_translate>", 1)[0]
                      for prompt in provider.prompts]
    assert requested_text == [
        "Novel", "Chapter", "Grouped", "Ungrouped", "Saved grouped", "Unsaved ungrouped"
    ]


def test_failed_translation_does_not_modify_project(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="Original.")
    original_manifest = project.manifest_path.read_bytes()
    provider = RecordingProvider([RuntimeError("model unavailable")])

    with pytest.raises(RuntimeError, match="model unavailable"):
        run_project_translation(
            provider,
            project,
            "English",
            "Ukrainian",
            {},
            is_cancelled=lambda: False,
        )

    assert project.manifest_path.read_bytes() == original_manifest
    assert project.read_scene(scene.id) == "Original."
    snapshots, issues = RevisionStore(
        project.root / ".utexteditor" / "revisions"
    ).list_snapshots()
    assert len(snapshots) == 1
    assert not issues


def test_translation_commit_conflict_preserves_entire_project(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter")
    scene = project.add_scene("Scene", chapter_id=chapter.id, content="Scene text.")
    note = project.add_note("Note", content="Note text.")
    provider = RecordingProvider()
    translation = run_project_translation(
        provider,
        project,
        "English",
        "Ukrainian",
        {},
        is_cancelled=lambda: False,
    )
    original_manifest = project.manifest_path.read_bytes()
    (project.root / note.path).write_text("External change.", encoding="utf-8")

    with pytest.raises(ProjectError, match="changed during translation"):
        commit_project_translation(project, translation)

    assert project.manifest_path.read_bytes() == original_manifest
    assert project.read_scene(scene.id) == "Scene text."
    assert project.read_note(note.id) == "External change."
    assert next(
        item
        for item in Project.open(project.root).manifest.chapters
        if item.id == chapter.id
    ).title == "Chapter"


def test_translation_commit_rolls_back_files_if_late_install_fails(
    tmp_path, monkeypatch
):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter")
    scene = project.add_scene("Scene", chapter_id=chapter.id, content="Scene text.")
    note = project.add_note("Note", content="Note text.")
    character = project.add_character("Original character")
    provider = RecordingProvider()
    translation = run_project_translation(
        provider,
        project,
        "English",
        "Ukrainian",
        {},
        is_cancelled=lambda: False,
    )
    manifest_before = project.manifest_path.read_bytes()
    scene_before = (project.root / scene.path).read_bytes()
    note_before = (project.root / note.path).read_bytes()
    original_rename = Path.rename

    def fail_manifest_install(path, target):
        if path.name.endswith(".tmp") and Path(target) == project.manifest_path:
            raise OSError("simulated manifest installation failure")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_manifest_install)

    with pytest.raises(ProjectError, match="Could not apply project translation"):
        commit_project_translation(project, translation)

    assert project.manifest_path.read_bytes() == manifest_before
    assert (project.root / scene.path).read_bytes() == scene_before
    assert (project.root / note.path).read_bytes() == note_before
    assert next(
        item
        for item in Project.open(project.root).manifest.chapters
        if item.id == chapter.id
    ).title == "Chapter"
    assert not list(project.root.rglob("*.bak"))
    assert not list(project.root.rglob("*.tmp"))


def test_translation_cancellation_stops_before_translating_next_field(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("Scene", content="Scene text.")
    cancelled = Event()

    def cancel_after_first(message):
        if message.startswith("Translated project title"):
            cancelled.set()

    provider = RecordingProvider()
    with pytest.raises(ProjectError, match="cancelled"):
        run_project_translation(
            provider,
            project,
            "English",
            "Ukrainian",
            {},
            is_cancelled=cancelled.is_set,
            progress=cancel_after_first,
        )

    assert len(provider.prompts) == 1
    assert project.manifest.title == "Novel"


def character_project(tmp_path, *, grouped=False):
    from app.project.model import (
        CHARACTER_ARC_FIELDS, CHARACTER_BACKGROUND_FIELDS, CHARACTER_PERSONALITY_FIELDS,
        CharacterGoal, CharacterKnowledge, CharacterRelationship,
        CharacterStateChange, SceneCharacterAssociation,
    )
    from uuid import uuid4

    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter") if grouped else None
    scene = project.add_scene("Scene", chapter_id=chapter.id if chapter else None, content="A character returns.")
    character = project.add_character("Mara")
    character.display_name = "The visitor"
    character.aliases = ["Watcher", "Traveller"]
    character.role = "protagonist"
    character.description = "A quiet visitor"
    character.background = {key: f"Background {key}" for key in sorted(CHARACTER_BACKGROUND_FIELDS)}
    character.personality = {key: [f"First {key}", f"Second {key}"] for key in sorted(CHARACTER_PERSONALITY_FIELDS)}
    character.primary_motivation = "Find home"
    for name in ("secondary_motivations", "desires", "needs", "obstacles", "accepted_risks", "refusals", "internal_conflicts"):
        setattr(character, name, [f"First {name}", f"Second {name}"])
    character.goals = [CharacterGoal("Return home", "blocked", 2, "Needs a guide")]
    character.knowledge = [CharacterKnowledge("conceals", "The door is open")]
    character.arc = {key: f"Arc {key}" for key in sorted(CHARACTER_ARC_FIELDS)}
    project.update_character(character.id, character)
    other = project.add_character("Guide")
    relationship = CharacterRelationship(
        str(uuid4()), character.id, other.id, "rival", "Old rivals", "Distrustful", 42,
        "estranged", "Met at school", "A hidden key", "Learn to cooperate",
    )
    project.add_character_relationship(relationship)
    association = SceneCharacterAssociation(
        character.id, "mentioned", "Find the guide", ["Return home"], ["Grows wary"],
        [CharacterStateChange("current_state", "Wary", "Trusting", "She turned away.")],
    )
    project.associate_character(scene.id, association)
    project.save()
    return project, scene.id, character.id, other.id, relationship.id


class CharacterTranslationProvider(RecordingProvider):
    def generate_private(self, prompt, **options):
        self.prompts.append(prompt)
        self.options.append(options)
        source = prompt.split("<text_to_translate>\n", 1)[1].rsplit("\n</text_to_translate>", 1)[0]
        return "П: " + source


@pytest.mark.parametrize("grouped", [False, True])
@pytest.mark.parametrize("source,target", [("English", "Ukrainian"), ("Ukrainian", "English")])
def test_translation_includes_all_character_text_and_preserves_structured_values(tmp_path, grouped, source, target):
    project, scene_id, character_id, other_id, relationship_id = character_project(tmp_path, grouped=grouped)
    before = project.manifest.to_mapping()
    provider = CharacterTranslationProvider()
    translation = run_project_translation(
        provider, project, source, target, {}, is_cancelled=lambda: False,
    )
    assert project.manifest.to_mapping() == before
    snapshot = RevisionStore(project.root / ".utexteditor" / "revisions").read(translation.snapshot_path)
    assert snapshot.structure == before
    updated = commit_project_translation(project, translation).project
    character = updated.get_character(character_id)
    assert character.full_name == "П: Mara"
    assert character.display_name == "П: The visitor"
    assert character.aliases == ["П: Watcher", "П: Traveller"]
    assert character.role == "П: protagonist"
    assert character.description == "П: A quiet visitor"
    assert character.primary_motivation == "П: Find home"
    for name in ("secondary_motivations", "desires", "needs", "obstacles", "accepted_risks", "refusals", "internal_conflicts"):
        assert getattr(character, name) == [f"П: First {name}", f"П: Second {name}"]
    assert all(value.startswith("П: Background ") for value in character.background.values())
    assert all(all(value.startswith("П: ") for value in values) for values in character.personality.values())
    assert all(value.startswith("П: Arc ") for value in character.arc.values())
    assert (character.goals[0].description, character.goals[0].notes) == ("П: Return home", "П: Needs a guide")
    assert (character.goals[0].status, character.goals[0].priority) == ("blocked", 2)
    assert (character.knowledge[0].kind, character.knowledge[0].statement) == ("conceals", "П: The door is open")
    relationship = updated.manifest.character_relationships[0]
    assert (relationship.id, relationship.source_id, relationship.target_id, relationship.trust) == (relationship_id, character_id, other_id, 42)
    for name in ("relationship_type", "description", "attitude", "status", "history", "shared_secrets", "development_notes"):
        assert getattr(relationship, name).startswith("П: ")
    association = updated.get_scene(scene_id).character_associations[0]
    assert (association.character_id, association.presence) == (character_id, "mentioned")
    assert association.purpose == "П: Find the guide"
    assert association.relevant_goals == ["П: Return home"]
    assert association.development_notes == ["П: Grows wary"]
    change = association.state_changes[0]
    assert (change.field, change.value, change.previous_value, change.evidence) == (
        "current_state", "П: Wary", "П: Trusting", "П: She turned away.",
    )
    assert updated.get_character(other_id).full_name == "П: Guide"
    assert character.portrait == ""


@pytest.mark.parametrize("failure", ["error", "cancel", "invalid_name"])
def test_character_translation_failure_or_cancellation_preserves_project(tmp_path, failure):
    project, scene_id, character_id, *_ = character_project(tmp_path)
    manifest_before = project.manifest_path.read_bytes()
    cancelled = Event()

    class Provider(CharacterTranslationProvider):
        def generate_private(self, prompt, **options):
            source = prompt.split("<text_to_translate>\n", 1)[1].rsplit("\n</text_to_translate>", 1)[0]
            if source == "Mara" and failure == "invalid_name":
                return "Invalid\nname"
            if source == "Find home":
                if failure == "error":
                    raise RuntimeError("character model failure")
                cancelled.set()
            return super().generate_private(prompt, **options)

    expected = RuntimeError if failure == "error" else ProjectError
    with pytest.raises(expected):
        run_project_translation(
            Provider(), project, "English", "Ukrainian", {}, is_cancelled=cancelled.is_set,
        )
    assert project.manifest_path.read_bytes() == manifest_before
    assert project.read_scene(scene_id) == "A character returns."
    assert project.get_character(character_id).primary_motivation == "Find home"
    snapshots, issues = RevisionStore(project.root / ".utexteditor" / "revisions").list_snapshots()
    assert len(snapshots) == 1 and not issues


@pytest.mark.parametrize("alteration", ["omit", "identifier", "portrait"])
def test_character_translation_rejects_partial_or_metadata_field_updates(tmp_path, alteration):
    from dataclasses import replace

    project, scene_id, character_id, *_ = character_project(tmp_path)
    translation = run_project_translation(
        CharacterTranslationProvider(), project, "English", "Ukrainian", {}, is_cancelled=lambda: False,
    )
    manifest_before = project.manifest_path.read_bytes()
    fields = translation.character_fields
    if alteration == "omit":
        fields = fields[1:]
    else:
        first = fields[0]
        path = ("characters", 0, "id" if alteration == "identifier" else "portrait")
        fields = (replace(first, source=replace(first.source, path=path)), *fields[1:])
    with pytest.raises(ProjectError, match="character text field"):
        commit_project_translation(project, replace(translation, character_fields=fields))
    assert project.manifest_path.read_bytes() == manifest_before
    assert project.read_scene(scene_id) == "A character returns."
    assert Project.open(project.root).get_character(character_id).full_name == "Mara"


def test_character_edits_after_generation_discard_complete_translation(tmp_path):
    project, scene_id, character_id, *_ = character_project(tmp_path)
    translation = run_project_translation(
        CharacterTranslationProvider(), project, "English", "Ukrainian", {}, is_cancelled=lambda: False,
    )
    changed = project.get_character(character_id)
    changed.aliases.append("New author alias")
    project.update_character(character_id, changed)
    manifest_after_edit = project.manifest_path.read_bytes()
    with pytest.raises(ProjectError, match="changed during translation"):
        commit_project_translation(project, translation)
    assert project.manifest_path.read_bytes() == manifest_after_edit
    assert project.read_scene(scene_id) == "A character returns."
    assert translation.expected_manifest["characters"][0]["aliases"] == ["Watcher", "Traveller"]


@pytest.mark.parametrize("limit", ["fields", "length"])
def test_character_translation_limits_fail_before_snapshot_or_model(tmp_path, monkeypatch, limit):
    import app.project.translation as service

    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    character.description = "x" * 21
    project.update_character(character.id, character)
    monkeypatch.setattr(service, "MAX_TRANSLATION_ITEMS" if limit == "fields" else "MAX_TRANSLATION_INPUT_LENGTH", 2 if limit == "fields" else 20)
    provider = CharacterTranslationProvider()
    before = project.manifest_path.read_bytes()
    with pytest.raises(ProjectError, match="limit"):
        run_project_translation(provider, project, "English", "Ukrainian", {}, is_cancelled=lambda: False)
    assert not provider.prompts
    assert not (project.root / ".utexteditor" / "revisions").exists()
    assert project.manifest_path.read_bytes() == before


def test_character_blanks_portrait_and_schema_values_are_not_sent_for_translation(tmp_path):
    import base64

    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    character.description = " \n "
    character.portrait = base64.b64encode(b"\x89PNG\r\n\x1a\nportrait bytes").decode()
    project.update_character(character.id, character)
    provider = CharacterTranslationProvider()
    translation = run_project_translation(provider, project, "English", "Ukrainian", {}, is_cancelled=lambda: False)
    assert len(provider.prompts) == 3  # Project title, name and free-text role.
    assert all(character.portrait not in prompt and character.id not in prompt for prompt in provider.prompts)
    updated = commit_project_translation(project, translation).project.get_character(character.id)
    assert updated.portrait == character.portrait
    assert updated.description == " \n "
    assert updated.background == {} and updated.goals == []
