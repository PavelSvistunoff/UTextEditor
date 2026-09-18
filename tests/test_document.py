from pathlib import Path

import pytest

from app.document.document import Document
from app.document.encoding import detect_line_ending, normalize_line_endings
from app.document.file_manager import FileManager


def test_document_revision_and_dirty_state() -> None:
    document = Document.from_text("hello")
    assert not document.dirty
    document.update_text("hello!")
    assert document.dirty and document.revision == 1
    document.mark_saved()
    assert not document.dirty


def test_file_manager_preserves_line_endings(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_bytes(b"one\r\ntwo\r\n")
    document = FileManager().open(path)
    assert document.text == "one\ntwo\n"
    assert document.line_ending == "CRLF"
    document.update_text("three\nfour\n")
    FileManager().save(document)
    assert path.read_bytes() == b"three\r\nfour\r\n"


def test_line_ending_helpers() -> None:
    assert detect_line_ending("a\nb") == "LF"
    assert normalize_line_endings("a\nb", "CRLF") == "a\r\nb"


def test_document_returns_to_dirty_after_a_later_edit() -> None:
    document = Document.from_text("first")
    document.update_text("second")
    document.mark_saved()
    document.update_text("third")

    assert document.dirty
    assert document.revision == 2


def test_save_requires_a_path_for_untitled_document() -> None:
    with pytest.raises(ValueError, match="path is required"):
        FileManager().save(Document.from_text("draft"))


def test_file_manager_preserves_classic_mac_line_endings(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_bytes(b"one\rtwo\r")

    document = FileManager().open(path)
    document.update_text("three\nfour\n")
    FileManager().save(document)

    assert document.line_ending == "CR"
    assert path.read_bytes() == b"three\rfour\r"
