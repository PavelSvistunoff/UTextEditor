from dataclasses import replace
import base64
import json
import os
from uuid import uuid4

import pytest

from app.project import Project, SceneCharacterAssociation
from app.project.rag_sources import (
    BufferText, CaptureLimits, capture_project_sources, chunk_source,
)
from app.project.model import CharacterRelationship, ProjectError


def test_sources_keep_provenance_order_and_buffer_authority(tmp_path):
    project = Project.create(tmp_path / "novel", "Роман")
    chapter = project.add_chapter("Chapter")
    first = project.add_scene("Same", chapter_id=chapter.id, content="Disk scene\r\n\r\nSecond paragraph")
    second = project.add_scene("Same", content="Other scene")
    note = project.add_note("Same", "research", content="Disk note")
    buffers = {first.id: BufferText("Незбережена сцена\n\nДругий абзац", 4),
               note.id: BufferText("Unsaved note", 7)}
    capture = capture_project_sources(project, buffers)
    assert capture.complete and not capture.diagnostics
    by_id = {source.id: source for source in capture.sources}
    disk = {source.id: source for source in capture.disk_sources}
    assert by_id[first.id].text == buffers[first.id].text
    assert by_id[first.id].buffer_revision == 4
    assert disk[first.id].text == "Disk scene\r\n\r\nSecond paragraph"
    assert disk[first.id].buffer_revision is None
    assert by_id[first.id].scene_order == 0 and by_id[second.id].scene_order == 1
    assert by_id[note.id].scene_order is None and by_id[note.id].note_type == "research"
    assert all(source.project_id == project.manifest.project_id for source in capture.sources)
    assert by_id[first.id].content_digest != disk[first.id].content_digest
    capture.verify_current(buffers)


@pytest.mark.parametrize("text", ["", "one\n\ntwo\n\nthree", "Український текст. " * 150, "a\r\n\r\nb 🌙", "x" * 301])
def test_chunking_is_exact_bounded_complete_and_deterministic(tmp_path, text):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content=text)
    capture = capture_project_sources(project)
    source = capture.sources[0]
    chunks = chunk_source(source, chunk_characters=50, overlap_characters=8)
    assert chunks == chunk_source(source, chunk_characters=50, overlap_characters=8)
    assert len({chunk.id for chunk in chunks}) == len(chunks)
    covered = set()
    for chunk in chunks:
        assert chunk.source is source
        assert chunk.text == text[chunk.start:chunk.end]
        assert 0 < len(chunk.text) <= 50
        covered.update(range(chunk.start, chunk.end))
    assert covered == set(range(len(text)))
    if text:
        changed = replace(source, project_id="other-project")
        assert chunk_source(changed, chunk_characters=50, overlap_characters=8)[0].id != chunks[0].id


def test_profile_sections_and_scene_associations_are_captured(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="Mara waits.")
    character = project.add_character("Mara")
    character.primary_motivation = "Find her sister"
    character.background = {"history": "An earlier life"}
    project.update_character(character.id, character)
    project.associate_character(scene.id, SceneCharacterAssociation(character.id, presence="mentioned"))
    capture = capture_project_sources(project)
    profile = next(source for source in capture.sources if source.kind == "character")
    scene_source = next(source for source in capture.sources if source.kind == "scene")
    assert "mentioned" in scene_source.metadata_json and character.id in scene_source.metadata_json
    assert "Find her sister" in profile.text and "An earlier life" in profile.text
    assert "portrait" not in profile.text
    for chunk in chunk_source(profile):
        assert chunk.field
        section = next(section for section in profile.sections if section.field == chunk.field)
        assert section.start <= chunk.start < chunk.end <= section.end


@pytest.mark.parametrize("change", ["scene", "note", "manifest", "buffer", "new_buffer"])
def test_verification_rejects_changed_sources_and_metadata(tmp_path, change):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="Original")
    note = project.add_note("Note", content="Reference")
    buffers = {scene.id: BufferText("Unsaved", 2)}
    capture = capture_project_sources(project, buffers)
    if change == "scene":
        (project.root / scene.path).write_text("External", encoding="utf-8")
    elif change == "note":
        project.write_note(note.id, "Changed", expected_content="Reference")
    elif change == "manifest":
        project.rename_scene(scene.id, "Renamed")
    elif change == "buffer":
        buffers[scene.id] = BufferText("Unsaved", 3)
    else:
        buffers[note.id] = BufferText("New buffer", 0)
    with pytest.raises(ProjectError, match="changed"):
        capture.verify_current(buffers)


@pytest.mark.parametrize("issue", ["missing", "binary", "oversized", "buffer"])
def test_incomplete_capture_reports_problem_without_disk_fallback(tmp_path, issue):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="disk")
    buffers = {}
    if issue == "missing":
        (project.root / scene.path).unlink()
    elif issue == "binary":
        (project.root / scene.path).write_bytes(b"\x00bad")
    elif issue == "oversized":
        (project.root / scene.path).write_bytes(b"x" * 1001)
    else:
        buffers[scene.id] = BufferText("x" * 1001, 1)
    capture = capture_project_sources(project, buffers, limits=CaptureLimits(source_bytes=1000))
    assert not capture.complete
    assert capture.diagnostics[0].source_id == scene.id
    assert not capture.sources


@pytest.mark.parametrize("limit", ["sources", "total_bytes", "chunks"])
def test_work_limits_are_explicit_not_silent(tmp_path, limit):
    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("First", content="first text")
    project.add_scene("Second", content="second text")
    values = {"sources": 1} if limit == "sources" else {limit: 1}
    capture = capture_project_sources(project, limits=CaptureLimits(**values))
    assert not capture.complete and capture.diagnostics


def test_capture_rejects_foreign_buffers_stale_manifest_and_cancellation(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("Scene", content="text")
    with pytest.raises(ProjectError, match="buffer"):
        capture_project_sources(project, {"foreign": BufferText("text", 0)})
    with pytest.raises(ProjectError, match="cancelled"):
        capture_project_sources(project, is_cancelled=lambda: True)
    other = Project.open(project.root)
    other.add_scene("New", content="new text")
    with pytest.raises(ProjectError, match="changed"):
        capture_project_sources(project)


@pytest.mark.parametrize("values", [
    {"chunk_characters": 0}, {"overlap_characters": -1},
    {"chunk_characters": 10, "overlap_characters": 10}, {"chunks": True},
])
def test_invalid_capture_limits_are_rejected(values):
    with pytest.raises(ValueError):
        CaptureLimits(**values)


def test_portrait_is_excluded_but_directed_relationships_are_sources(tmp_path):
    from PySide6.QtGui import QImage

    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    other = project.add_character("Ivo")
    portrait_path = tmp_path / "portrait.png"
    image = QImage(2, 2, QImage.Format.Format_ARGB32)
    image.fill(0xff223344)
    assert image.save(str(portrait_path))
    portrait = base64.b64encode(portrait_path.read_bytes()).decode("ascii")
    character.portrait = portrait
    project.update_character(character.id, character)
    relationship = CharacterRelationship(str(uuid4()), character.id, other.id, "rival")
    project.add_character_relationship(relationship)
    capture = capture_project_sources(project)
    assert capture.complete
    assert all(portrait not in source.text + source.metadata_json for source in capture.sources)
    source = next(source for source in capture.sources if source.kind == "relationship")
    assert source.id == relationship.id
    assert json.loads(source.text)["source_id"] == character.id
    assert json.loads(source.text)["target_id"] == other.id


@pytest.mark.parametrize("kind", ["directory", "fifo", "invalid_utf8"])
def test_nonregular_paths_refuse_and_invalid_text_reports_incomplete_coverage(tmp_path, kind):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="text")
    path = project.root / scene.path
    path.unlink()
    if kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        if not hasattr(os, "mkfifo"):
            pytest.skip("Named pipes are not supported on this platform")
        os.mkfifo(path)
    else:
        path.write_bytes(b"\xff")
    if kind != "invalid_utf8":
        # Reuse Project.open's stronger whole-project path validation.
        with pytest.raises(ProjectError, match="not a regular file"):
            capture_project_sources(project)
        return
    capture = capture_project_sources(project)
    assert not capture.complete and not capture.sources
    assert capture.diagnostics[0].source_id == scene.id


def test_escaping_symlink_is_rejected_before_source_read(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="text")
    outside = tmp_path / "outside.txt"
    outside.write_text("Never include this", encoding="utf-8")
    path = project.root / scene.path
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(ProjectError, match="escapes"):
        capture_project_sources(project)


def test_source_and_chunk_caps_bound_work_before_building_all_chunks(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("Huge paragraph", content="x" * 1000)
    second = project.add_scene("Second", content="next")
    limited = capture_project_sources(project, limits=CaptureLimits(
        sources=1, chunks=2, chunk_characters=10, overlap_characters=0))
    assert not limited.complete and not limited.sources
    assert any("1 sources omitted" in item.reason for item in limited.diagnostics)
    assert any("Chunk-count" in item.reason for item in limited.diagnostics)
    assert all(source.id != second.id for source in limited.sources)


def test_cancellation_while_chunking_aborts_instead_of_returning_partial_capture(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("Scene", content="x" * 2000)
    checks = 0

    def cancel_once():
        nonlocal checks
        checks += 1
        return checks == 4

    with pytest.raises(ProjectError, match="cancelled"):
        capture_project_sources(project, is_cancelled=cancel_once)


def test_disk_changes_during_capture_cannot_publish_a_stale_snapshot(tmp_path, monkeypatch):
    import app.project.rag_sources as sources_module

    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="first")
    original_read = sources_module._read_source

    def change_after_first_read(project, path, maximum):
        result = original_read(project, path, maximum)
        (project.root / scene.path).write_text("second", encoding="utf-8")
        return result

    monkeypatch.setattr(sources_module, "_read_source", change_after_first_read)
    with pytest.raises(ProjectError, match="changed on disk"):
        capture_project_sources(project)


def test_reopen_is_deterministic_but_metadata_only_changes_invalidate_chunks(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="identical words")
    character = project.add_character("Mara")
    initial = capture_project_sources(project)
    assert capture_project_sources(Project.open(project.root)) == initial
    original = next(chunk for chunk in initial.chunks if chunk.source.id == scene.id)
    project.associate_character(scene.id, SceneCharacterAssociation(character.id, presence="mentioned"))
    updated = capture_project_sources(project)
    changed = next(chunk for chunk in updated.chunks if chunk.source.id == scene.id)
    assert original.text == changed.text and original.id != changed.id
    with pytest.raises(ProjectError, match="metadata changed"):
        initial.verify_current()


def test_different_projects_with_same_titles_do_not_share_chunk_identity(tmp_path):
    first = Project.create(tmp_path / "first", "Same")
    second = Project.create(tmp_path / "second", "Same")
    first.add_scene("Same", content="Same content")
    second.add_scene("Same", content="Same content")
    first_capture = capture_project_sources(first)
    second_capture = capture_project_sources(second)
    assert first_capture.project_id != second_capture.project_id
    assert first_capture.chunks[0].id != second_capture.chunks[0].id


def test_closed_buffer_and_unicode_byte_limits_do_not_reuse_old_text(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="disk")
    capture = capture_project_sources(project, {scene.id: BufferText("author edits", 1)})
    with pytest.raises(ProjectError, match="buffer changed"):
        capture.verify_current({})
    limited = capture_project_sources(project, {scene.id: BufferText("ї" * 60, 2)},
                                       limits=CaptureLimits(source_bytes=100))
    assert not limited.complete and not limited.sources
    assert "no disk fallback" in limited.diagnostics[0].reason


def test_unreadable_source_has_diagnostic_and_no_source_files_are_written(tmp_path, monkeypatch):
    import app.project.rag_sources as sources_module

    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("Scene", content="Original")
    note = project.add_note("Note", content="Reference")
    before = {str(path.relative_to(project.root)): path.read_bytes()
              for path in project.root.rglob("*") if path.is_file()}
    original_read = sources_module._read_source

    def deny_note(project, path, maximum):
        if path == note.path:
            raise PermissionError("Source is unreadable")
        return original_read(project, path, maximum)

    monkeypatch.setattr(sources_module, "_read_source", deny_note)
    capture = capture_project_sources(project)
    assert not capture.complete
    assert capture.diagnostics[0].source_id == note.id
    after = {str(path.relative_to(project.root)): path.read_bytes()
             for path in project.root.rglob("*") if path.is_file()}
    assert before == after


def test_metadata_edit_during_capture_refuses_publication(tmp_path, monkeypatch):
    import app.project.rag_sources as sources_module

    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="text")
    original_read = sources_module._read_source

    def rename_after_read(fresh, path, maximum):
        result = original_read(fresh, path, maximum)
        project.rename_scene(scene.id, "Renamed externally")
        return result

    monkeypatch.setattr(sources_module, "_read_source", rename_after_read)
    with pytest.raises(ProjectError, match="metadata changed"):
        capture_project_sources(project)


def test_paragraph_boundary_is_preferred_over_cutting_the_next_paragraph(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("Scene", content="First paragraph.\n\nSecond paragraph continues for a while.")
    source = capture_project_sources(project).sources[0]
    chunks = chunk_source(source, chunk_characters=30, overlap_characters=0)
    assert chunks[0].text == "First paragraph.\n\n"
    assert "".join(chunk.text for chunk in chunks) == source.text
