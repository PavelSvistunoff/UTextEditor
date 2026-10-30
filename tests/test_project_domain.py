from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
from threading import Event, Thread, current_thread
from uuid import uuid4

import pytest
import yaml

import app.project.service as project_service
from app.project import (
    Chapter,
    Manifest,
    Project,
    ProjectError,
    ProjectFormatError,
    ProjectPathError,
    count_words,
    CharacterGoal,
    CharacterKnowledge,
    CharacterRelationship,
    CharacterStateChange,
    SceneCharacterAssociation,
    validate_project_path,
)


def test_create_open_and_versioned_manifest(tmp_path):
    root = tmp_path / "Novel"
    project = Project.create(root, "My Novel")

    assert (root / "manuscript").is_dir()
    assert (root / "notes").is_dir()
    assert Project.open(root).manifest == project.manifest
    data = yaml.safe_load((root / "utexteditor.yaml").read_text(encoding="utf-8"))
    assert data["format_version"] == 1
    assert data["title"] == "My Novel"


def test_character_data_round_trips_and_legacy_manifest_is_not_rewritten(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    original = project.manifest_path.read_bytes()
    reopened = Project.open(project.root)
    assert reopened.manifest_path.read_bytes() == original
    left = reopened.add_character("Mara")
    right = reopened.add_character("Ivo")
    left.primary_motivation = "Expose the council"
    left.goals = [CharacterGoal("Find the ledger")]
    left.knowledge = [CharacterKnowledge("does_not_know", "The witness survived")]
    reopened.update_character(left.id, left)
    reopened.add_character_relationship(CharacterRelationship(
        str(uuid4()), left.id, right.id, relationship_type="rival", trust=20
    ))
    scene = reopened.add_scene("Confrontation")
    reopened.associate_character(scene.id, SceneCharacterAssociation(left.id, purpose="force a choice"))
    loaded = Project.open(reopened.root)
    assert loaded.get_character(left.id).goals[0].description == "Find the ledger"
    assert loaded.get_scene(scene.id).character_associations[0].character_id == left.id
    assert loaded.manifest.character_relationships[0].target_id == right.id


def test_removing_character_cleans_relationships_and_scene_references(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    other = project.add_character("Ivo")
    project.add_character_relationship(CharacterRelationship(str(uuid4()), character.id, other.id))
    scene = project.add_scene("Scene")
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    project.remove_character(character.id)
    assert not project.manifest.character_relationships
    assert not project.get_scene(scene.id).character_associations


def test_scene_character_association_can_be_removed_without_deleting_profile(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    scene = project.add_scene("Scene")
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    project.unassociate_character(scene.id, character.id)
    assert not project.get_scene(scene.id).character_associations
    assert project.get_character(character.id).full_name == "Mara"


def test_character_relationship_can_be_edited_and_removed(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    first = project.add_character("Mara")
    second = project.add_character("Ivo")
    relationship = CharacterRelationship(str(uuid4()), first.id, second.id, relationship_type="rival")
    project.add_character_relationship(relationship)

    edited = project.manifest.character_relationships[0]
    edited.relationship_type = "reluctant ally"
    edited.trust = 35
    project.update_character_relationship(relationship.id, edited)
    assert project.manifest.character_relationships[0].relationship_type == "reluctant ally"
    assert project.manifest.character_relationships[0].trust == 35

    project.remove_character_relationship(relationship.id)
    assert project.manifest.character_relationships == []


def test_character_profile_import_export_round_trip_uses_new_stable_id(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    character.aliases = ["The Fox"]
    character.primary_motivation = "Expose the council"
    project.update_character(character.id, character)
    exported = project.export_character(character.id, tmp_path / "mara.yaml")
    imported = project.import_character(exported)

    assert imported.id != character.id
    assert imported.full_name == character.full_name
    assert imported.aliases == ["The Fox"]
    assert imported.primary_motivation == character.primary_motivation


def test_character_profile_import_rejects_malformed_yaml_and_duplicate_keys(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    malformed = tmp_path / "malformed.yaml"
    malformed.write_text("character_format_version: 1\ncharacter_format_version: 1\ncharacter: {}\n", encoding="utf-8")

    with pytest.raises(ProjectFormatError, match="Malformed"):
        project.import_character(malformed)
    assert project.manifest.characters == []


def test_character_profile_import_rejects_oversized_input(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    oversized = tmp_path / "oversized.yaml"
    oversized.write_bytes(b" " * 1_000_001)

    with pytest.raises(ProjectFormatError, match="1 MB import limit"):
        project.import_character(oversized)

    assert project.manifest.characters == []


def test_character_profile_export_can_confirm_replacement_of_missing_target(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    destination = tmp_path / "profiles" / "mara.yaml"

    exported = project.export_character(character.id, destination, replace_existing=True)

    assert exported == destination
    assert "Mara" in destination.read_text(encoding="utf-8")


def test_find_scenes_mentioned_by_character_includes_alias_and_excerpt(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara Venn")
    character.aliases = ["the Fox"]
    project.update_character(character.id, character)
    matching = project.add_scene("Market", content="At dusk, the Fox entered the market.")
    project.add_scene("Other", content="Ivo crossed the bridge.")
    project.add_scene("Prefix only", content="Foxglove grew beside the road.")

    results = project.find_scenes_mentioning_character(character.id)

    assert [(scene.id, excerpt) for scene, excerpt in results] == [
        (matching.id, "At dusk, the Fox entered the market.")
    ]

    unsaved = project.find_scenes_mentioning_character(
        character.id, scene_texts={matching.id: "Mara Venn returns home."}
    )
    assert [(scene.id, excerpt) for scene, excerpt in unsaved] == [
        (matching.id, "Mara Venn returns home.")
    ]


def test_scene_linked_character_state_changes_round_trip_in_order(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    first = project.add_scene("First scene")
    second = project.add_scene("Second scene")
    project.associate_character(
        first.id,
        SceneCharacterAssociation(
            character.id,
            state_changes=[CharacterStateChange("knowledge", "learns the code", evidence="Finds the letter")],
        ),
    )
    project.associate_character(
        second.id,
        SceneCharacterAssociation(
            character.id,
            state_changes=[CharacterStateChange("belief", "trusts Ivo", "distrusts Ivo")],
        ),
    )

    reopened = Project.open(project.root)
    changes = [
        association.state_changes[0]
        for scene in reopened.iter_scenes()
        for association in scene.character_associations
    ]
    assert [(change.field, change.value) for change in changes] == [
        ("knowledge", "learns the code"),
        ("belief", "trusts Ivo"),
    ]
    assert reopened.character_current_state(character.id) == {
        "knowledge": "learns the code",
        "belief": "trusts Ivo",
    }


def test_rejects_broken_scene_character_reference(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene")
    data = yaml.safe_load(project.manifest_path.read_text(encoding="utf-8"))
    data["ungrouped_scenes"][0]["character_associations"] = [{"character_id": str(uuid4())}]
    project.manifest_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ProjectFormatError, match="invalid character association"):
        Project.open(project.root)


def test_character_save_detects_external_manifest_change(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    with project.manifest_path.open("a", encoding="utf-8") as stream:
        stream.write("# external edit\n")
    character.description = "Changed locally"
    with pytest.raises(ProjectError, match="changed outside"):
        project.update_character(character.id, character)
    assert project.get_character(character.id).description == ""


@pytest.mark.parametrize("field", ["goals", "knowledge"])
def test_character_validation_rejects_malformed_in_memory_collections(tmp_path, field):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    setattr(character, field, None)

    with pytest.raises(ProjectFormatError, match=f"{field} must be a list"):
        project.update_character(character.id, character)

    assert project.get_character(character.id).full_name == "Mara"


@pytest.mark.parametrize(
    "invalid_value, update",
    [
        ("bad\x00evidence", "state_change"),
        ("bad\x00note", "goal"),
        ("bad\x00statement", "knowledge"),
    ],
)
def test_character_text_fields_reject_nul_before_persisting(
    tmp_path, invalid_value, update
):
    from app.project import CharacterStateChange

    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    scene = project.add_scene("Scene")
    if update == "state_change":
        association = SceneCharacterAssociation(
            character.id,
            state_changes=[CharacterStateChange("knowledge", "learns", evidence=invalid_value)],
        )
        operation = lambda: project.associate_character(scene.id, association)
    else:
        if update == "goal":
            character.goals = [CharacterGoal("Find the key", notes=invalid_value)]
        else:
            character.knowledge = [CharacterKnowledge("knows", invalid_value)]
        operation = lambda: project.update_character(character.id, character)

    with pytest.raises(ProjectFormatError, match="must be text"):
        operation()

    assert not project.manifest.characters[0].goals
    assert not project.manifest.characters[0].knowledge


def test_create_refuses_nonempty_and_rolls_back_invalid_title(tmp_path):
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    marker = occupied / "keep.txt"
    marker.write_text("leave me", encoding="utf-8")
    with pytest.raises(ProjectError):
        Project.create(occupied, "Novel")
    assert marker.read_text(encoding="utf-8") == "leave me"

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ProjectFormatError):
        Project.create(empty, "  ")
    assert list(empty.iterdir()) == []


@pytest.mark.parametrize("path", ["../outside.txt", "/outside.txt", "a/../b", r"a\\b", "C:/outside"])
def test_rejects_unsafe_project_paths(tmp_path, path):
    with pytest.raises(ProjectPathError):
        validate_project_path(tmp_path, path)


def test_rejects_symlink_escape(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ProjectPathError):
        validate_project_path(root, "escape/secret.txt")


def test_open_rejects_unsupported_and_invalid_manifests(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    data = yaml.safe_load(project.manifest_path.read_text(encoding="utf-8"))
    data["format_version"] = 2
    project.manifest_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ProjectFormatError, match="Unsupported"):
        Project.open(project.root)

    project.manifest_path.write_text("chapters: [", encoding="utf-8")
    with pytest.raises(ProjectFormatError, match="Malformed"):
        Project.open(project.root)


def test_open_rejects_traversal_in_referenced_manifest_path(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    project.add_scene("Scene")
    data = yaml.safe_load(project.manifest_path.read_text(encoding="utf-8"))
    data["ungrouped_scenes"][0]["path"] = "../outside.txt"
    project.manifest_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ProjectFormatError, match="safe project-relative"):
        Project.open(project.root)


def test_open_rejects_duplicate_yaml_mapping_keys(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    project.manifest_path.write_text(
        "format_version: 1\nproject_id: first\ntitle: Novel\ntitle: Overwritten\n"
        "chapters: []\nungrouped_scenes: []\nnotes: []\nlinks: []\n",
        encoding="utf-8",
    )
    with pytest.raises(ProjectFormatError, match="Malformed"):
        Project.open(project.root)


def test_manifest_rejects_duplicate_ids_and_paths():
    duplicate = str(uuid4())
    manifest = Manifest(
        project_id=str(uuid4()),
        title="Novel",
        chapters=[
            Chapter(id=duplicate, title="One"),
            Chapter(id=duplicate, title="Two"),
        ],
    )
    with pytest.raises(ProjectFormatError, match="Duplicate"):
        manifest.validate()


def test_chapter_scene_crud_order_move_and_rename(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    first = project.add_chapter("First")
    second = project.add_chapter("Second")
    scene_a = project.add_scene("Opening", chapter_id=first.id, content="Hello")
    scene_b = project.add_scene("Next", chapter_id=first.id)

    project.reorder_scene(scene_b.id, 0)
    project.move_scene(scene_a.id, chapter_id=second.id)
    project.rename_scene(scene_a.id, "Beginning")
    assert [scene.id for scene in first.scenes] == [scene_b.id]
    assert [scene.id for scene in second.scenes] == [scene_a.id]
    assert project.read_scene(scene_a.id) == "Hello"

    old_file = project.root / scene_a.path
    project.rename_scene(scene_a.id, "New file name", rename_file=True)
    assert scene_a.title == "New file name"
    assert not old_file.exists()
    assert (project.root / scene_a.path).read_text(encoding="utf-8") == "Hello"

    duplicate = project.duplicate_scene(scene_a.id)
    assert duplicate.id != scene_a.id
    assert duplicate.path != scene_a.path
    assert project.read_scene(duplicate.id) == "Hello"

    project.remove_scene(duplicate.id)
    assert not any(scene.id == duplicate.id for scene in project.iter_scenes())
    assert (project.root / duplicate.path).exists()
    project.remove_scene(scene_a.id, delete_file=True)
    assert not (project.root / scene_a.path).exists()
    reopened = Project.open(project.root)
    assert [chapter.id for chapter in reopened.manifest.chapters] == [first.id, second.id]
    assert [scene.id for scene in reopened.iter_scenes()] == [scene_b.id]


def test_chapter_reorder_and_removal_requires_explicit_scene_destination(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    first = project.add_chapter("First")
    second = project.add_chapter("Second")
    scene = project.add_scene("Scene", chapter_id=first.id)

    with pytest.raises(ProjectError, match="destination"):
        project.remove_chapter(first.id)
    project.remove_chapter(first.id, move_to_ungrouped=True)
    assert scene in project.manifest.ungrouped_scenes

    project.reorder_chapter(second.id, 0)
    assert project.manifest.chapters[0].id == second.id
    project.remove_chapter(second.id)
    assert project.manifest.chapters == []
    assert (project.root / scene.path).exists()


def test_scene_import_and_failed_manifest_update_roll_back_file(tmp_path, monkeypatch):
    project = Project.create(tmp_path / "project", "Novel")
    source = project.root / "loose.txt"
    source.write_text("Imported words.", encoding="utf-8")
    scene = project.import_scene("loose.txt", title="Import")
    assert project.read_scene(scene.id) == "Imported words."
    with pytest.raises(ProjectError, match="already included"):
        project.import_scene(scene.path)

    before = list(project.iter_scenes())

    def fail_write():
        raise ProjectError("simulated manifest failure")

    monkeypatch.setattr(project, "_write_manifest", fail_write)
    with pytest.raises(ProjectError, match="simulated"):
        project.add_scene("Rollback")
    assert list(project.iter_scenes()) == before
    assert not (project.root / "manuscript/rollback.txt").exists()


def test_import_rejects_invalid_utf8_and_external_path(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    (project.root / "bad.txt").write_bytes(b"\xff")
    with pytest.raises(ProjectError, match="UTF-8"):
        project.import_scene("bad.txt")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    with pytest.raises(ProjectPathError):
        project.import_scene("../outside.txt")


def test_external_import_requires_confirmation_and_copies_text(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    source = tmp_path / "draft.txt"
    source.write_text("outside draft", encoding="utf-8")
    with pytest.raises(ProjectError, match="confirmation"):
        project.import_external_scene(source)
    scene = project.import_external_scene(source, confirmed=True)
    assert project.read_scene(scene.id) == "outside draft"
    assert source.read_text(encoding="utf-8") == "outside draft"


def test_text_saves_are_atomic_and_reject_stale_disk_snapshots(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    scene = project.add_scene("Scene", content="first")
    note = project.add_note("Note", content="reference")
    scene_path = project.root / scene.path
    scene_path.chmod(0o640)

    project.write_scene(scene.id, "edited UTF-8 — text", expected_content="first")
    assert project.read_scene(scene.id) == "edited UTF-8 — text"
    assert scene_path.stat().st_mode & 0o777 == 0o640
    (project.root / note.path).write_text("external change", encoding="utf-8")
    with pytest.raises(ProjectError, match="changed on disk"):
        project.write_note(note.id, "replacement", expected_content="reference")
    assert project.read_note(note.id) == "external change"
    assert not list((project.root / "notes").glob("*.tmp"))


def test_project_save_detects_separate_process_edit_during_staging(tmp_path, monkeypatch):
    project = Project.create(tmp_path / "project", "Novel")
    scene = project.add_scene("Scene", content="original")
    path = project.root / scene.path
    original_fsync = os.fsync
    changed = []

    def change_after_stage(fd):
        original_fsync(fd)
        if not changed:
            subprocess.run([sys.executable, "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('external edit', encoding='utf-8')", str(path)], check=True)
            changed.append(True)

    monkeypatch.setattr(project_service.os, "fsync", change_after_stage)
    with pytest.raises(ProjectError, match="during saving"):
        project.write_scene(scene.id, "my edit", expected_content="original")
    assert path.read_text(encoding="utf-8") == "external edit"
    assert not list(path.parent.glob(".scene.txt.*.tmp"))


def test_manifest_save_detects_separate_process_edit_during_staging(tmp_path, monkeypatch):
    project = Project.create(tmp_path / "project", "Novel")
    chapter = project.add_chapter("Original")
    path = project.root / "utexteditor.yaml"
    original_fsync = os.fsync
    changed = []

    def change_after_stage(fd):
        original_fsync(fd)
        if not changed:
            subprocess.run([sys.executable, "-c", "from pathlib import Path; import sys; p=Path(sys.argv[1]); p.write_bytes(p.read_bytes()+b'\\n# external edit\\n')", str(path)], check=True)
            changed.append(True)

    monkeypatch.setattr(project_service.os, "fsync", change_after_stage)
    with pytest.raises(ProjectError, match="during saving"):
        project.rename_chapter(chapter.id, "Changed")
    assert path.read_bytes().endswith(b"# external edit\n")
    assert project.manifest.chapters[0].title == "Original"
    assert not list(project.root.glob(".utexteditor.yaml.*.tmp"))


def test_project_save_serializes_compare_and_replace(tmp_path, monkeypatch):
    project = Project.create(tmp_path / "project", "Novel")
    scene = project.add_scene("Scene", content="original")
    target = project.root / scene.path
    first_replace_started = Event()
    release_first_replace = Event()
    second_started = Event()
    second_read_finished = Event()
    outcomes = {}
    original_read_bytes = Path.read_bytes
    original_replace = project_service.os.replace

    def observed_read_bytes(path):
        content = original_read_bytes(path)
        if path == target and current_thread().name == "second-save":
            second_read_finished.set()
        return content

    def pause_first_replace(source, destination):
        if (
            Path(destination) == target
            and current_thread().name == "first-save"
        ):
            first_replace_started.set()
            if not release_first_replace.wait(3):
                raise TimeoutError("Test did not release the first project save.")
        return original_replace(source, destination)

    monkeypatch.setattr(Path, "read_bytes", observed_read_bytes)
    monkeypatch.setattr(project_service.os, "replace", pause_first_replace)

    def save(label, content):
        if label == "second":
            second_started.set()
        try:
            project.write_scene(scene.id, content, expected_content="original")
        except ProjectError:
            outcomes[label] = "conflict"
        else:
            outcomes[label] = "saved"

    first = Thread(target=save, args=("first", "first edit"), name="first-save")
    second = Thread(target=save, args=("second", "second edit"), name="second-save")
    first.start()
    try:
        assert first_replace_started.wait(2)
        second.start()
        assert second_started.wait(2)
        assert not second_read_finished.wait(0.5)
    finally:
        release_first_replace.set()
        first.join(3)
        if second.ident is not None:
            second.join(3)

    assert not first.is_alive()
    assert not second.is_alive()
    assert outcomes == {"first": "saved", "second": "conflict"}
    assert project.read_scene(scene.id) == "first edit"


def test_notes_links_orphans_and_separate_word_counts(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    chapter = project.add_chapter("Chapter One")
    scene = project.add_scene(
        "Scene", chapter_id=chapter.id, content="Hello, world! l’amour state-of-the-art 你好 123"
    )
    note = project.add_note("A character", "character", content="note words are excluded")
    related = project.add_note("A setting", "setting")
    link = project.link_note(note.id, scene.id)
    project.link_note(note.id, related.id)

    assert link in project.links_from(note.id)
    assert link in project.links_to(scene.id)
    assert project.scene_word_count(scene.id).count == 6
    assert project.chapter_word_count(chapter.id).count == 6
    assert project.project_word_count().count == 6
    assert count_words("... --- 42 don't co-operate") == 3

    with pytest.raises(ProjectError, match="link"):
        project.remove_note(note.id)
    project.remove_note(note.id, keep_orphan_links=True)
    assert project.links_to(scene.id) == ()
    assert project.links_to(related.id) == ()
    assert (project.root / note.path).exists()


def test_note_retype_duplicate_links_and_delete_requires_explicit_link_choice(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    scene = project.add_scene("Scene")
    note = project.add_note("Note", content="separate")
    project.link_note(note.id, scene.id)
    duplicate = project.duplicate_note(note.id)
    assert duplicate.id != note.id
    assert project.links_from(duplicate.id) == ()
    linked_copy = project.duplicate_note(note.id, copy_links=True)
    assert project.links_from(linked_copy.id)[0].target_id == scene.id
    project.retype_note(linked_copy.id, "research")
    assert linked_copy.type == "research"
    with pytest.raises(ProjectError, match="link"):
        project.remove_scene(scene.id, delete_file=True)
    project.remove_scene(scene.id, delete_file=True, keep_orphan_links=True)
    assert project.links_to(scene.id)
    assert not (project.root / scene.path).exists()
    assert Project.open(project.root).links_to(scene.id)


def test_missing_scene_makes_counts_incomplete_and_reorder_preserves_count(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    chapter = project.add_chapter("Chapter")
    one = project.add_scene("One", chapter_id=chapter.id, content="one two")
    two = project.add_scene("Two", chapter_id=chapter.id, content="three")
    project.reorder_scene(two.id, 0)
    assert project.project_word_count().count == 3
    (project.root / one.path).unlink()
    result = project.project_word_count()
    assert result.count == 1
    assert not result.complete


def test_relink_and_confirmed_recreate_preserve_entry_ids(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    scene = project.add_scene("Scene", content="original")
    note = project.add_note("Reference", content="note")
    scene_id, note_id = scene.id, note.id
    original_scene_path = scene.path
    (project.root / scene.path).unlink()

    with pytest.raises(ProjectError, match="confirmation"):
        project.recreate_scene(scene.id)
    project.recreate_scene(scene.id, confirmed=True)
    assert project.get_scene(scene_id).id == scene_id
    assert project.read_scene(scene_id) == ""

    replacement = project.root / "manuscript/replacement.txt"
    replacement.write_text("restored words", encoding="utf-8")
    project.relink_scene(scene.id, "manuscript/replacement.txt")
    assert project.read_scene(scene_id) == "restored words"
    assert scene.path != original_scene_path

    (project.root / note.path).unlink()
    project.recreate_note(note.id, confirmed=True)
    assert project.get_note(note_id).id == note_id
    assert project.read_note(note_id) == ""


def test_project_text_reads_and_saves_preserve_crlf_bytes(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    scene = project.add_scene("Scene", content="first\nsecond\n")
    target = project.root / scene.path
    target.write_bytes(b"first\r\nsecond\r\n")

    original = project.read_scene(scene.id)
    assert original == "first\r\nsecond\r\n"

    project.write_scene(
        scene.id,
        "first\r\nedited\r\n",
        expected_content=original,
    )

    assert target.read_bytes() == b"first\r\nedited\r\n"


def test_existing_symlink_manifest_is_rejected(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    other = Project.create(tmp_path / "other", "Other")
    (root / "utexteditor.yaml").symlink_to(other.manifest_path)
    with pytest.raises(ProjectPathError):
        Project.open(root)
