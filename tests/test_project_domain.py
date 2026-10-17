from __future__ import annotations

from uuid import uuid4

import pytest
import yaml

from app.project import (
    Chapter,
    Manifest,
    Project,
    ProjectError,
    ProjectFormatError,
    ProjectPathError,
    count_words,
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
