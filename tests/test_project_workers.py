"""Project worker behavior can be verified without constructing Qt widgets."""

import pytest

from app.document.export import ExportChapter, ExportScene
from app.document.recovery import RecoveryStore
from app.project import Project
from app.project.manuscript import export_project_snapshot, compile_project_book_snapshot
from app.project.recovery import prepare_recovery_restore


@pytest.mark.parametrize("failure", ["changed", "missing_item", "wrong_project", "unavailable"])
def test_project_recovery_failures_preserve_text_as_untitled(tmp_path, failure):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="saved")
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("recovery-id", "unsaved", canonical_path=project.root / scene.path,
                       project_path=project.root, project_id=project.manifest.project_id,
                       project_item_id=scene.id, project_item_kind="scene")
    located = None
    if failure == "changed":
        (project.root / scene.path).write_text("external", encoding="utf-8")
    elif failure == "missing_item":
        project.remove_scene(scene.id)
    elif failure == "wrong_project":
        project.root.rename(tmp_path / "original")
        located = Project.create(tmp_path / "other", "Other").root
    else:
        project.root.rename(tmp_path / "original")
    _, document, error = prepare_recovery_restore(store, (entry,), located)[0]
    assert error and document.path is None and document.text == "unsaved" and document.dirty
    assert entry.snapshot_path.exists()



def test_selected_scene_export_does_not_read_unselected_scene(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter One")
    included = project.add_scene("Included", chapter_id=chapter.id, content="Export this.")
    excluded = project.add_scene("Excluded", chapter_id=chapter.id, content="Unavailable.")
    (project.root / project.get_scene(excluded.id).path).unlink()

    output = export_project_snapshot(
        project,
        [ExportChapter("Chapter One", (
            ExportScene(included.id, "Included"),
            ExportScene(excluded.id, "Excluded"),
        ))],
        [],
        {},
        tmp_path / "selected.md",
        "markdown",
        False,
        {included.id},
        True,
        True,
        "\n\n",
    )

    assert output.read_text(encoding="utf-8") == (
        "# Chapter One\n\n## Included\n\nExport this."
    )



def test_export_workers_reject_project_source_destinations(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="keep scene")
    note = project.add_note("Note", content="keep note")
    scene_path = project.root / scene.path
    note_path = project.root / note.path
    hardlink = tmp_path / "linked.md"
    hardlink.hardlink_to(scene_path)
    symlink = tmp_path / "linked-note.md"
    symlink.symlink_to(note_path)
    for target in (scene_path, note_path, project.manifest_path, hardlink, symlink):
        before = target.read_bytes()
        with pytest.raises(ValueError, match="project source"):
            export_project_snapshot(project, [], [ExportScene(scene.id, scene.title)],
                {}, target, "markdown", True, None, True, True, "\n\n")
        with pytest.raises(ValueError, match="project source"):
            compile_project_book_snapshot(project, "Book", [],
                [ExportScene(scene.id, scene.title)], {}, target, True)
        assert target.read_bytes() == before

