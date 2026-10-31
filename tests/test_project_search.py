from threading import Event

import pytest

from app.project.search import SearchDocument, search_project


def test_search_prefers_open_buffer_and_reports_locations(tmp_path):
    (tmp_path / "scene.txt").write_text("disk only", encoding="utf-8")
    (tmp_path / "note.txt").write_text("first\r\nПривіт word\r\n", encoding="utf-8")
    docs = (SearchDocument("scene", "s", "Scene", "scene.txt", "unsaved word\nword"),
            SearchDocument("note", "n", "Note", "note.txt"))
    result = search_project(tmp_path, docs, "word")
    assert [(match.id, match.line, match.column) for match in result.matches] == [("s", 1, 9), ("s", 2, 1), ("n", 2, 8)]
    assert not result.errors and not result.cancelled
    assert (tmp_path / "scene.txt").read_text(encoding="utf-8") == "disk only"


def test_search_reports_missing_binary_and_oversized_documents(tmp_path, monkeypatch):
    from app.project import search
    monkeypatch.setattr(search, "MAX_DOCUMENT_BYTES", 4)
    (tmp_path / "large.txt").write_text("12345", encoding="utf-8")
    (tmp_path / "binary.txt").write_bytes(b"a\x00b")
    docs = tuple(SearchDocument("note", name, name, name + ".txt") for name in ("missing", "large", "binary"))
    result = search_project(tmp_path, docs, "a")
    assert len(result.errors) == 3 and not result.matches


def test_search_limits_results_and_honours_cancellation(tmp_path, monkeypatch):
    from app.project import search
    monkeypatch.setattr(search, "MAX_MATCHES", 2)
    doc = SearchDocument("scene", "s", "Scene", "scene.txt", "a a a")
    result = search_project(tmp_path, (doc,), "a")
    assert len(result.matches) == 2 and result.limited
    cancel = Event()
    cancel.set()
    result = search_project(tmp_path, (doc,), "a", cancel)
    assert result.cancelled and not result.matches
    with pytest.raises(ValueError):
        search_project(tmp_path, (doc,), "")


def test_multiline_query_counts_following_line_correctly(tmp_path):
    doc = SearchDocument("scene", "s", "Scene", "scene.txt", "a\nb\na\nb")
    result = search_project(tmp_path, (doc,), "a\nb")
    assert [(m.line, m.column) for m in result.matches] == [(1, 1), (3, 1)]


def test_search_cancels_during_a_document_and_rejects_escaping_paths(tmp_path):
    class CancelAfterFirstMatch:
        checks = 0
        def is_set(self):
            self.checks += 1
            return self.checks > 2

    doc = SearchDocument("scene", "s", "Scene", "scene.txt", "word word word")
    result = search_project(tmp_path, (doc,), "word", CancelAfterFirstMatch())
    assert result.cancelled and len(result.matches) == 1
    escaping = SearchDocument("note", "n", "Outside", "../outside.txt")
    result = search_project(tmp_path, (escaping,), "word")
    assert len(result.errors) == 1 and not result.matches


def test_large_project_stops_at_result_limit(tmp_path):
    documents = tuple(SearchDocument("scene", str(i), str(i), f"{i}.txt", "word") for i in range(2500))
    result = search_project(tmp_path, documents, "word")
    assert result.limited and len(result.matches) == 1000
    assert result.matches[-1].id == "999"


def test_large_project_can_cancel_before_reading_remaining_files(tmp_path):
    class CancelAfterDocuments:
        checks = 0

        def is_set(self):
            self.checks += 1
            return self.checks > 1000

    # Missing files make each visited document observable in the error list.
    documents = tuple(SearchDocument("note", str(i), str(i), f"{i}.txt") for i in range(5000))
    result = search_project(tmp_path, documents, "absent", CancelAfterDocuments())
    assert result.cancelled
    assert len(result.errors) == 1000
    assert not result.matches and not result.limited
