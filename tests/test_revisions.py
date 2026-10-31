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


def test_comparison_reports_chapter_changes_without_false_moves_for_additions(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    def snapshot(chapters):
        return store.create("Draft", structure={"chapters": chapters}, scene_order=[],
                            scene_titles={}, documents={})
    before = snapshot([{"id": "a", "title": "Alpha"}, {"id": "b", "title": "Beta"},
                       {"id": "removed", "title": "Old"}])
    after = snapshot([{"id": "new", "title": "New"}, {"id": "b", "title": "Beta"},
                      {"id": "a", "title": "Renamed"}])
    changes = store.compare(before, after).changes
    assert {(c.item_id, c.kind, c.item_type) for c in changes} == {
        ("removed", "removed", "chapter"), ("new", "added", "chapter"),
        ("a", "moved", "chapter"), ("b", "moved", "chapter"),
        ("a", "title-changed", "chapter"),
    }
    assert next(c for c in changes if c.kind == "title-changed").old_title == "Alpha"
    unchanged_order = snapshot([{"id": "new", "title": "New"},
                                {"id": "a", "title": "Alpha"}, {"id": "b", "title": "Beta"}])
    assert not any(c.kind == "moved" for c in store.compare(before, unchanged_order).changes)


def test_comparison_reports_added_and_removed_directed_links(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    def snapshot(links):
        return store.create("Draft", structure={"links": links}, scene_order=[], scene_titles={}, documents={})
    before = snapshot([{"source_id": "note", "target_id": "scene"}])
    after = snapshot([{"source_id": "scene", "target_id": "note"}])
    assert [(c.item_id, c.kind, c.item_type) for c in store.compare(before, after).changes] == [
        ("note → scene", "removed", "link"), ("scene → note", "added", "link")
    ]


def test_comparison_reports_scene_chapter_changes_even_if_flat_order_is_unchanged(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    def snapshot(chapters, ungrouped):
        return store.create("Draft", structure={"chapters": chapters, "ungrouped_scenes": ungrouped},
                            scene_order=["scene"], scene_titles={"scene": "Opening"}, documents={"scene": "text"})
    before = snapshot([{"id": "a", "title": "Chapter", "scenes": [{"id": "scene"}]}], [])
    after = snapshot([{"id": "a", "title": "Chapter", "scenes": []}], [{"id": "scene"}])
    change, = store.compare(before, after).changes
    assert change.kind == "chapter-changed" and change.item_id == "scene"
    assert (change.old_chapter_id, change.new_chapter_id) == ("a", None)
    reverse, = store.compare(after, before).changes
    assert (reverse.old_chapter_id, reverse.new_chapter_id) == (None, "a")


def test_comparison_reports_project_title_and_scene_and_note_path_changes(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    def snapshot(title, scene_path, note_path):
        return store.create("Draft", structure={
            "title": title, "chapters": [],
            "ungrouped_scenes": [{"id": "scene", "path": scene_path}],
            "notes": [{"id": "note", "title": "Reference", "type": "general", "path": note_path}],
        }, scene_order=["scene"], scene_titles={"scene": "Opening"},
            documents={"scene": "text", "note": "reference"})
    before = snapshot("Old project", "manuscript/old.txt", "notes/old.txt")
    after = snapshot("New project", "manuscript/new.txt", "notes/new.txt")
    changes = store.compare(before, after).changes
    assert [(c.item_id, c.kind, c.item_type) for c in changes] == [
        ("project", "title-changed", "project"), ("scene", "path-changed", "scene"),
        ("note", "path-changed", "note"),
    ]
    assert (changes[1].old_path, changes[1].new_path) == ("manuscript/old.txt", "manuscript/new.txt")
    assert (changes[2].old_path, changes[2].new_path) == ("notes/old.txt", "notes/new.txt")


def test_comparison_reports_character_and_directed_relationship_metadata(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    def snapshot(characters, relationships):
        return store.create("Draft", structure={"characters": characters, "character_relationships": relationships},
                            scene_order=[], scene_titles={}, documents={})
    before = snapshot([{"id": "same", "full_name": "Mira", "goals": ["leave"]},
                       {"id": "removed", "full_name": "Mira"}],
                      [{"id": "rel", "source_id": "same", "target_id": "removed", "trust": 1}])
    after = snapshot([{"id": "same", "full_name": "Mira", "goals": ["stay"]},
                      {"id": "added", "full_name": "Mira"}],
                     [{"id": "rel", "source_id": "same", "target_id": "removed", "trust": 2}])
    changes = store.compare(before, after).changes
    assert [(c.item_id, c.kind, c.item_type) for c in changes] == [
        ("removed", "removed", "character"), ("added", "added", "character"),
        ("same", "metadata-changed", "character"), ("rel", "metadata-changed", "relationship"),
    ]
    assert not store.compare(after, after).changes


def test_comparison_reports_scene_character_associations_by_stable_id(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    def snapshot(associations):
        scene = {"id": "scene", "character_associations": associations}
        return store.create("Draft", structure={"chapters": [], "ungrouped_scenes": [scene]},
                            scene_order=["scene"], scene_titles={"scene": "Opening"}, documents={"scene": "text"})
    before = snapshot([{"character_id": "removed", "presence": "present"},
                       {"character_id": "same", "presence": "present"}])
    after = snapshot([{"character_id": "same", "presence": "mentioned"},
                      {"character_id": "added", "presence": "present"}])
    changes = store.compare(before, after).changes
    assert [(c.item_id, c.kind, c.character_id) for c in changes] == [
        ("scene", "association-removed", "removed"), ("scene", "association-added", "added"),
        ("scene", "association-changed", "same"),
    ]
    reordered = snapshot(list(reversed(before.structure["ungrouped_scenes"][0]["character_associations"])))
    assert not store.compare(before, reordered).changes


def test_removing_scene_does_not_mark_later_scenes_as_moved(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    before = create_snapshot(
        store,
        order=["first", "removed", "last"],
        titles={"first": "First", "removed": "Removed", "last": "Last"},
        documents={"first": "1", "removed": "2", "last": "3"},
    )
    after = create_snapshot(
        store,
        order=["first", "last"],
        titles={"first": "First", "last": "Last"},
        documents={"first": "1", "last": "3"},
    )

    changes = store.compare(before, after).changes

    assert [(change.scene_id, change.kind) for change in changes] == [
        ("removed", "removed")
    ]


def test_comparison_reports_reference_note_content_titles_types_and_removal(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    before = store.create(
        "Before",
        structure={"notes": [
            {"id": "character", "title": "Mira", "type": "character"},
            {"id": "setting", "title": "Old House", "type": "setting"},
        ]},
        scene_order=[],
        scene_titles={},
        documents={"character": "She has dark hair.\n", "setting": "A cottage."},
    )
    after = store.create(
        "After",
        structure={"notes": [
            {"id": "character", "title": "Mira Venn", "type": "research"},
            {"id": "new-note", "title": "Timeline", "type": "timeline"},
        ]},
        scene_order=[],
        scene_titles={},
        documents={"character": "She has silver hair.\n", "new-note": "Winter, then spring."},
    )

    changes = store.compare(before, after).changes

    assert [(change.item_id, change.kind, change.item_type) for change in changes] == [
        ("setting", "removed", "note"),
        ("new-note", "added", "note"),
        ("character", "title-changed", "note"),
        ("character", "type-changed", "note"),
        ("character", "text-changed", "note"),
    ]
    type_change = next(change for change in changes if change.kind == "type-changed")
    assert (type_change.old_note_type, type_change.new_note_type) == ("character", "research")
    text_change = next(change for change in changes if change.kind == "text-changed")
    assert "-She has dark hair." in text_change.diff
    assert "+She has silver hair." in text_change.diff


def test_incomplete_snapshot_is_rejected_and_no_file_is_written(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")

    with pytest.raises(ValueError, match="incomplete"):
        create_snapshot(store, order=["missing"], titles={}, documents={})

    assert not store.root.exists()


def test_snapshot_rejects_reference_note_without_captured_text(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")

    with pytest.raises(ValueError, match="reference-note text is unavailable"):
        store.create(
            "Incomplete note snapshot",
            structure={"notes": [{"id": "note", "title": "Character", "type": "character"}]},
            scene_order=[],
            scene_titles={},
            documents={},
        )

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


def test_delete_rejects_snapshot_replaced_after_selection(tmp_path) -> None:
    store = RevisionStore(tmp_path / "revisions")
    selected = create_snapshot(store, order=["one"], titles={}, documents={"one": "first"})
    replacement = create_snapshot(store, order=["one"], titles={}, documents={"one": "second"})
    selected.snapshot_path.write_bytes(replacement.snapshot_path.read_bytes())

    with pytest.raises(ValueError, match="changed since"):
        store.delete(selected, confirmed=True)
    assert store.read(selected.snapshot_path).documents["one"] == "second"
