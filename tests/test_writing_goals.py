from pathlib import Path

import pytest

from app.document.writing_goals import WritingGoalStore, WritingGoalTracker


def test_scope_history_records_last_complete_observation_per_identity_and_round_trips(tmp_path):
    tracker = WritingGoalTracker(100, "active_scene")
    assert tracker.record_scope_count("file:a", 12, local_date="2026-10-17")
    assert not tracker.record_scope_count("file:a", 12, local_date="2026-10-17")
    assert tracker.record_scope_count("file:a", 9, local_date="2026-10-17")
    tracker.set_paused(True)
    assert not tracker.record_scope_count("file:a", 20, local_date="2026-10-17")
    tracker.set_paused(False)
    tracker.configure(100, "project_manuscript")
    assert tracker.record_scope_count("project:p", 40, local_date="2026-10-18")
    store = WritingGoalStore(tmp_path / "goals.json")
    store.save(tracker)
    loaded = store.load()
    assert loaded.scope_history == {"2026-10-17": {"active_scene": {"file:a": 9}},
                                    "2026-10-18": {"project_manuscript": {"project:p": 40}}}
    assert WritingGoalTracker.from_mapping({"progress": {}}).scope_history == {}


def test_clear_progress_removes_all_days_and_undo_redo_cannot_restore_them():
    tracker = WritingGoalTracker(100, "new_words")
    tracker.attach("doc", "")
    tracker.record_text("doc", "one ", local_date="2026-10-17")
    tracker.record_text("doc", "one two", local_date="2026-10-18")
    tracker.scope_history = {"2026-10-17": {"active_scene": {"doc": 1}}}
    tracker.clear_progress()
    assert tracker.progress == {} and tracker.scope_history == {}
    assert tracker._current_text["doc"] == "one two"
    tracker.record_text("doc", "one ", undo=True, local_date="2026-10-18")
    tracker.record_text("doc", "one two", redo=True, local_date="2026-10-18")
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 0
    assert tracker.count_new_words({"doc"}, local_date="2026-10-18") == 0
    tracker.record_text("doc", "one two three", local_date="2026-10-18")
    assert tracker.count_new_words({"doc"}, local_date="2026-10-18") == 1


@pytest.mark.parametrize("history", [[], None, {"2026-10-17": {"new_words": {"x": 2}}},
                                     {"2026-10-17": {"active_scene": {"x": -1}}}])
def test_invalid_persisted_scope_history_is_rejected(history):
    with pytest.raises(ValueError):
        WritingGoalTracker.from_mapping({"scope_history": history})


def test_new_words_count_tokens_added_by_typing_and_paste_once() -> None:
    tracker = WritingGoalTracker(100, "new_words")
    tracker.attach("doc", "")

    assert tracker.record_text("doc", "h", local_date="2026-10-17") == 1
    assert tracker.record_text("doc", "hel", local_date="2026-10-17") == 0
    assert tracker.record_text("doc", "hello world — Привіт", local_date="2026-10-17") == 2
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 3


def test_new_words_count_handles_repeated_text_without_quadratic_diff() -> None:
    before = "a" * 10_000

    assert WritingGoalTracker._new_tokens_added(before, before + " new") == 1
    assert WritingGoalTracker._new_tokens_added("word", "wordx") == 0


def test_new_words_count_handles_changes_across_long_unchanged_spans() -> None:
    prefix = "word " * 1000
    suffix = " end" * 1300
    before = prefix + "old" + suffix
    after = prefix + "new words" + suffix
    assert WritingGoalTracker._new_tokens_added(before, after) == 2
    assert WritingGoalTracker._new_tokens_added(after, before) == 1


def test_undo_and_redo_restore_daily_insertion_contribution() -> None:
    tracker = WritingGoalTracker(10, "new_words")
    tracker.attach("doc", "existing text")
    tracker.record_text("doc", "existing text and new words", local_date="2026-10-17")

    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 3
    tracker.record_text("doc", "existing text", local_date="2026-10-17", undo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 0
    tracker.record_text("doc", "existing text and new words", local_date="2026-10-17", redo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 3


@pytest.mark.parametrize("action", ["undo", "redo"])
def test_unknown_undo_or_redo_state_does_not_count_restored_words(action: str) -> None:
    tracker = WritingGoalTracker(10, "new_words")
    tracker.attach("doc", "")
    tracker.record_text("doc", "first", local_date="2026-10-17")
    # Reattachment represents an editor state whose prior Qt undo entries
    # outlive the tracker's earlier checkpoints.
    tracker.attach("doc", "first")
    assert tracker.record_text("doc", "first restored words", local_date="2026-10-17", **{action: True}) == 0
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 1
    tracker.record_text("doc", "first restored words new", local_date="2026-10-17")
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 2


def test_deletion_does_not_reduce_words_written_and_branching_after_undo_is_consistent() -> None:
    tracker = WritingGoalTracker(10, "new_words")
    tracker.attach("doc", "")
    tracker.record_text("doc", "one two", local_date="2026-10-17")
    tracker.record_text("doc", "", local_date="2026-10-17")
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 2
    tracker.record_text("doc", "one", local_date="2026-10-17")
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 3
    tracker.record_text("doc", "", local_date="2026-10-17", undo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 2


def test_progress_uses_local_date_keys_without_erasing_prior_days() -> None:
    tracker = WritingGoalTracker(5, "new_words")
    tracker.attach("doc", "")
    tracker.record_text("doc", "one two", local_date="2026-10-17")
    tracker.record_text("doc", "one two three", local_date="2026-10-18")

    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 2
    assert tracker.count_new_words({"doc"}, local_date="2026-10-18") == 1


def test_goal_scopes_pause_disable_and_reset_do_not_modify_text() -> None:
    tracker = WritingGoalTracker(4, "active_scene")
    tracker.attach("doc", "draft")
    tracker.record_text("doc", "draft more", local_date="2026-10-17")

    assert tracker.goal_progress(
        active_scene_words=7,
        project_words=20,
        document_ids={"doc"},
        local_date="2026-10-17",
    ) == (7, 4)
    tracker.configure(4, "project_manuscript")
    assert tracker.goal_progress(active_scene_words=7, project_words=20, document_ids={"doc"}) == (20, 4)
    tracker.configure(4, "new_words")
    assert tracker.goal_progress(
        active_scene_words=7,
        project_words=20,
        document_ids={"doc"},
        local_date="2026-10-17",
    ) == (1, 4)
    tracker.set_paused(True)
    assert tracker.goal_progress(active_scene_words=7, project_words=20, document_ids={"doc"}) is None
    tracker.set_paused(False)
    tracker.configure(0, "new_words")
    assert tracker.goal_progress(active_scene_words=0, project_words=0, document_ids={"doc"}) is None
    tracker.reset_today(local_date="2026-10-17")
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 0
    assert tracker._current_text["doc"] == "draft more"


def test_history_keeps_one_text_copy_and_tracks_undo_branch_across_days() -> None:
    tracker = WritingGoalTracker(100, "new_words")
    initial = "a" * 10_000
    tracker.attach("doc", initial)
    for number in range(100):
        tracker.record_text("doc", initial + " word" * (number + 1), local_date="2026-10-17")

    states, _ = tracker._histories["doc"]
    assert len(states) == 101
    assert sum(len(fingerprint) for fingerprint, _ in states) == 101 * 32
    tracker.record_text("doc", initial + " word" * 99, local_date="2026-10-18", undo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 99
    tracker.record_text("doc", initial + " word" * 100, local_date="2026-10-18", redo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 100
    tracker.record_text("doc", initial + " word" * 99, local_date="2026-10-18", undo=True)
    tracker.record_text("doc", initial + " word" * 99 + " different", local_date="2026-10-18")
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 99
    assert tracker.count_new_words({"doc"}, local_date="2026-10-18") == 1


def test_unchanged_progress_snapshots_are_shared_and_remain_correct_after_reset() -> None:
    tracker = WritingGoalTracker(100, "new_words")
    tracker.attach("doc", "")
    tracker.record_text("doc", "w", local_date="2026-10-17")
    tracker.record_text("doc", "wo", local_date="2026-10-17")
    tracker.record_text("doc", "word", local_date="2026-10-17")
    states, _ = tracker._histories["doc"]
    assert states[1][1] is states[2][1] is states[3][1]

    tracker.reset_today(local_date="2026-10-17")
    assert states[1][1] is states[2][1] is states[3][1]
    tracker.record_text("doc", "wo", local_date="2026-10-17", undo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 0
    tracker.record_text("doc", "wo next", local_date="2026-10-18")
    assert tracker.count_new_words({"doc"}, local_date="2026-10-18") == 1


def test_daily_snapshots_share_prior_days_and_survive_undo_and_reset() -> None:
    tracker = WritingGoalTracker(100, "new_words", progress={
        "2026-10-16": {"doc": 7}, "2026-10-17": {"doc": 3},
    })
    tracker.attach("doc", "")
    for number in range(1, 101):
        tracker.record_text("doc", " word" * number, local_date="2026-10-18")
    states, _ = tracker._histories["doc"]
    assert all(snapshot.base is states[1][1].base for _, snapshot in states[1:])
    tracker.record_text("doc", " word" * 99, local_date="2026-10-18", undo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-18") == 99
    assert tracker.count_new_words({"doc"}, local_date="2026-10-16") == 7
    tracker.reset_today(local_date="2026-10-17")
    assert all(snapshot.base is states[1][1].base for _, snapshot in states[1:])
    tracker.record_text("doc", " word" * 100, local_date="2026-10-18", redo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 0
    assert tracker.count_new_words({"doc"}, local_date="2026-10-18") == 100


def test_reset_current_day_shares_prior_counts_and_keeps_old_undo_states() -> None:
    tracker = WritingGoalTracker(100, "new_words", progress={"2026-10-16": {"doc": 7}})
    tracker.attach("doc", "")
    tracker.record_text("doc", "one", local_date="2026-10-17")
    tracker.record_text("doc", "one two", local_date="2026-10-17")
    states, _ = tracker._histories["doc"]
    tracker.reset_today(local_date="2026-10-17")
    assert states[1][1] is states[2][1]
    tracker.record_text("doc", "one", undo=True, local_date="2026-10-17")
    assert tracker.count_new_words({"doc"}, local_date="2026-10-16") == 7
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 0


def test_compacted_command_preserves_daily_counts_through_reset_undo_and_redo() -> None:
    tracker = WritingGoalTracker(10, "new_words")
    tracker.attach("doc", "")
    tracker.record_text("doc", "one", local_date="2026-10-17")
    tracker.record_text("doc", "one two", local_date="2026-10-18", merge_with_previous=True)
    assert len(tracker._histories["doc"][0]) == 2
    tracker.reset_today(local_date="2026-10-18")
    tracker.record_text("doc", "", local_date="2026-10-18", undo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 0
    tracker.record_text("doc", "one two", local_date="2026-10-18", redo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 1
    assert tracker.count_new_words({"doc"}, local_date="2026-10-18") == 0


def test_paused_edits_keep_undo_checkpoints_without_counting_new_words() -> None:
    tracker = WritingGoalTracker(10, "new_words")
    tracker.attach("doc", "")
    tracker.record_text("doc", "first", local_date="2026-10-17")
    tracker.set_paused(True)
    assert tracker.record_text("doc", "first paused", local_date="2026-10-17") == 0
    tracker.set_paused(False)
    tracker.record_text("doc", "first", local_date="2026-10-17", undo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 1
    tracker.record_text("doc", "", local_date="2026-10-17", undo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 0
    tracker.record_text("doc", "first", local_date="2026-10-17", redo=True)
    tracker.record_text("doc", "first paused", local_date="2026-10-17", redo=True)
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 1


def test_goal_settings_and_progress_round_trip_atomically(tmp_path: Path) -> None:
    store = WritingGoalStore(tmp_path / "settings" / "writing-goals.json")
    tracker = WritingGoalTracker(250, "new_words")
    tracker.attach("scene-id", "")
    tracker.record_text("scene-id", "word", local_date="2026-10-17")
    store.save(tracker)

    loaded = store.load()

    assert loaded.to_mapping() == tracker.to_mapping()


@pytest.mark.parametrize("payload", ['{"progress": [1]}', '{"progress": []}', '{"progress": null}', '{"progress": "bad"}', '{"progress": {"2026-01-01": []}}', '{'])
def test_invalid_persisted_progress_is_reported(tmp_path: Path, payload: str) -> None:
    path = tmp_path / "writing-goals.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError):
        WritingGoalStore(path).load()


def test_rekeying_a_saved_document_preserves_its_daily_contribution() -> None:
    tracker = WritingGoalTracker(100, "new_words")
    tracker.attach("untitled", "")
    tracker.record_text("untitled", "new words", local_date="2026-10-17")
    tracker.rekey_document("untitled", "file:/draft.txt", "new words")

    assert tracker.count_new_words({"untitled"}, local_date="2026-10-17") == 0
    assert tracker.count_new_words({"file:/draft.txt"}, local_date="2026-10-17") == 2


def test_rekey_collision_leaves_both_histories_and_progress_intact() -> None:
    tracker = WritingGoalTracker(100, "new_words")
    tracker.attach("source", "")
    tracker.attach("destination", "")
    tracker.record_text("source", "one two", local_date="2026-10-17")
    tracker.record_text("destination", "three", local_date="2026-10-17")

    assert not tracker.rekey_document("source", "destination", "one two")
    for identity, text, count in (("source", "one two", 2), ("destination", "three", 1)):
        tracker.record_text(identity, "", local_date="2026-10-17", undo=True)
        assert tracker.count_new_words({identity}, local_date="2026-10-17") == 0
        tracker.record_text(identity, text, local_date="2026-10-17", redo=True)
        assert tracker.count_new_words({identity}, local_date="2026-10-17") == count
    tracker.reset_today(local_date="2026-10-17")
    for identity in ("source", "destination"):
        tracker.record_text(identity, "", local_date="2026-10-17", undo=True)
        assert tracker.count_new_words({identity}, local_date="2026-10-17") == 0


def test_alias_progress_survives_reload_and_deduplicates_project_selection() -> None:
    day = "2026-10-17"
    tracker = WritingGoalTracker(100, "new_words")
    tracker.attach("scene", "")
    tracker.attach("other", "")
    tracker.record_text("scene", "one", local_date=day)
    tracker.record_text("other", "two three", local_date=day)
    assert tracker.rekey_document("other", "goal-alias:unique", "two three")
    tracker.associate_alias("goal-alias:unique", "scene")
    assert tracker.count_new_words({"scene", "goal-alias:unique"}, local_date=day) == 3
    loaded = WritingGoalTracker.from_mapping(tracker.to_mapping())
    assert loaded.count_new_words({"scene"}, local_date=day) == 3
    loaded.attach("scene", "one")
    loaded.set_paused(True)
    loaded.record_text("scene", "one paused", local_date=day)
    loaded.set_paused(False)
    loaded.record_text("scene", "one", local_date=day, undo=True)
    assert loaded.count_new_words({"scene"}, local_date=day) == 3
    loaded.reset_today(local_date=day)
    loaded.record_text("scene", "one paused", local_date=day, redo=True)
    assert loaded.count_new_words({"scene"}, local_date=day) == 0


def test_rekey_primary_keeps_aliases_and_rekey_alias_leaves_others() -> None:
    day = "2026-10-17"
    tracker = WritingGoalTracker(100, "new_words")
    for identity in ("scene", "alias-a", "alias-b"):
        tracker.attach(identity, "")
        tracker.record_text(identity, identity, local_date=day)
    tracker.associate_alias("alias-a", "scene")
    tracker.associate_alias("alias-b", "scene")
    assert tracker.rekey_document("scene", "renamed", "scene")
    assert tracker.count_new_words({"renamed"}, local_date=day) == 3
    assert tracker.rekey_document("alias-a", "separate", "alias-a")
    assert tracker.count_new_words({"renamed"}, local_date=day) == 2
    assert tracker.count_new_words({"separate"}, local_date=day) == 1


@pytest.mark.parametrize("aliases", [None, [], {"a": "a"}, {"a": "b", "b": "c"}])
def test_invalid_persisted_aliases_are_rejected(aliases) -> None:
    with pytest.raises(ValueError):
        WritingGoalTracker.from_mapping({"aliases": aliases})


def test_detach_releases_history_but_preserves_daily_progress() -> None:
    tracker = WritingGoalTracker(100, "new_words")
    tracker.attach("doc", "")
    tracker.record_text("doc", "new words", local_date="2026-10-17")
    tracker.detach("doc")
    assert "doc" not in tracker._histories
    assert "doc" not in tracker._current_text
    tracker.attach("doc", "new words")
    assert tracker.count_new_words({"doc"}, local_date="2026-10-17") == 2


@pytest.mark.parametrize(
    "target,scope",
    [(-1, "active_scene"), (True, "active_scene"), (5, "all_documents")],
)
def test_invalid_goal_configuration_is_rejected(target, scope) -> None:
    with pytest.raises((TypeError, ValueError)):
        WritingGoalTracker(target, scope)


@pytest.mark.parametrize("new_id", ["untitled", "file:/saved.txt"])
def test_rekey_preserves_undo_redo_checkpoints_for_unused_destination(new_id):
    tracker = WritingGoalTracker(100, "new_words")
    tracker.attach("untitled", "")
    tracker.record_text("untitled", "first ", local_date="2026-10-17")
    tracker.record_text("untitled", "first second", local_date="2026-10-18")
    tracker.rekey_document("untitled", new_id, "first second")
    tracker.record_text(new_id, "first ", undo=True, local_date="2026-10-18")
    assert tracker.count_new_words({new_id}, local_date="2026-10-17") == 1
    assert tracker.count_new_words({new_id}, local_date="2026-10-18") == 0
    tracker.record_text(new_id, "first second", redo=True, local_date="2026-10-18")
    assert tracker.count_new_words({new_id}, local_date="2026-10-18") == 1


def test_rekey_existing_destination_keeps_larger_progress_through_undo():
    tracker = WritingGoalTracker(100, "new_words", progress={"2026-10-18": {"file:/saved.txt": 10}})
    tracker.attach("untitled", "")
    tracker.record_text("untitled", "new words", local_date="2026-10-18")
    tracker.rekey_document("untitled", "file:/saved.txt", "new words")
    tracker.record_text("file:/saved.txt", "", undo=True, local_date="2026-10-18")
    assert tracker.count_new_words({"file:/saved.txt"}, local_date="2026-10-18") == 10
    assert "untitled" not in tracker._histories


def test_rekey_destination_floor_retains_shared_history_and_daily_counts():
    tracker = WritingGoalTracker(100, "new_words", progress={
        "2026-10-16": {"source": 4, "saved": 7},
        "2026-10-17": {"saved": 20},
    })
    tracker.attach("source", "")
    for number in range(1, 31):
        tracker.record_text("source", " word" * number, local_date="2026-10-17")
    assert tracker.rekey_document("source", "saved", " word" * 30)
    states, _ = tracker._histories["saved"]
    assert all(snapshot.base is states[1][1].base for _, snapshot in states[1:])
    tracker.record_text("saved", " word" * 29, undo=True, local_date="2026-10-17")
    assert tracker.count_new_words({"saved"}, local_date="2026-10-16") == 7
    assert tracker.count_new_words({"saved"}, local_date="2026-10-17") == 29
    for number in range(28, 9, -1):
        tracker.record_text("saved", " word" * number, undo=True, local_date="2026-10-17")
    assert tracker.count_new_words({"saved"}, local_date="2026-10-17") == 20
    tracker.record_text("saved", " word" * 11, redo=True, local_date="2026-10-17")
    assert tracker.count_new_words({"saved"}, local_date="2026-10-17") == 20


def test_rekey_changed_text_attaches_fresh_checkpoint_without_counting_it():
    tracker = WritingGoalTracker(100, "new_words")
    tracker.attach("untitled", "")
    tracker.record_text("untitled", "new words", local_date="2026-10-18")
    tracker.rekey_document("untitled", "file:/saved.txt", "different buffer")
    assert len(tracker._histories["file:/saved.txt"][0]) == 1
    assert tracker._current_text["file:/saved.txt"] == "different buffer"
    assert tracker.count_new_words({"file:/saved.txt"}, local_date="2026-10-18") == 2


def test_rekey_existing_progress_preserves_source_undo_above_destination_floor():
    tracker = WritingGoalTracker(100, "new_words", progress={"2026-10-18": {"saved": 1}})
    tracker.attach("source", "")
    tracker.record_text("source", "one ", local_date="2026-10-18")
    tracker.record_text("source", "one two", local_date="2026-10-18")
    tracker.rekey_document("source", "saved", "one two")
    assert tracker.count_new_words({"saved"}, local_date="2026-10-18") == 2
    tracker.record_text("saved", "one ", undo=True, local_date="2026-10-18")
    assert tracker.count_new_words({"saved"}, local_date="2026-10-18") == 1
    tracker.record_text("saved", "", undo=True, local_date="2026-10-18")
    assert tracker.count_new_words({"saved"}, local_date="2026-10-18") == 1
    tracker.record_text("saved", "one two", redo=True, local_date="2026-10-18")
    assert tracker.count_new_words({"saved"}, local_date="2026-10-18") == 2


def test_bounded_token_scan_matches_full_scan_for_boundary_edits():
    from app.document.writing_goals import _WORD

    samples = ["", "a", "longword", "can't", "one-two", "слово", "a b", "a--b", "a’b", "123", "a_b"]
    replacements = ["", "x", " word ", "'", "-", "’", "_", "я"]
    for before in samples:
        for start in range(len(before) + 1):
            for end in range(start, len(before) + 1):
                for replacement in replacements:
                    after = before[:start] + replacement + before[end:]
                    prefix = 0
                    while prefix < min(len(before), len(after)) and before[prefix] == after[prefix]:
                        prefix += 1
                    suffix = 0
                    while suffix < min(len(before), len(after)) - prefix and before[-suffix - 1] == after[-suffix - 1]:
                        suffix += 1
                    expected = sum(token.start() >= prefix and token.end() <= len(after) - suffix
                                   for token in _WORD.finditer(after))
                    assert WritingGoalTracker._new_tokens_added(before, after) == expected, (before, after)
