import json

import pytest

from app.document.revisions import RevisionStore


def create_snapshot(store, *, order, titles, documents):
    return store.create(
        "Draft",
        structure={"chapter_ids": ["chapter"]},
        scene_order=order,
        scene_titles=titles,
        documents=documents,
    )


def test_snapshot_captures_in_memory_state_and_text_comparison(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    before = create_snapshot(
        store,
        order=["one"],
        titles={"one": "Opening"},
        documents={"one": "A first draft.\n"},
    )
    after = create_snapshot(
        store,
        order=["one", "two"],
        titles={"one": "Beginning", "two": "New scene"},
        documents={"one": "A revised draft.\n", "two": "Added text."},
    )

    comparison = store.compare(before, after)

    assert [(change.scene_id, change.kind) for change in comparison.changes] == [
        ("two", "added"),
        ("one", "title-changed"),
        ("one", "text-changed"),
    ]
    text_change = next(change for change in comparison.changes if change.kind == "text-changed")
    assert "-A first draft." in text_change.diff
    assert "+A revised draft." in text_change.diff
    assert before.documents["one"] == "A first draft.\n"


def test_comparison_reports_removal_and_reorder_without_false_moves_from_additions(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    before = create_snapshot(
        store,
        order=["one", "two"],
        titles={"one": "One", "two": "Two"},
        documents={"one": "1", "two": "2"},
    )
    after = create_snapshot(
        store,
        order=["new", "two"],
        titles={"new": "New", "two": "Two"},
        documents={"new": "new", "two": "2"},
    )

    changes = store.compare(before, after).changes

    assert {(change.scene_id, change.kind) for change in changes} == {
        ("one", "removed"),
        ("new", "added"),
    }


def test_reordered_scenes_are_reported_as_moved(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    before = create_snapshot(
        store,
        order=["one", "two"],
        titles={"one": "One", "two": "Two"},
        documents={"one": "1", "two": "2"},
    )
    after = create_snapshot(
        store,
        order=["two", "one"],
        titles={"one": "One", "two": "Two"},
        documents={"one": "1", "two": "2"},
    )

    assert {(change.scene_id, change.kind) for change in store.compare(before, after).changes} == {
        ("one", "moved"),
        ("two", "moved"),
    }


def test_incomplete_snapshot_is_rejected_and_no_file_is_written(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")

    with pytest.raises(ValueError, match="incomplete"):
        create_snapshot(store, order=["missing"], titles={}, documents={})

    assert not store.root.exists()


def test_corrupt_snapshot_is_reported_not_loaded_or_deleted(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    snapshot = create_snapshot(
        store, order=["one"], titles={"one": "One"}, documents={"one": "text"}
    )
    payload = json.loads(snapshot.snapshot_path.read_text(encoding="utf-8"))
    payload["documents"]["one"] = "corrupted"
    snapshot.snapshot_path.write_text(json.dumps(payload), encoding="utf-8")

    snapshots, issues = store.list_snapshots()

    assert not snapshots
    assert len(issues) == 1
    assert snapshot.snapshot_path.exists()


def test_delete_requires_confirmation_and_only_removes_snapshot(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    snapshot = create_snapshot(
        store, order=["one"], titles={"one": "One"}, documents={"one": "text"}
    )

    with pytest.raises(PermissionError, match="confirmation"):
        store.delete(snapshot)
    store.delete(snapshot, confirmed=True)

    assert not snapshot.snapshot_path.exists()
