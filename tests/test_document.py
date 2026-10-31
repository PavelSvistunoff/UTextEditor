from pathlib import Path
import os
import subprocess
import sys
from threading import Event, Thread, current_thread

import pytest

from app.document.document import Document
from app.document.encoding import detect_line_ending, normalize_line_endings, python_index_to_qt_position, qt_position_to_python_index
from app.document.file_manager import ExternalChangeError, FileManager


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


def test_file_manager_strips_utf8_bom_when_opening(tmp_path: Path) -> None:
    path = tmp_path / "with_bom.txt"
    path.write_bytes(b"\xef\xbb\xbfhello\r\nworld\r\n")

    document = FileManager().open(path)

    assert document.text == "hello\nworld\n"
    assert document.line_ending == "CRLF"
    assert not document.text.startswith("\ufeff")


def test_line_ending_helpers() -> None:
    assert detect_line_ending("a\nb") == "LF"
    assert normalize_line_endings("a\nb", "CRLF") == "a\r\nb"
    assert detect_line_ending("a\nb\r\nc\r") == "LF"
    assert detect_line_ending("a\nb\r\nc\r\nd\r\n") == "CRLF"


def test_python_and_qt_positions_round_trip_around_non_bmp_characters() -> None:
    text = "a😀б"

    assert python_index_to_qt_position(text, 2) == 3
    assert qt_position_to_python_index(text, 3) == 2
    assert qt_position_to_python_index(text, 2) == 1


def test_document_returns_to_dirty_after_a_later_edit() -> None:
    document = Document.from_text("first")
    document.update_text("second")
    document.mark_saved()
    document.update_text("third")

    assert document.dirty
    assert document.revision == 2


def test_document_becomes_clean_when_text_returns_to_saved_contents() -> None:
    document = Document.from_text("saved")
    document.update_text("changed")
    document.update_text("saved")

    assert not document.dirty
    assert document.revision == 2


def test_directly_initialized_document_uses_initial_text_as_saved_snapshot() -> None:
    document = Document(text="initial")
    document.update_text("edited")
    document.update_text("initial")

    assert not document.dirty


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


def test_file_manager_rejects_embedded_nul_as_binary_data(tmp_path: Path) -> None:
    path = tmp_path / "binary.dat"
    path.write_bytes(b"text\x00bytes")

    with pytest.raises(ValueError, match="binary data"):
        FileManager().open(path)


def test_file_manager_creates_parent_directories_for_new_files(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "folder" / "new.txt"
    document = Document.from_text("saved")
    document.path = path

    saved = FileManager().save(document)

    assert saved == path
    assert path.read_text(encoding="utf-8") == "saved"


def test_failed_atomic_save_keeps_original_file_and_document_dirty(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("saved", encoding="utf-8")
    document = FileManager().open(path)
    document.update_text("unsaved")

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr("app.document.file_manager.os.replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        FileManager().save(document)

    assert path.read_text(encoding="utf-8") == "saved"
    assert document.dirty


def test_file_manager_refuses_to_overwrite_external_changes(tmp_path: Path) -> None:
    path = tmp_path / "draft.txt"
    path.write_text("original", encoding="utf-8")
    manager = FileManager()
    document = manager.open(path)
    document.update_text("my edit")
    path.write_text("external version", encoding="utf-8")

    with pytest.raises(ExternalChangeError, match="changed on disk"):
        manager.save(document)

    assert path.read_text(encoding="utf-8") == "external version"
    assert document.dirty


def test_save_detects_separate_process_edit_during_staging(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "draft.txt"
    path.write_text("original", encoding="utf-8")
    manager = FileManager()
    document = manager.open(path)
    document.update_text("my edit")
    original_fsync = os.fsync
    changed = []

    def change_after_stage(fd):
        original_fsync(fd)
        if not changed:
            subprocess.run([sys.executable, "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('external edit', encoding='utf-8')", str(path)], check=True)
            changed.append(True)

    monkeypatch.setattr("app.document.file_manager.os.fsync", change_after_stage)
    with pytest.raises(ExternalChangeError, match="during saving"):
        manager.save(document)
    assert path.read_text(encoding="utf-8") == "external edit"
    assert document.dirty
    assert not list(tmp_path.glob(".draft.txt.*.tmp"))


def test_standalone_saves_serialize_check_and_replace_in_process(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "draft.txt"
    path.write_text("original", encoding="utf-8")
    first_manager, second_manager = FileManager(), FileManager()
    first_doc, second_doc = first_manager.open(path), second_manager.open(path)
    first_doc.update_text("first edit")
    second_doc.update_text("second edit")
    first_replacing, release_first, second_started, second_read = (Event() for _ in range(4))
    outcomes = {}
    original_replace, original_read = os.replace, Path.read_bytes

    def pause_replace(source, destination):
        if current_thread().name == "first-save" and Path(destination) == path:
            first_replacing.set()
            if not release_first.wait(3):
                raise TimeoutError("First save was not released.")
        return original_replace(source, destination)

    def observe_read(target):
        result = original_read(target)
        if current_thread().name == "second-save" and target == path:
            second_read.set()
        return result

    def save(label, manager, document):
        if label == "second":
            second_started.set()
        try:
            manager.save(document)
        except ExternalChangeError:
            outcomes[label] = "conflict"
        else:
            outcomes[label] = "saved"

    monkeypatch.setattr("app.document.file_manager.os.replace", pause_replace)
    monkeypatch.setattr(Path, "read_bytes", observe_read)
    first = Thread(target=save, args=("first", first_manager, first_doc), name="first-save")
    second = Thread(target=save, args=("second", second_manager, second_doc), name="second-save")
    first.start()
    try:
        assert first_replacing.wait(2)
        second.start()
        assert second_started.wait(2)
        assert not second_read.wait(0.5)
    finally:
        release_first.set()
        first.join(3)
        if second.ident is not None:
            second.join(3)
    assert not first.is_alive() and not second.is_alive()
    assert outcomes == {"first": "saved", "second": "conflict"}
    assert path.read_text(encoding="utf-8") == "first edit"
    assert second_doc.dirty


def test_separate_process_edit_after_final_check_exposes_save_race(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "draft.txt"
    path.write_text("original", encoding="utf-8")
    manager = FileManager()
    document = manager.open(path)
    document.update_text("my edit")
    original_replace = os.replace
    external_observed = []

    def edit_before_replace(source, destination):
        subprocess.run(
            [sys.executable, "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('external edit', encoding='utf-8')", str(path)],
            check=True,
        )
        external_observed.append(path.read_text(encoding="utf-8"))
        original_replace(source, destination)

    monkeypatch.setattr("app.document.file_manager.os.replace", edit_before_replace)
    manager.save(document)

    # This documents the current limitation, not a desired conflict policy.
    # Change this assertion when supported coordination closes the race.
    assert external_observed == ["external edit"]
    assert path.read_text(encoding="utf-8") == "my edit"


def test_file_manager_updates_disk_digest_for_repeated_saves(tmp_path: Path) -> None:
    path = tmp_path / "draft.txt"
    path.write_text("original", encoding="utf-8")
    manager = FileManager()
    document = manager.open(path)
    document.update_text("first save")
    manager.save(document)
    document.update_text("second save")

    manager.save(document)

    assert path.read_text(encoding="utf-8") == "second save"
    assert not document.dirty


def test_save_as_to_a_new_path_does_not_compare_against_source_digest(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    destination = tmp_path / "copy.txt"
    source.write_text("original", encoding="utf-8")
    manager = FileManager()
    document = manager.open(source)
    document.update_text("copy")

    manager.save(document, destination)

    assert source.read_text(encoding="utf-8") == "original"
    assert destination.read_text(encoding="utf-8") == "copy"
    assert document.path == destination


def test_document_via_text_update_on_same_value_does_not_increase_revision() -> None:
    document = Document.from_text("same")
    before = document.revision

    document.update_text("same")

    assert document.revision == before
    assert not document.dirty


@pytest.mark.parametrize("encoding", ["cp1251", "cp1252", "utf-16"])
def test_open_unsupported_encoding_preserves_original_bytes(tmp_path, encoding):
    path = tmp_path / "legacy.txt"
    raw = ("Привіт" if encoding == "cp1251" else "café").encode(encoding)
    path.write_bytes(raw)
    with pytest.raises(UnicodeError):
        FileManager().open(path)
    assert path.read_bytes() == raw


@pytest.mark.parametrize("encoding", ["cp1251", "cp1252"])
def test_unrepresentable_save_preserves_disk_and_dirty_buffer(tmp_path, encoding):
    path = tmp_path / "draft.txt"
    path.write_bytes(b"original")
    manager = FileManager()
    document = manager.open(path)
    document.encoding = encoding
    document.update_text("draft 😀")
    digest = document.disk_digest
    with pytest.raises(UnicodeEncodeError):
        manager.save(document)
    assert path.read_bytes() == b"original"
    assert document.text == "draft 😀" and document.dirty
    assert document.disk_digest == digest
    assert not list(tmp_path.glob(".*.tmp"))
