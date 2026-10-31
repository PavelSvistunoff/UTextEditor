import json
from pathlib import Path

import pytest

from app.document.recovery import RecoveryComparisonLabels, RecoveryConflictError, RecoveryStore
from app.document.file_manager import FileManager


def test_recovery_snapshot_is_local_and_restores_as_dirty_without_writing_source(tmp_path: Path) -> None:
    canonical = tmp_path / "draft.txt"
    canonical.write_text("saved", encoding="utf-8")
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("scene-1", "unsaved", canonical_path=canonical)

    recovered = store.restore(entry)

    assert canonical.read_text(encoding="utf-8") == "saved"
    assert recovered.path == canonical
    assert recovered.text == "unsaved"
    assert recovered.dirty


def test_recovery_refuses_automatic_restore_when_canonical_file_changed(tmp_path: Path) -> None:
    canonical = tmp_path / "draft.txt"
    canonical.write_text("saved", encoding="utf-8")
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("scene-1", "recovered", canonical_path=canonical)
    canonical.write_text("external edit", encoding="utf-8")

    with pytest.raises(RecoveryConflictError, match="changed after"):
        store.restore(entry)

    assert canonical.read_text(encoding="utf-8") == "external edit"


def test_recovery_conflicts_if_canonical_file_appeared_after_snapshot(tmp_path: Path) -> None:
    canonical = tmp_path / "new-draft.txt"
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("untitled", "recovered", canonical_path=canonical)
    canonical.write_text("different file", encoding="utf-8")

    with pytest.raises(RecoveryConflictError, match="appeared after"):
        store.restore(entry)


def test_recovery_comparison_shows_changes_without_editing_canonical_file(tmp_path: Path) -> None:
    canonical = tmp_path / "draft.txt"
    canonical.write_text("saved text\n", encoding="utf-8")
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("scene", "recovered text\n", canonical_path=canonical)

    comparison = store.compare(entry)

    assert "-saved text" in comparison
    assert "+recovered text" in comparison
    assert canonical.read_text(encoding="utf-8") == "saved text\n"


def test_recovery_comparison_localizes_labels_without_translating_document_text(tmp_path: Path) -> None:
    canonical = tmp_path / "draft.txt"
    canonical.write_text("saved text\n", encoding="utf-8")
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("scene", "recovered text\n", canonical_path=canonical)
    labels = RecoveryComparisonLabels(
        untitled="Без назви", missing="Відсутній: {path}", disk="{path} (диск)",
        snapshot="Копія", identical="Збігається",
    )
    comparison = store.compare(entry, labels)
    assert f"--- {canonical} (диск)" in comparison
    assert "+++ Копія" in comparison
    assert "-saved text" in comparison and "+recovered text" in comparison
    canonical.write_text("recovered text\n", encoding="utf-8")
    assert store.compare(entry, labels) == "Збігається"
    canonical.unlink()
    assert store.compare(entry, labels) == f"Відсутній: {canonical}"
    untitled = store.save("untitled", "text")
    assert store.compare(untitled, labels) == "Без назви"


def test_scan_reports_corrupt_snapshot_and_preserves_it_for_diagnosis(tmp_path: Path) -> None:
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("scene-1", "recover me")
    corrupt = entry.snapshot_path.parent / "corrupt.json"
    corrupt.write_text("{broken", encoding="utf-8")

    scan = store.scan()

    assert [item.text for item in scan.entries] == ["recover me"]
    assert len(scan.issues) == 1
    assert scan.issues[0].snapshot_path == corrupt
    assert corrupt.exists()


def test_empty_recovery_snapshot_can_be_scanned_and_restored(tmp_path: Path) -> None:
    store = RecoveryStore(tmp_path / "recovery")
    store.save("scene", "")

    scan = store.scan()

    assert not scan.issues
    assert store.restore(scan.entries[0]).text == ""


@pytest.mark.parametrize("ending", [b"\r\n", b"\r"])
def test_restored_document_preserves_canonical_line_endings_on_save(tmp_path: Path, ending: bytes) -> None:
    canonical = tmp_path / "draft.txt"
    canonical.write_bytes(b"first" + ending + b"second")
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("scene", "changed\ntext", canonical_path=canonical)

    recovered = store.restore(entry)
    FileManager().save(recovered)

    assert canonical.read_bytes() == b"changed" + ending + b"text"


def test_recovery_retention_keeps_latest_snapshots_for_document(tmp_path: Path) -> None:
    store = RecoveryStore(tmp_path / "recovery", retention=2)

    entries = [store.save("scene-1", f"version {index}") for index in range(4)]

    scan = store.scan()
    assert len(scan.entries) == 2
    assert {entry.text for entry in scan.entries} == {entries[-1].text, entries[-2].text}


def test_discard_only_removes_recovery_data_not_canonical_files(tmp_path: Path) -> None:
    canonical = tmp_path / "draft.txt"
    canonical.write_text("canonical", encoding="utf-8")
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("scene-1", "recovered", canonical_path=canonical)

    store.discard()

    assert not entry.snapshot_path.exists()
    assert canonical.read_text(encoding="utf-8") == "canonical"


def test_scan_rejects_unsupported_recovery_version_and_keeps_data(tmp_path: Path) -> None:
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("scene-1", "text")
    payload = json.loads(entry.snapshot_path.read_text(encoding="utf-8"))
    payload["format_version"] = 99
    entry.snapshot_path.write_text(json.dumps(payload), encoding="utf-8")

    scan = store.scan()

    assert not scan.entries
    assert len(scan.issues) == 1
    assert entry.snapshot_path.exists()


def test_scan_rejects_malformed_project_item_identity(tmp_path: Path) -> None:
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("document", "text")
    payload = json.loads(entry.snapshot_path.read_text(encoding="utf-8"))
    payload.update(project_item_id="scene-id", project_item_kind=[])
    entry.snapshot_path.write_text(json.dumps(payload), encoding="utf-8")
    scan = store.scan()
    assert not scan.entries and len(scan.issues) == 1
    assert entry.snapshot_path.exists()
