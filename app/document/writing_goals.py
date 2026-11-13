"""Local daily writing-goal state and undo-aware insertion counting."""

from copy import deepcopy
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Iterator, Mapping

_WORD = re.compile(r"(?u)[^\W_]+(?:['’‐‑‒–—-][^\W_]+)*")
_SCOPES = {"active_scene", "project_manuscript", "new_words"}


class _DailyCounts(Mapping[str, int]):
    """Immutable snapshot sharing unchanged days across consecutive edits."""

    def __init__(self, previous: Mapping[str, int], day: str, count: int) -> None:
        if isinstance(previous, _DailyCounts) and previous.day == day:
            self.base = previous.base
        else:
            self.base = dict(previous)
            self.base.pop(day, None)
        self.day = day
        self.count = count

    def __getitem__(self, key: str) -> int:
        return self.count if key == self.day else self.base[key]

    def __iter__(self) -> Iterator[str]:
        yield from self.base
        yield self.day

    def __len__(self) -> int:
        return len(self.base) + 1

    def without_day(self, day: str, bases: dict[int, tuple[dict[str, int], dict[str, int]]]) -> Mapping[str, int]:
        if day == self.day:
            return self.base
        if day not in self.base:
            return self
        key = id(self.base)
        if key not in bases:
            bases[key] = (self.base, {name: count for name, count in self.base.items() if name != day})
        result = object.__new__(_DailyCounts)
        result.base = bases[key][1]
        result.day = self.day
        result.count = self.count
        return result

    def with_floor(
        self, floor: Mapping[str, int],
        bases: dict[tuple[int, str], tuple[dict[str, int], dict[str, int]]],
    ) -> "_DailyCounts":
        key = (id(self.base), self.day)
        if key not in bases:
            merged = dict(self.base)
            for day, count in floor.items():
                if day != self.day:
                    merged[day] = max(merged.get(day, 0), count)
            bases[key] = (self.base, merged)
        result = object.__new__(_DailyCounts)
        result.base = bases[key][1]
        result.day = self.day
        result.count = max(self.count, floor.get(self.day, 0))
        return result


class WritingGoalTracker:
    """Track current-count goals and daily inserted words without touching prose."""

    def __init__(
        self,
        target: int = 0,
        scope: str = "active_scene",
        paused: bool = False,
        progress: Mapping[str, Mapping[str, int]] | None = None,
        scope_history: Mapping[str, Mapping[str, Mapping[str, int]]] | None = None,
        aliases: Mapping[str, str] | None = None,
    ) -> None:
        self.target = self._validate_target(target)
        if scope not in _SCOPES:
            raise ValueError(f"Unsupported writing-goal scope: {scope!r}")
        if not isinstance(paused, bool):
            raise TypeError("Writing-goal paused state must be a boolean.")
        self.scope = scope
        self.paused = paused
        self.progress: dict[str, dict[str, int]] = {}
        if progress is not None and not isinstance(progress, Mapping):
            raise ValueError("Writing-goal progress must be a mapping.")
        for day, counts in (progress if progress is not None else {}).items():
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
        self.scope_history: dict[str, dict[str, dict[str, int]]] = {}
        if scope_history is not None and not isinstance(scope_history, Mapping):
            raise ValueError("Writing-goal scope history must be a mapping.")
        for day, scopes in (scope_history or {}).items():
            date.fromisoformat(day)
            if not isinstance(scopes, Mapping):
                raise ValueError("Writing-goal scope history must map dates to scopes.")
            checked_scopes: dict[str, dict[str, int]] = {}
            for name, values in scopes.items():
                if name not in {"active_scene", "project_manuscript"} or not isinstance(values, Mapping):
                    raise ValueError("Writing-goal scope history has an invalid scope.")
                checked_values: dict[str, int] = {}
                for identity, count in values.items():
                    if not isinstance(identity, str) or not identity or isinstance(count, bool) or not isinstance(count, int) or count < 0:
                        raise ValueError("Writing-goal scope history has an invalid count or identity.")
                    checked_values[identity] = count
                checked_scopes[name] = checked_values
            self.scope_history[day] = checked_scopes
        self._histories: dict[str, tuple[list[tuple[bytes, Mapping[str, int]]], int]] = {}
        self._current_text: dict[str, str] = {}
        if aliases is not None and not isinstance(aliases, Mapping):
            raise ValueError("Writing-goal aliases must be a mapping.")
        self.aliases: dict[str, str] = dict(aliases or {})
        if any(not isinstance(key, str) or not key or not isinstance(value, str) or not value
               or key == value or value in self.aliases for key, value in self.aliases.items()):
            raise ValueError("Writing-goal aliases must map distinct identities to primary identities.")

    @staticmethod
    def _fingerprint(text: str) -> bytes:
        return hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).digest()

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
        self._histories[document_id] = ([(self._fingerprint(text), counts)], 0)
        self._current_text[document_id] = text

    def is_attached(self, document_id: str) -> bool:
        return document_id in self._histories

    def associate_alias(self, alias: str, primary: str) -> None:
        if not alias or not primary or alias == primary or primary in self.aliases:
            raise ValueError("An alias and a distinct primary identity are required.")
        for key, value in tuple(self.aliases.items()):
            if value == alias:
                self.aliases[key] = primary
        self.aliases[alias] = primary

    def rekey_document(self, old_id: str, new_id: str, text: str) -> bool:
        """Move history to an unused identity; leave both histories intact on collision."""
        if old_id == new_id:
            if self._current_text.get(old_id) != text:
                self.attach(new_id, text)
            return True
        if new_id in self._histories:
            return False
        if new_id in self.aliases:
            raise ValueError("Cannot rekey to an alias identity.")
        self.aliases.pop(old_id, None)
        for alias, primary in tuple(self.aliases.items()):
            if primary == old_id:
                self.aliases[alias] = new_id
        preserve_history = (
            old_id in self._histories
            and self._current_text.get(old_id) == text
            and new_id not in self._histories
        )
        destination_counts = {
            day: values[new_id] for day, values in self.progress.items() if new_id in values
        }
        for values in self.progress.values():
            old_count = values.pop(old_id, None)
            if old_count is not None:
                values[new_id] = max(values.get(new_id, 0), old_count)
        history = self._histories.pop(old_id, None)
        self._current_text.pop(old_id, None)
        if preserve_history and history is not None:
            states, index = history
            if destination_counts:
                merged_counts: dict[int, Mapping[str, int]] = {}
                merged_bases: dict[tuple[int, str], tuple[dict[str, int], dict[str, int]]] = {}
                for position, (fingerprint, counts) in enumerate(states):
                    key = id(counts)
                    if key not in merged_counts:
                        if isinstance(counts, _DailyCounts):
                            merged_counts[key] = counts.with_floor(destination_counts, merged_bases)
                        else:
                            merged = dict(counts)
                            for day, count in destination_counts.items():
                                merged[day] = max(merged.get(day, 0), count)
                            merged_counts[key] = merged
                    states[position] = (fingerprint, merged_counts[key])
            self._histories[new_id] = (states, index)
            self._current_text[new_id] = text
        else:
            self.attach(new_id, text)
        return True

    def detach(self, document_id: str) -> None:
        """Release transient undo history while retaining saved progress."""
        self._histories.pop(document_id, None)
        self._current_text.pop(document_id, None)

    def record_text(
        self,
        document_id: str,
        text: str,
        *,
        local_date: str | None = None,
        undo: bool = False,
        redo: bool = False,
        merge_with_previous: bool = False,
        count_new: bool = True,
    ) -> int:
        if not isinstance(text, str):
            raise TypeError("Writing-goal text must be a string.")
        today = local_date or self.local_date()
        date.fromisoformat(today)
        if document_id not in self._histories:
            self.attach(document_id, text)
            return 0
        states, index = self._histories[document_id]
        before = self._current_text[document_id]
        if before == text:
            return 0
        fingerprint = self._fingerprint(text)
        if undo:
            for candidate in range(index - 1, -1, -1):
                if states[candidate][0] == fingerprint:
                    self._histories[document_id] = (states, candidate)
                    self._current_text[document_id] = text
                    self._replace_document_progress(document_id, states[candidate][1])
                    return 0
        if redo:
            for candidate in range(index + 1, len(states)):
                if states[candidate][0] == fingerprint:
                    self._histories[document_id] = (states, candidate)
                    self._current_text[document_id] = text
                    self._replace_document_progress(document_id, states[candidate][1])
                    return 0

        del states[index + 1:]
        # A Qt undo/redo may reach a state that predates our attached history
        # (for example after tracking was reconfigured). Its text is
        # restored, not newly written, even when the old checkpoint is absent.
        added = 0 if undo or redo or self.paused or not count_new else self._new_tokens_added(before, text)
        counts = states[index][1]
        if added:
            # Progress snapshots are immutable after being stored. Reuse the
            # previous one for edits that do not add a word.
            counts = _DailyCounts(counts, today, counts.get(today, 0) + added)
        # Qt may merge many keystrokes into a single undo command. Its
        # intermediate contents cannot be reached by undo or redo, so the UI
        # may replace the previous endpoint when it knows the command merged.
        if merge_with_previous and index > 0:
            states[index] = (fingerprint, counts)
        else:
            states.append((fingerprint, counts))
        self._current_text[document_id] = text
        self._histories[document_id] = (states, len(states) - 1)
        self._replace_document_progress(document_id, counts)
        return added

    def discard_unreachable_history(
        self, document_id: str, *, keep_undo: bool = False, keep_redo: bool = False,
    ) -> None:
        """Discard checkpoints in directions the editor can no longer reach."""
        if document_id in self._histories:
            states, index = self._histories[document_id]
            if not keep_redo:
                del states[index + 1:]
            if not keep_undo:
                del states[:index]
                index = 0
            self._histories[document_id] = (states, index)

    def count_new_words(self, document_ids: set[str] | tuple[str, ...] | list[str], *, local_date: str | None = None) -> int:
        today = local_date or self.local_date()
        date.fromisoformat(today)
        counts = self.progress.get(today, {})
        primary_ids = {self.aliases.get(document_id, document_id) for document_id in document_ids}
        identities = primary_ids | {alias for alias, primary in self.aliases.items() if primary in primary_ids}
        return sum(counts.get(document_id, 0) for document_id in identities)

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

    def record_scope_count(self, identity: str, count: int, *, local_date: str | None = None) -> bool:
        """Record the latest complete observed count for the active count-based scope."""
        if self.target == 0 or self.paused or self.scope == "new_words":
            return False
        if not isinstance(identity, str) or not identity or isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("A valid scope identity and count are required.")
        day = local_date or self.local_date()
        date.fromisoformat(day)
        counts = self.scope_history.setdefault(day, {}).setdefault(self.scope, {})
        if counts.get(identity) == count:
            return False
        counts[identity] = count
        return True

    def reset_today(self, *, local_date: str | None = None) -> None:
        today = local_date or self.local_date()
        date.fromisoformat(today)
        self.progress[today] = {}
        shared_bases: dict[int, tuple[dict[str, int], dict[str, int]]] = {}
        for document_id, (states, index) in tuple(self._histories.items()):
            updated_counts: dict[int, Mapping[str, int]] = {}
            for state_index, (fingerprint, counts) in enumerate(states):
                if today not in counts:
                    continue
                key = id(counts)
                if key not in updated_counts:
                    if isinstance(counts, _DailyCounts):
                        updated_counts[key] = counts.without_day(today, shared_bases)
                    else:
                        updated = dict(counts)
                        updated.pop(today)
                        updated_counts[key] = updated
                states[state_index] = (fingerprint, updated_counts[key])
            self._histories[document_id] = (states, index)

    def clear_progress(self) -> None:
        """Remove stored progress and prevent undo/redo from restoring it."""
        self.progress.clear()
        self.scope_history.clear()
        empty: dict[str, int] = {}
        for states, _index in self._histories.values():
            for position, (fingerprint, _counts) in enumerate(states):
                states[position] = (fingerprint, empty)

    def to_mapping(self) -> dict[str, object]:
        return {
            "target": self.target,
            "scope": self.scope,
            "paused": self.paused,
            "progress": deepcopy(self.progress),
            "scope_history": deepcopy(self.scope_history),
            "aliases": dict(self.aliases),
        }

    @classmethod
    def from_mapping(cls, value: object) -> "WritingGoalTracker":
        if not isinstance(value, dict):
            raise ValueError("Writing-goal settings must be a mapping.")
        if "progress" in value and not isinstance(value["progress"], Mapping):
            raise ValueError("Writing-goal progress must be a mapping.")
        if "scope_history" in value and not isinstance(value["scope_history"], Mapping):
            raise ValueError("Writing-goal scope history must be a mapping.")
        if "aliases" in value and not isinstance(value["aliases"], Mapping):
            raise ValueError("Writing-goal aliases must be a mapping.")
        return cls(
            target=value.get("target", 0),
            scope=value.get("scope", "active_scene"),
            paused=value.get("paused", False),
            progress=value.get("progress", {}),
            scope_history=value.get("scope_history", {}),
            aliases=value.get("aliases", {}),
        )

    @staticmethod
    def _new_tokens_added(before: str, after: str) -> int:
        """Count words wholly inside the single changed span of an editor edit."""
        shared_limit = min(len(before), len(after))
        prefix = 0
        # Compare long unchanged spans in C rather than one Python character
        # at a time. The final short scan keeps exact code-point boundaries.
        chunk_size = 4096
        while prefix + chunk_size <= shared_limit and before[prefix:prefix + chunk_size] == after[prefix:prefix + chunk_size]:
            prefix += chunk_size
        while prefix < shared_limit and before[prefix] == after[prefix]:
            prefix += 1

        suffix = 0
        while suffix + chunk_size <= shared_limit - prefix:
            old_end = len(before) - suffix
            new_end = len(after) - suffix
            if before[old_end - chunk_size:old_end] != after[new_end - chunk_size:new_end]:
                break
            suffix += chunk_size
        while suffix < shared_limit - prefix and before[-suffix - 1] == after[-suffix - 1]:
            suffix += 1

        changed_end = len(after) - suffix
        return sum(
            1
            # Two surrounding characters retain internal apostrophe/dash
            # boundaries without scanning the unchanged document.
            for token in _WORD.finditer(after, max(0, prefix - 2), min(len(after), changed_end + 2))
            if token.start() >= prefix and token.end() <= changed_end
        )

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
