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

    @property
    def document_titles(self) -> Mapping[str, str]:
        """Captured document labels, including reference notes and legacy IDs."""
        titles = {item_id: item_id for item_id in self.documents}
        titles.update(self.scene_titles)
        for item_id, (title, _) in _note_records(self.structure).items():
            if title is not None:
                titles[item_id] = title
        return titles


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
    old_chapter_id: str | None = None
    new_chapter_id: str | None = None
    old_path: str | None = None
    new_path: str | None = None
    character_id: str | None = None
    changed_fields: tuple[str, ...] = ()

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
        try:
            paths = sorted(path for path in self.root.iterdir() if path.suffix == ".json")
        except OSError as exc:
            return (), (RevisionIssue(self.root, str(exc)),)
        for path in paths:
            try:
                snapshots.append(self.read(path))
            except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                issues.append(RevisionIssue(path, str(exc)))
        snapshots.sort(key=lambda snapshot: datetime.fromisoformat(snapshot.captured_at), reverse=True)
        return tuple(snapshots), tuple(issues)

    def read(self, snapshot: str | Path | RevisionSnapshot) -> RevisionSnapshot:
        path = snapshot.snapshot_path if isinstance(snapshot, RevisionSnapshot) else Path(snapshot)
        if path.is_symlink():
            raise ValueError("Revision snapshot must not be a symbolic link.")
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
        try:
            captured_at = datetime.fromisoformat(payload["captured_at"])
            if captured_at.utcoffset() is None:
                raise ValueError("Missing timezone")
        except (ValueError, OverflowError) as exc:
            raise ValueError("Revision snapshot has an invalid or timezone-free capture timestamp.") from exc
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
        if isinstance(left.structure, dict) and isinstance(right.structure, dict):
            old_project_title = left.structure.get("title")
            new_project_title = right.structure.get("title")
            if (isinstance(old_project_title, str) and isinstance(new_project_title, str)
                    and old_project_title != new_project_title):
                changes.append(SceneChange("project", "title-changed", old_project_title,
                                           new_project_title, item_type="project"))
        old_chapters, new_chapters = _chapter_records(left.structure), _chapter_records(right.structure)
        old_parents, new_parents = _scene_parents(left.structure), _scene_parents(right.structure)
        old_paths, new_paths = _document_paths(left.structure), _document_paths(right.structure)
        old_associations = _scene_associations(left.structure)
        new_associations = _scene_associations(right.structure)
        old_chapter_ids, new_chapter_ids = set(old_chapters), set(new_chapters)
        common_chapters = old_chapter_ids & new_chapter_ids
        old_chapter_order = [key for key in old_chapters if key in common_chapters]
        new_chapter_order = [key for key in new_chapters if key in common_chapters]
        old_chapter_positions = {key: index for index, key in enumerate(old_chapter_order)}
        new_chapter_positions = {key: index for index, key in enumerate(new_chapter_order)}
        for chapter_id, title in old_chapters.items():
            if chapter_id not in new_chapter_ids:
                changes.append(SceneChange(chapter_id, "removed", title, item_type="chapter"))
        for chapter_id, title in new_chapters.items():
            if chapter_id not in old_chapter_ids:
                changes.append(SceneChange(chapter_id, "added", new_title=title, item_type="chapter"))
        for chapter_id in old_chapters:
            if chapter_id not in common_chapters:
                continue
            old_title, new_title = old_chapters[chapter_id], new_chapters[chapter_id]
            if old_chapter_positions[chapter_id] != new_chapter_positions[chapter_id]:
                changes.append(SceneChange(chapter_id, "moved", old_title, new_title, item_type="chapter"))
            if old_title != new_title:
                changes.append(SceneChange(chapter_id, "title-changed", old_title, new_title, item_type="chapter"))
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
            if (scene_id in old_parents and scene_id in new_parents
                    and old_parents[scene_id] != new_parents[scene_id]):
                changes.append(SceneChange(
                    scene_id, "chapter-changed", old_title, new_title,
                    old_chapter_id=old_parents[scene_id], new_chapter_id=new_parents[scene_id],
                ))
            if old_title != new_title:
                changes.append(SceneChange(scene_id, "title-changed", old_title, new_title))
            if scene_id in old_paths and scene_id in new_paths and old_paths[scene_id] != new_paths[scene_id]:
                changes.append(SceneChange(scene_id, "path-changed", old_title, new_title,
                                           old_path=old_paths[scene_id], new_path=new_paths[scene_id]))
            if scene_id in old_associations and scene_id in new_associations:
                old_scene_chars, new_scene_chars = old_associations[scene_id], new_associations[scene_id]
                for character_id in sorted(old_scene_chars.keys() - new_scene_chars.keys()):
                    changes.append(SceneChange(scene_id, "association-removed", old_title, new_title,
                                               character_id=character_id))
                for character_id in sorted(new_scene_chars.keys() - old_scene_chars.keys()):
                    changes.append(SceneChange(scene_id, "association-added", old_title, new_title,
                                               character_id=character_id))
                for character_id in sorted(old_scene_chars.keys() & new_scene_chars.keys()):
                    if old_scene_chars[character_id] != new_scene_chars[character_id]:
                        changes.append(SceneChange(scene_id, "association-changed", old_title, new_title,
                                                   character_id=character_id,
                                                   changed_fields=_changed_fields(old_scene_chars[character_id],
                                                                                  new_scene_chars[character_id])))
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
        common_note_ids = old_note_ids & new_note_ids
        old_note_positions = {key: index for index, key in enumerate(
            key for key in old_notes if key in common_note_ids)}
        new_note_positions = {key: index for index, key in enumerate(
            key for key in new_notes if key in common_note_ids)}
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
            if old_note_positions[note_id] != new_note_positions[note_id]:
                changes.append(SceneChange(note_id, "moved", old_title, new_title, item_type="note"))
            if old_title != new_title:
                changes.append(SceneChange(
                    note_id, "title-changed", old_title, new_title, item_type="note"
                ))
            if old_type != new_type:
                changes.append(SceneChange(
                    note_id, "type-changed", old_title, new_title, item_type="note",
                    old_note_type=old_type, new_note_type=new_type,
                ))
            if note_id in old_paths and note_id in new_paths and old_paths[note_id] != new_paths[note_id]:
                changes.append(SceneChange(note_id, "path-changed", old_title, new_title, item_type="note",
                                           old_path=old_paths[note_id], new_path=new_paths[note_id]))
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
        old_links, new_links = _link_records(left.structure), _link_records(right.structure)
        for source_id, target_id in sorted(old_links - new_links):
            changes.append(SceneChange(f"{source_id} → {target_id}", "removed", item_type="link"))
        for source_id, target_id in sorted(new_links - old_links):
            changes.append(SceneChange(f"{source_id} → {target_id}", "added", item_type="link"))
        for field, item_type in (("characters", "character"), ("character_relationships", "relationship")):
            old_records = _metadata_records(left.structure, field)
            new_records = _metadata_records(right.structure, field)
            for item_id in sorted(old_records.keys() - new_records.keys()):
                changes.append(SceneChange(item_id, "removed", item_type=item_type))
            for item_id in sorted(new_records.keys() - old_records.keys()):
                changes.append(SceneChange(item_id, "added", item_type=item_type))
            for item_id in sorted(old_records.keys() & new_records.keys()):
                if old_records[item_id] != new_records[item_id]:
                    changes.append(SceneChange(item_id, "metadata-changed", item_type=item_type,
                                               changed_fields=_changed_fields(old_records[item_id], new_records[item_id])))
        return RevisionComparison(tuple(changes))

    def delete(self, snapshot: str | Path | RevisionSnapshot, *, confirmed: bool = False) -> None:
        if not confirmed:
            raise PermissionError("Deleting a revision snapshot requires explicit confirmation.")
        path = snapshot.snapshot_path if isinstance(snapshot, RevisionSnapshot) else Path(snapshot)
        if path.parent.resolve() != self.root.resolve():
            raise ValueError("Revision snapshot is outside this revision store.")
        if isinstance(snapshot, RevisionSnapshot):
            if path.is_symlink() or self.read(path).digest != snapshot.digest:
                raise ValueError("Revision snapshot changed since it was selected.")
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


def _changed_fields(before: dict, after: dict) -> tuple[str, ...]:
    missing = object()
    return tuple(sorted(key for key in before.keys() | after.keys()
                        if before.get(key, missing) != after.get(key, missing)))


def _scene_associations(structure: object) -> dict[str, dict[str, dict]]:
    if not isinstance(structure, dict):
        return {}
    result: dict[str, dict[str, dict]] = {}
    def collect(scenes: object) -> None:
        if not isinstance(scenes, list):
            return
        for scene in scenes:
            if not isinstance(scene, dict) or not isinstance(scene.get("id"), str):
                continue
            associations = scene.get("character_associations", [])
            if isinstance(associations, list):
                result[scene["id"]] = {
                    entry["character_id"]: entry for entry in associations
                    if isinstance(entry, dict) and isinstance(entry.get("character_id"), str)
                    and entry["character_id"]
                }
    collect(structure.get("ungrouped_scenes"))
    chapters = structure.get("chapters")
    if isinstance(chapters, list):
        for chapter in chapters:
            if isinstance(chapter, dict):
                collect(chapter.get("scenes"))
    return result


def _metadata_records(structure: object, field: str) -> dict[str, dict]:
    if not isinstance(structure, dict) or not isinstance(structure.get(field, []), list):
        return {}
    return {item["id"]: item for item in structure.get(field, [])
            if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]}


def _document_paths(structure: object) -> dict[str, str]:
    if not isinstance(structure, dict):
        return {}
    result: dict[str, str] = {}
    def collect(items: object) -> None:
        if isinstance(items, list):
            for item in items:
                if (isinstance(item, dict) and isinstance(item.get("id"), str)
                        and isinstance(item.get("path"), str)):
                    result[item["id"]] = item["path"]
    collect(structure.get("notes"))
    collect(structure.get("ungrouped_scenes"))
    chapters = structure.get("chapters")
    if isinstance(chapters, list):
        for chapter in chapters:
            if isinstance(chapter, dict):
                collect(chapter.get("scenes"))
    return result


def _scene_parents(structure: object) -> dict[str, str | None]:
    if (not isinstance(structure, dict) or not isinstance(structure.get("chapters"), list)
            or not isinstance(structure.get("ungrouped_scenes"), list)):
        return {}
    result: dict[str, str | None] = {}
    for chapter in structure["chapters"]:
        if not isinstance(chapter, dict) or not isinstance(chapter.get("id"), str):
            continue
        scenes = chapter.get("scenes")
        if not isinstance(scenes, list):
            continue
        for scene in scenes:
            if isinstance(scene, dict) and isinstance(scene.get("id"), str) and scene["id"]:
                result[scene["id"]] = chapter["id"]
    for scene in structure["ungrouped_scenes"]:
        if isinstance(scene, dict) and isinstance(scene.get("id"), str) and scene["id"]:
            result[scene["id"]] = None
    return result


def _link_records(structure: object) -> set[tuple[str, str]]:
    if not isinstance(structure, dict) or not isinstance(structure.get("links"), list):
        return set()
    return {
        (link["source_id"], link["target_id"])
        for link in structure["links"]
        if isinstance(link, dict) and isinstance(link.get("source_id"), str)
        and isinstance(link.get("target_id"), str) and link["source_id"] and link["target_id"]
    }


def _chapter_records(structure: object) -> dict[str, str | None]:
    """Read ordered chapter identities and titles from a captured manifest."""
    if not isinstance(structure, dict) or not isinstance(structure.get("chapters"), list):
        return {}
    result: dict[str, str | None] = {}
    for chapter in structure["chapters"]:
        if isinstance(chapter, dict) and isinstance(chapter.get("id"), str) and chapter["id"]:
            title = chapter.get("title")
            result[chapter["id"]] = title if isinstance(title, str) else None
    return result


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
