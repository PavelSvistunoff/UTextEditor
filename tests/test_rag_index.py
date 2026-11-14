import shutil
from pathlib import Path
import sqlite3
from threading import Event, Thread
import sys

import pytest

from app.project import Project, ProjectError
from app.project.rag_sources import CaptureCancelled, CaptureLimits, capture_project_sources
from app.project.rag_index import LexicalIndex, IndexUnavailable, fts5_available


@pytest.fixture
def corpus(tmp_path):
    if not fts5_available():
        pytest.skip("Runtime SQLite has no FTS5")
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Ніч", content="Марія відчинила двері. The quiet night.")
    note = project.add_note("Reference", content="A secret silver key")
    index = LexicalIndex(tmp_path / "cache", project.root, project.manifest.project_id)
    return project, scene, note, index


def test_missing_index_status_does_not_create_files(corpus):
    _project, _scene, _note, index = corpus
    assert index.status().state == "missing"
    assert not index.path.parent.exists()


def test_refresh_indexes_unicode_and_reuses_unchanged_sources(corpus):
    project, scene, note, index = corpus
    first = index.refresh(capture_project_sources(project))
    assert first.state == "ready" and first.source_count == 2
    assert first.changed_sources == 2
    assert index.search_terms(("Марія",))[0].source_id == scene.id
    assert index.search_terms(("silver",))[0].source_id == note.id
    assert index.status().generation == first.generation
    second = index.refresh(capture_project_sources(Project.open(project.root)))
    assert second.generation == first.generation and second.changed_sources == 0


def test_refresh_handles_edit_rename_add_delete_and_empty_sources(corpus):
    project, scene, note, index = corpus
    index.refresh(capture_project_sources(project))
    project.write_scene(scene.id, "A golden compass", expected_content=project.read_scene(scene.id))
    project.rename_note(note.id, "Archive")
    empty = project.add_scene("Empty", content="")
    changed = index.refresh(capture_project_sources(project))
    assert changed.changed_sources == 3
    assert not index.search_terms(("Марія",))
    assert index.search_terms(("compass",))[0].source_id == scene.id
    assert index.search_terms(("Archive",))[0].source_id == note.id
    assert changed.source_count == 3
    project.remove_scene(empty.id, delete_file=False)
    deleted = index.refresh(capture_project_sources(project))
    assert deleted.removed_sources == 1 and deleted.source_count == 2


def test_only_saved_text_is_persisted(corpus):
    from app.project.rag_sources import BufferText

    project, scene, _note, index = corpus
    capture = capture_project_sources(project, {scene.id: BufferText("UNSAVEDSECRET", 9)})
    index.refresh(capture)
    assert not index.search_terms(("UNSAVEDSECRET",))
    assert index.search_terms(("Марія",))
    assert b"UNSAVEDSECRET" not in index.path.read_bytes()


@pytest.mark.parametrize("issue", ["corrupt", "schema", "policy"])
def test_bad_cache_is_rebuilt_without_touching_manuscripts(corpus, issue):
    project, scene, _note, index = corpus
    before = {str(path.relative_to(project.root)): path.read_bytes()
              for path in project.root.rglob("*") if path.is_file()}
    index.refresh(capture_project_sources(project))
    if issue == "corrupt":
        index.path.write_bytes(b"broken database")
        assert index.status().state == "error"
    else:
        key = "schema_version" if issue == "schema" else "chunk_policy"
        with sqlite3.connect(index.path) as connection:
            connection.execute("UPDATE metadata SET value = 'obsolete' WHERE key = ?", (key,))
        assert index.status().state == "rebuild_required"
    refreshed = index.refresh(capture_project_sources(project))
    assert refreshed.state == "ready"
    assert index.search_terms(("Марія",))[0].source_id == scene.id
    after = {str(path.relative_to(project.root)): path.read_bytes()
             for path in project.root.rglob("*") if path.is_file()}
    assert before == after


def test_policy_change_rebuilds_chunks_and_missing_sources_remove_old_hits(corpus):
    project, _scene, note, index = corpus
    initial = index.refresh(capture_project_sources(project))
    limits = CaptureLimits(chunk_characters=32, overlap_characters=4)
    rebuilt = index.refresh(capture_project_sources(project, limits=limits))
    assert rebuilt.generation != initial.generation
    assert index.search_terms(("Марія",), limits=limits)
    (project.root / note.path).unlink()
    partial = index.refresh(capture_project_sources(project))
    assert partial.state == "incomplete" and partial.diagnostics
    assert not index.search_terms(("silver",))


def test_relocation_and_copied_project_id_have_separate_scopes(corpus, tmp_path):
    project, _scene, _note, index = corpus
    index.refresh(capture_project_sources(project))
    destination = tmp_path / "copy"
    shutil.copytree(project.root, destination)
    copied = Project.open(destination)
    other = LexicalIndex(tmp_path / "cache", copied.root, copied.manifest.project_id)
    assert other.path != index.path
    assert other.status().state == "missing"
    other.refresh(capture_project_sources(copied))
    other.delete()
    assert index.status().state == "ready" and other.status().state == "missing"


def test_interrupted_staging_is_ignored_and_deletion_is_scoped(corpus):
    project, _scene, _note, index = corpus
    index.refresh(capture_project_sources(project))
    orphan = index.path.with_name(index.path.stem + ".interrupted.building")
    orphan.write_bytes(b"unfinished manuscript cache")
    unrelated = index.path.parent / "other.sqlite3"
    unrelated.write_bytes(b"unrelated")
    assert index.status().state == "ready"
    index.delete()
    assert not orphan.exists() and not index.path.exists()
    assert unrelated.read_bytes() == b"unrelated"


def test_delete_removes_scoped_sqlite_sidecars_even_without_fts5(corpus, monkeypatch):
    project, _scene, _note, index = corpus
    index.refresh(capture_project_sources(project))
    sidecars = [Path(str(index.path) + suffix) for suffix in ("-wal", "-shm", "-journal")]
    for path in sidecars:
        path.write_bytes(b"old cached text")
    monkeypatch.setattr("app.project.rag_index.fts5_available", lambda: False)
    assert index.delete().state == "missing"
    assert not index.path.exists() and not any(path.exists() for path in sidecars)


def test_unavailable_fts5_does_not_create_a_cache(tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    index = LexicalIndex(tmp_path / "cache", project.root, project.manifest.project_id)
    monkeypatch.setattr("app.project.rag_index.fts5_available", lambda: False)
    assert index.status().state == "unavailable"
    with pytest.raises(IndexUnavailable, match="FTS5"):
        index.refresh(capture_project_sources(project))
    assert not index.path.exists()


def test_runtime_probe_reports_unavailable_sqlite_feature(monkeypatch):
    def unavailable(*_args, **_options):
        raise sqlite3.OperationalError("no such module: fts5")

    monkeypatch.setattr("app.project.rag_index.sqlite3.connect", unavailable)
    assert fts5_available() is False


def test_unwritable_cache_directory_does_not_change_sources(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="Original")
    cache_root = tmp_path / "blocked"
    cache_root.write_text("not a directory", encoding="utf-8")
    index = LexicalIndex(cache_root, project.root, project.manifest.project_id)
    with pytest.raises(IndexUnavailable, match="cache"):
        index.refresh(capture_project_sources(project))
    assert project.read_scene(scene.id) == "Original"
    assert cache_root.read_text(encoding="utf-8") == "not a directory"


def test_unwritable_cache_reports_error_preserving_old_generation(corpus, monkeypatch):
    import app.project.rag_index as module

    project, _scene, _note, index = corpus
    original = index.refresh(capture_project_sources(project))
    monkeypatch.setattr(module.os, "replace", lambda *_args: (_ for _ in ()).throw(PermissionError("Denied")))
    with pytest.raises(IndexUnavailable, match="cache"):
        index.refresh(capture_project_sources(project), force=True)
    assert index.status().generation == original.generation


@pytest.mark.parametrize("cancel_at", [1, 4, 8])
def test_cancelled_update_preserves_prior_generation(corpus, cancel_at):
    project, scene, _note, index = corpus
    original = index.refresh(capture_project_sources(project))
    project.write_scene(scene.id, "new text", expected_content=project.read_scene(scene.id))
    checks = 0

    def cancelled():
        nonlocal checks
        checks += 1
        return checks >= cancel_at

    with pytest.raises(CaptureCancelled):
        index.refresh(capture_project_sources(project), is_cancelled=cancelled)
    assert index.status().generation == original.generation


def test_source_change_during_index_build_cannot_publish(corpus, monkeypatch):
    import app.project.rag_index as module

    project, scene, _note, index = corpus
    original = index.refresh(capture_project_sources(project))
    original_insert = module.LexicalIndex._write_source

    def change_during_write(self, connection, source, chunks):
        original_insert(self, connection, source, chunks)
        (project.root / scene.path).write_text("External edit", encoding="utf-8")

    monkeypatch.setattr(module.LexicalIndex, "_write_source", change_during_write)
    with pytest.raises(ProjectError, match="changed"):
        index.refresh(capture_project_sources(project), force=True)
    assert index.status().generation == original.generation


def test_concurrent_reader_sees_complete_previous_generation(corpus, monkeypatch):
    project, scene, _note, index = corpus
    old = index.refresh(capture_project_sources(project))
    project.write_scene(scene.id, "replacement phrase", expected_content=project.read_scene(scene.id))
    capture = capture_project_sources(project)
    entered, release = Event(), Event()
    original_insert = LexicalIndex._write_source
    failures = []

    def paused_insert(self, connection, source, chunks):
        original_insert(self, connection, source, chunks)
        entered.set()
        if not release.wait(5):
            raise RuntimeError("Test did not release staging")

    def refresh():
        try:
            index.refresh(capture)
        except Exception as exc:
            failures.append(exc)

    monkeypatch.setattr(LexicalIndex, "_write_source", paused_insert)
    thread = Thread(target=refresh)
    thread.start()
    try:
        assert entered.wait(5)
        assert index.status().generation == old.generation
        assert index.search_terms(("Марія",))
        assert not index.search_terms(("replacement",))
    finally:
        release.set()
        thread.join(5)
    assert not thread.is_alive() and not failures
    assert index.status().generation != old.generation
    assert index.search_terms(("replacement",))


def test_cache_inside_project_and_symlink_targets_are_refused(corpus, tmp_path):
    project, scene, _note, index = corpus
    with pytest.raises(IndexUnavailable, match="outside"):
        LexicalIndex(project.root, project.root, project.manifest.project_id)
    index.path.parent.mkdir(parents=True)
    index.path.symlink_to(project.root / scene.path)
    assert index.status().state == "error"
    with pytest.raises(IndexUnavailable):
        index.refresh(capture_project_sources(project))
    assert project.read_scene(scene.id).startswith("Марія")


def test_older_worker_waiting_for_writer_lock_is_discarded(corpus):
    project, _scene, _note, index = corpus
    original = index.refresh(capture_project_sources(project))
    capture = capture_project_sources(project)
    cancelled = Event()
    entered = Event()
    failures = []

    def obsolete_refresh():
        entered.set()
        try:
            index.refresh(capture, force=True, is_cancelled=cancelled.is_set)
        except CaptureCancelled:
            failures.append("discarded")

    index._lock.acquire()
    thread = Thread(target=obsolete_refresh)
    try:
        thread.start()
        assert entered.wait(5)
        cancelled.set()
    finally:
        index._lock.release()
        thread.join(5)
    assert not thread.is_alive() and failures == ["discarded"]
    assert index.status().generation == original.generation


def test_plain_terms_cannot_inject_fts_or_sql_syntax(corpus):
    project, _scene, _note, index = corpus
    index.refresh(capture_project_sources(project))
    assert not index.search_terms(('" OR title:*; DROP TABLE sources; --',))
    assert index.status().state == "ready"


def test_interrupted_staging_failure_cleans_private_files_and_keeps_committed_cache(corpus, monkeypatch):
    project, _scene, _note, index = corpus
    original = index.refresh(capture_project_sources(project))

    def fail_write(*_args):
        raise sqlite3.OperationalError("simulated interrupted write")

    monkeypatch.setattr(LexicalIndex, "_write_source", fail_write)
    with pytest.raises(IndexUnavailable, match="interrupted write"):
        index.refresh(capture_project_sources(project), force=True)
    assert index.status().generation == original.generation
    assert not tuple(index.path.parent.glob("*.building*"))


def test_captured_lookup_filters_scope_and_stale_sources_without_writing_cache(corpus):
    project, scene, note, index = corpus
    original = index.refresh(capture_project_sources(project))
    project.write_note(note.id, "Current reference", expected_content=project.read_note(note.id))
    capture = capture_project_sources(project)
    allowed = tuple(source for source in capture.sources if source.id == note.id)
    before = index.path.read_bytes()
    result = index.lookup_capture(("silver", "Марія"), allowed)
    assert result.generation == original.generation
    assert not result.current_source_ids and not result.matches
    assert index.path.read_bytes() == before
    result = index.lookup_capture(("Марія",), capture.sources)
    assert result.current_source_ids == frozenset({scene.id})
    assert result.matches[0].source_id == scene.id
    assert result.matches[0].source_json == ""


def test_lookup_cancellation_is_not_downgraded_to_unavailable_cache(corpus):
    project, _scene, _note, index = corpus
    index.refresh(capture_project_sources(project))
    capture = capture_project_sources(project)
    calls = 0

    def cancel_once():
        nonlocal calls
        calls += 1
        return calls == 2

    with pytest.raises(CaptureCancelled):
        index.lookup_capture(("silver",), capture.sources, is_cancelled=cancel_once)


def test_lookup_generation_and_rows_come_from_one_read_snapshot(corpus, monkeypatch):
    project, scene, _note, index = corpus
    original = index.refresh(capture_project_sources(project))
    capture = capture_project_sources(project)
    entered, release = Event(), Event()
    original_status = LexicalIndex._status
    results, failures = [], []

    def paused_status(self, connection, limits):
        from threading import current_thread

        result = original_status(self, connection, limits)
        if current_thread().name == "captured-lookup":
            entered.set()
            if not release.wait(5):
                raise RuntimeError("Test did not release captured lookup")
        return result

    def lookup():
        try:
            results.append(index.lookup_capture(("Марія",), capture.sources))
        except Exception as exc:
            failures.append(exc)

    monkeypatch.setattr(LexicalIndex, "_status", paused_status)
    reader = Thread(target=lookup, name="captured-lookup")
    reader.start()
    try:
        assert entered.wait(5)
        project.write_scene(scene.id, "Replacement phrase", expected_content=project.read_scene(scene.id))
        try:
            index.refresh(capture_project_sources(project), force=True)
        except IndexUnavailable as exc:
            if sys.platform != "win32" or not isinstance(exc.__cause__, PermissionError):
                raise
    finally:
        release.set()
        reader.join(5)
    assert not reader.is_alive() and not failures
    assert results[0].generation == original.generation
    assert "Марія" in results[0].matches[0].text
    with pytest.raises(ProjectError, match="changed on disk"):
        capture.verify_current()
