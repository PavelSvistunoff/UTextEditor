"""Local, integrity-checked manuscript snapshots and comparisons."""

from dataclasses import dataclass
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Mapping, Sequence
from uuid import uuid4


@dataclass(frozen=True)
class RevisionSnapshot:
    snapshot_id: str
    name: str
    captured_at: str
    structure: object
    scene_order: tuple[str, ...]
    scene_titles: Mapping[str, str]
    documents: Mapping[str, str]
    digest: str
    snapshot_path: Path


@dataclass(frozen=True)
class RevisionIssue:
    snapshot_path: Path
    message: str


@dataclass(frozen=True)
class SceneChange:
    scene_id: str
    kind: str
    old_title: str | None = None
    new_title: str | None = None
    diff: str = ""
    item_type: str = "scene"
    old_note_type: str | None = None
    new_note_type: str | None = None

    @property
    def item_id(self) -> str:
        """Stable ID of the changed scene or reference note."""
        return self.scene_id


@dataclass(frozen=True)
class RevisionComparison:
    changes: tuple[SceneChange, ...]


class RevisionStore:
    """Store complete snapshots; a corrupt or incomplete one is never restored."""

    FORMAT_VERSION = 1

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def create(
        self,
        name: str,
        *,
        structure: object,
        scene_order: Sequence[str],
        scene_titles: Mapping[str, str],
        documents: Mapping[str, str],
    ) -> RevisionSnapshot:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("A snapshot name is required.")
        if len(set(scene_order)) != len(scene_order) or any(not item for item in scene_order):
            raise ValueError("Scene IDs in a snapshot must be unique and non-empty.")
        if any(scene_id not in documents for scene_id in scene_order):
            raise ValueError("Cannot create an incomplete snapshot: scene text is unavailable.")
        if any(not isinstance(text, str) for text in documents.values()):
            raise TypeError("Snapshot document contents must be text.")
        if any(not isinstance(title, str) for title in scene_titles.values()):
            raise TypeError("Snapshot scene titles must be text.")
        missing_notes = set(_note_records(structure)) - documents.keys()
        if missing_notes:
            raise ValueError("Cannot create an incomplete snapshot: reference-note text is unavailable.")

        captured_at = datetime.now(timezone.utc).isoformat()
        snapshot_id = uuid4().hex
        payload = {
            "format_version": self.FORMAT_VERSION,
            "snapshot_id": snapshot_id,
            "name": clean_name,
            "captured_at": captured_at,
            "structure": structure,
            "scene_order": list(scene_order),
            "scene_titles": dict(scene_titles),
            "documents": dict(documents),
        }
        serialized = self._serialize(payload)
        payload["digest"] = self._digest(serialized)
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / f"{captured_at.replace(':', '-')}-{snapshot_id}.json"
        self._atomic_write(target, self._serialize(payload))
        return self._to_snapshot(payload, target)

    def list_snapshots(self) -> tuple[tuple[RevisionSnapshot, ...], tuple[RevisionIssue, ...]]:
        if not self.root.exists():
            return (), ()
        snapshots: list[RevisionSnapshot] = []
        issues: list[RevisionIssue] = []
        for path in sorted(self.root.glob("*.json")):
            try:
                snapshots.append(self.read(path))
            except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                issues.append(RevisionIssue(path, str(exc)))
        snapshots.sort(key=lambda snapshot: snapshot.captured_at, reverse=True)
        return tuple(snapshots), tuple(issues)

    def read(self, snapshot: str | Path | RevisionSnapshot) -> RevisionSnapshot:
        path = snapshot.snapshot_path if isinstance(snapshot, RevisionSnapshot) else Path(snapshot)
        with path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
        if not isinstance(payload, dict) or payload.get("format_version") != self.FORMAT_VERSION:
            raise ValueError("Unsupported or malformed revision snapshot.")
        digest = payload.get("digest")
        unsigned = {key: value for key, value in payload.items() if key != "digest"}
        if not isinstance(digest, str) or digest != self._digest(self._serialize(unsigned)):
            raise ValueError("Revision snapshot integrity check failed.")
        required_strings = ("snapshot_id", "name", "captured_at")
        if any(not isinstance(payload.get(key), str) or not payload[key] for key in required_strings):
            raise ValueError("Revision snapshot is missing required metadata.")
        order = payload.get("scene_order")
        titles = payload.get("scene_titles")
        documents = payload.get("documents")
        if (
            not isinstance(order, list)
            or any(not isinstance(item, str) or not item for item in order)
            or len(set(order)) != len(order)
            or not isinstance(titles, dict)
            or any(not isinstance(key, str) or not isinstance(value, str) for key, value in titles.items())
            or not isinstance(documents, dict)
            or any(not isinstance(key, str) or not isinstance(value, str) for key, value in documents.items())
            or any(scene_id not in documents for scene_id in order)
            or any(note_id not in documents for note_id in _note_records(payload.get("structure")))
        ):
            raise ValueError("Revision snapshot is incomplete or has invalid document data.")
        return self._to_snapshot(payload, path)

    def compare(self, before: RevisionSnapshot, after: RevisionSnapshot) -> RevisionComparison:
        left, right = self.read(before), self.read(after)
        old_ids, new_ids = set(left.scene_order), set(right.scene_order)
        common = old_ids & new_ids
        old_common_order = [scene_id for scene_id in left.scene_order if scene_id in common]
        new_common_order = [scene_id for scene_id in right.scene_order if scene_id in common]
        old_positions = {scene_id: index for index, scene_id in enumerate(old_common_order)}
        new_positions = {scene_id: index for index, scene_id in enumerate(new_common_order)}
        changes: list[SceneChange] = []
        for scene_id in left.scene_order:
            if scene_id not in new_ids:
                changes.append(SceneChange(scene_id, "removed", left.scene_titles.get(scene_id)))
        for scene_id in right.scene_order:
            if scene_id not in old_ids:
                changes.append(SceneChange(scene_id, "added", new_title=right.scene_titles.get(scene_id)))
        for scene_id in left.scene_order:
            if scene_id not in common:
                continue
            old_title, new_title = left.scene_titles.get(scene_id), right.scene_titles.get(scene_id)
            if old_positions[scene_id] != new_positions[scene_id]:
                changes.append(SceneChange(scene_id, "moved", old_title, new_title))
            if old_title != new_title:
                changes.append(SceneChange(scene_id, "title-changed", old_title, new_title))
            if left.documents[scene_id] != right.documents[scene_id]:
                diff = "".join(difflib.unified_diff(
                    left.documents[scene_id].splitlines(keepends=True),
                    right.documents[scene_id].splitlines(keepends=True),
                    fromfile=f"{old_title or scene_id} (before)",
                    tofile=f"{new_title or scene_id} (after)",
                ))
                changes.append(SceneChange(scene_id, "text-changed", old_title, new_title, diff))

        old_notes, new_notes = _note_records(left.structure), _note_records(right.structure)
        old_note_ids, new_note_ids = set(old_notes), set(new_notes)
        for note_id in old_notes:
            if note_id not in new_note_ids:
                changes.append(SceneChange(
                    note_id, "removed", old_notes[note_id][0], item_type="note",
                    old_note_type=old_notes[note_id][1],
                ))
        for note_id in new_notes:
            if note_id not in old_note_ids:
                changes.append(SceneChange(
                    note_id, "added", new_title=new_notes[note_id][0], item_type="note",
                    new_note_type=new_notes[note_id][1],
                ))
        for note_id in old_notes:
            if note_id not in new_note_ids:
                continue
            old_title, old_type = old_notes[note_id]
            new_title, new_type = new_notes[note_id]
            if old_title != new_title:
                changes.append(SceneChange(
                    note_id, "title-changed", old_title, new_title, item_type="note"
                ))
            if old_type != new_type:
                changes.append(SceneChange(
                    note_id, "type-changed", old_title, new_title, item_type="note",
                    old_note_type=old_type, new_note_type=new_type,
                ))
            if left.documents.get(note_id) != right.documents.get(note_id):
                old_text, new_text = left.documents.get(note_id), right.documents.get(note_id)
                diff = "".join(difflib.unified_diff(
                    (old_text or "").splitlines(keepends=True),
                    (new_text or "").splitlines(keepends=True),
                    fromfile=f"{old_title or note_id} (before)",
                    tofile=f"{new_title or note_id} (after)",
                ))
                changes.append(SceneChange(
                    note_id, "text-changed", old_title, new_title, diff, item_type="note"
                ))
        return RevisionComparison(tuple(changes))

    def delete(self, snapshot: str | Path | RevisionSnapshot, *, confirmed: bool = False) -> None:
        if not confirmed:
            raise PermissionError("Deleting a revision snapshot requires explicit confirmation.")
        path = snapshot.snapshot_path if isinstance(snapshot, RevisionSnapshot) else Path(snapshot)
        if path.parent.resolve() != self.root.resolve():
            raise ValueError("Revision snapshot is outside this revision store.")
        path.unlink()

    @classmethod
    def _serialize(cls, payload: object) -> bytes:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    @staticmethod
    def _digest(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _to_snapshot(payload: dict, path: Path) -> RevisionSnapshot:
        return RevisionSnapshot(
            snapshot_id=payload["snapshot_id"],
            name=payload["name"],
            captured_at=payload["captured_at"],
            structure=payload["structure"],
            scene_order=tuple(payload["scene_order"]),
            scene_titles=dict(payload["scene_titles"]),
            documents=dict(payload["documents"]),
            digest=payload["digest"],
            snapshot_path=path,
        )

    @staticmethod
    def _atomic_write(target: Path, payload: bytes) -> None:
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        except BaseException:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise


def _note_records(structure: object) -> dict[str, tuple[str | None, str | None]]:
    """Read note IDs, titles, and types from the captured project manifest."""
    if not isinstance(structure, dict) or not isinstance(structure.get("notes"), list):
        return {}
    records: dict[str, tuple[str | None, str | None]] = {}
    for note in structure["notes"]:
        if not isinstance(note, dict):
            continue
        note_id = note.get("id")
        if isinstance(note_id, str) and note_id:
            title = note.get("title")
            note_type = note.get("type")
            records[note_id] = (
                title if isinstance(title, str) else None,
                note_type if isinstance(note_type, str) else None,
            )
    return records
