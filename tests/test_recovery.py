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


def test_scan_reports_unfinished_snapshot_write_and_preserves_it_until_discard(tmp_path: Path) -> None:
    store = RecoveryStore(tmp_path / "recovery", retention=1)
    entry = store.save("doc", "valid")
    partial = entry.snapshot_path.parent / f".{entry.snapshot_path.name}.interrupted.tmp"
    partial.write_text('{"text":"partial', encoding="utf-8")

    store.save("doc", "newer")
    scan = store.scan()
    assert [item.text for item in scan.entries] == ["newer"]
    assert len(scan.issues) == 1
    assert scan.issues[0].snapshot_path == partial and scan.issues[0].incomplete_write
    store.discard_document("doc")
    assert partial.read_text(encoding="utf-8") == '{"text":"partial'
    store.discard()
    assert not partial.exists()


@pytest.mark.parametrize("timestamp", ["not a timestamp", "2026-01-01T12:00:00"])
def test_scan_reports_invalid_timestamp_without_hiding_valid_snapshot(tmp_path: Path, timestamp: str) -> None:
    store = RecoveryStore(tmp_path / "recovery")
    good = store.save("doc", "valid")
    damaged = store.save("other", "recoverable text")
    payload = json.loads(damaged.snapshot_path.read_text(encoding="utf-8"))
    payload["captured_at"] = timestamp
    damaged.snapshot_path.write_text(json.dumps(payload), encoding="utf-8")

    scan = store.scan()
    assert scan.entries == (good,)
    assert len(scan.issues) == 1 and "timestamp" in scan.issues[0].message
    assert damaged.snapshot_path.exists()
    assert store.restore(scan.entries[0]).text == "valid"


def test_scan_orders_timestamps_by_instant_across_timezones(tmp_path: Path) -> None:
    store = RecoveryStore(tmp_path / "recovery")
    first = store.save("doc", "earlier")
    second = store.save("doc", "later")
    for entry, timestamp in ((first, "2026-01-01T12:00:00+02:00"),
                             (second, "2026-01-01T11:00:00+00:00")):
        payload = json.loads(entry.snapshot_path.read_text(encoding="utf-8"))
        payload["captured_at"] = timestamp
        entry.snapshot_path.write_text(json.dumps(payload), encoding="utf-8")

    assert [entry.text for entry in store.scan().entries] == ["later", "earlier"]


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


def test_automatic_cleanup_preserves_damaged_snapshots(tmp_path: Path) -> None:
    store = RecoveryStore(tmp_path / "recovery", retention=1)
    damaged = store.save("scene-1", "original").snapshot_path
    damaged.write_text("{broken", encoding="utf-8")

    latest = store.save("scene-1", "new content")
    assert damaged.read_text(encoding="utf-8") == "{broken"
    assert latest.snapshot_path.exists()

    store.discard_document("scene-1")
    assert not latest.snapshot_path.exists()
    assert damaged.read_text(encoding="utf-8") == "{broken"
    assert store.scan().issues[0].snapshot_path == damaged

    store.discard()  # Explicit discard can remove damaged data.
    assert not damaged.exists()


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


def test_unreadable_directory_does_not_hide_other_recovery_snapshots(tmp_path, monkeypatch):
    store = RecoveryStore(tmp_path / "recovery")
    inaccessible = store.save("unreadable", "preserve me")
    readable = store.save("readable", "recover me")
    original_iterdir = Path.iterdir

    def denied_iterdir(path):
        if path == inaccessible.snapshot_path.parent:
            raise PermissionError("Cannot list recovery directory")
        return original_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", denied_iterdir)
    scan = store.scan()
    assert scan.entries == (readable,)
    assert len(scan.issues) == 1
    assert scan.issues[0].snapshot_path == inaccessible.snapshot_path.parent
    assert "Cannot list" in scan.issues[0].message
    assert inaccessible.snapshot_path.read_bytes()
