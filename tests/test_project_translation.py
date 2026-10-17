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
