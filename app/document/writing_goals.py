"""Local daily writing-goal state and undo-aware insertion counting."""

from copy import deepcopy
from datetime import date, datetime
import difflib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Mapping

_WORD = re.compile(r"(?u)[^\W_]+(?:['’‐‑‒–—-][^\W_]+)*")
_SCOPES = {"active_scene", "project_manuscript", "new_words"}


class WritingGoalTracker:
    """Track current-count goals and daily inserted words without touching prose."""

    def __init__(
        self,
        target: int = 0,
        scope: str = "active_scene",
        paused: bool = False,
        progress: Mapping[str, Mapping[str, int]] | None = None,
    ) -> None:
        self.target = self._validate_target(target)
        if scope not in _SCOPES:
            raise ValueError(f"Unsupported writing-goal scope: {scope!r}")
        if not isinstance(paused, bool):
            raise TypeError("Writing-goal paused state must be a boolean.")
        self.scope = scope
        self.paused = paused
        self.progress: dict[str, dict[str, int]] = {}
        for day, counts in (progress or {}).items():
            date.fromisoformat(day)
            if not isinstance(counts, Mapping):
                raise ValueError("Writing-goal progress must map dates to document counts.")
            checked: dict[str, int] = {}
            for document_id, count in counts.items():
                if not isinstance(document_id, str) or not document_id:
                    raise ValueError("Writing-goal document IDs must be non-empty strings.")
                if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                    raise ValueError("Writing-goal counts must be non-negative integers.")
                checked[document_id] = count
            self.progress[day] = checked
        self._histories: dict[str, tuple[list[tuple[str, dict[str, int]]], int]] = {}

    @staticmethod
    def _validate_target(target: int) -> int:
        if isinstance(target, bool) or not isinstance(target, int) or not 0 <= target <= 1_000_000:
            raise ValueError("Writing goal must be an integer between 0 and 1,000,000.")
        return target

    @staticmethod
    def local_date() -> str:
        return datetime.now().astimezone().date().isoformat()

    def configure(self, target: int, scope: str) -> None:
        self.target = self._validate_target(target)
        if scope not in _SCOPES:
            raise ValueError(f"Unsupported writing-goal scope: {scope!r}")
        self.scope = scope

    def attach(self, document_id: str, text: str) -> None:
        if not document_id or not isinstance(text, str):
            raise ValueError("A document ID and text are required to track writing.")
        counts = {
            day: values[document_id]
            for day, values in self.progress.items()
            if document_id in values
        }
        self._histories[document_id] = ([(text, counts)], 0)

    def rekey_document(self, old_id: str, new_id: str, text: str) -> None:
        if old_id == new_id:
            self.attach(new_id, text)
            return
        for values in self.progress.values():
            old_count = values.pop(old_id, None)
            if old_count is not None:
                values[new_id] = max(values.get(new_id, 0), old_count)
        self._histories.pop(old_id, None)
        self.attach(new_id, text)

    def record_text(
        self,
        document_id: str,
        text: str,
        *,
        local_date: str | None = None,
        undo: bool = False,
        redo: bool = False,
    ) -> int:
        if not isinstance(text, str):
            raise TypeError("Writing-goal text must be a string.")
        today = local_date or self.local_date()
        date.fromisoformat(today)
        if document_id not in self._histories:
            self.attach(document_id, text)
            return 0
        states, index = self._histories[document_id]
        before = states[index][0]
        if before == text:
            return 0
        if undo:
            for candidate in range(index - 1, -1, -1):
                if states[candidate][0] == text:
                    self._histories[document_id] = (states, candidate)
                    self._replace_document_progress(document_id, states[candidate][1])
                    return 0
        if redo:
            for candidate in range(index + 1, len(states)):
                if states[candidate][0] == text:
                    self._histories[document_id] = (states, candidate)
                    self._replace_document_progress(document_id, states[candidate][1])
                    return 0

        del states[index + 1:]
        counts = dict(states[index][1])
        added = self._new_tokens_added(before, text)
        if added:
            counts[today] = counts.get(today, 0) + added
        states.append((text, counts))
        self._histories[document_id] = (states, len(states) - 1)
        self._replace_document_progress(document_id, counts)
        return added

    def count_new_words(self, document_ids: set[str] | tuple[str, ...] | list[str], *, local_date: str | None = None) -> int:
        today = local_date or self.local_date()
        date.fromisoformat(today)
        counts = self.progress.get(today, {})
        return sum(counts.get(document_id, 0) for document_id in set(document_ids))

    def goal_progress(
        self,
        *,
        active_scene_words: int,
        project_words: int,
        document_ids: set[str] | tuple[str, ...] | list[str],
        local_date: str | None = None,
    ) -> tuple[int, int] | None:
        if self.target == 0 or self.paused:
            return None
        if self.scope == "active_scene":
            count = active_scene_words
        elif self.scope == "project_manuscript":
            count = project_words
        else:
            count = self.count_new_words(document_ids, local_date=local_date)
        return max(0, int(count)), self.target

    def set_paused(self, paused: bool) -> None:
        if not isinstance(paused, bool):
            raise TypeError("Writing-goal paused state must be a boolean.")
        self.paused = paused

    def reset_today(self, *, local_date: str | None = None) -> None:
        today = local_date or self.local_date()
        date.fromisoformat(today)
        self.progress[today] = {}
        for document_id, (states, index) in tuple(self._histories.items()):
            for state_index, (text, counts) in enumerate(states):
                updated = dict(counts)
                updated.pop(today, None)
                states[state_index] = (text, updated)
            self._histories[document_id] = (states, index)

    def to_mapping(self) -> dict[str, object]:
        return {
            "target": self.target,
            "scope": self.scope,
            "paused": self.paused,
            "progress": deepcopy(self.progress),
        }

    @classmethod
    def from_mapping(cls, value: object) -> "WritingGoalTracker":
        if not isinstance(value, dict):
            raise ValueError("Writing-goal settings must be a mapping.")
        return cls(
            target=value.get("target", 0),
            scope=value.get("scope", "active_scene"),
            paused=value.get("paused", False),
            progress=value.get("progress", {}),
        )

    @staticmethod
    def _new_tokens_added(before: str, after: str) -> int:
        retained_new_positions: list[tuple[int, int]] = []
        for block in difflib.SequenceMatcher(None, before, after, autojunk=False).get_matching_blocks():
            if block.size:
                retained_new_positions.append((block.b, block.b + block.size))
        added = 0
        for token in _WORD.finditer(after):
            if not any(start < token.end() and end > token.start() for start, end in retained_new_positions):
                added += 1
        return added

    def _replace_document_progress(self, document_id: str, counts: Mapping[str, int]) -> None:
        for values in self.progress.values():
            values.pop(document_id, None)
        for day, count in counts.items():
            self.progress.setdefault(day, {})[document_id] = count


class WritingGoalStore:
    """Atomic JSON persistence for local goal settings and progress."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> WritingGoalTracker:
        if not self.path.exists():
            return WritingGoalTracker()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Writing-goal data could not be read: {exc}") from exc
        return WritingGoalTracker.from_mapping(payload)

    def save(self, tracker: WritingGoalTracker | Mapping[str, object]) -> None:
        payload = tracker.to_mapping() if isinstance(tracker, WritingGoalTracker) else dict(tracker)
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(serialized)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except BaseException:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise
