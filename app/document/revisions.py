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
        ):
            raise ValueError("Revision snapshot is incomplete or has invalid document data.")
        return self._to_snapshot(payload, path)

    def compare(self, before: RevisionSnapshot, after: RevisionSnapshot) -> RevisionComparison:
        left, right = self.read(before), self.read(after)
        old_ids, new_ids = set(left.scene_order), set(right.scene_order)
        common = old_ids & new_ids
        old_common = [scene_id for scene_id in left.scene_order if scene_id in common]
        new_common = [scene_id for scene_id in right.scene_order if scene_id in common]
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
            if old_common.index(scene_id) != new_common.index(scene_id):
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
