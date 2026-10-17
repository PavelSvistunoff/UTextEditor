"""Local, bounded recovery snapshots kept separate from canonical documents."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Iterable
from uuid import uuid4
import difflib

from .document import Document


@dataclass(frozen=True)
class RecoveryEntry:
    snapshot_id: str
    document_id: str
    canonical_path: str | None
    project_path: str | None
    text: str
    captured_at: str
    canonical_digest: str | None
    canonical_existed: bool
    project_id: str | None
    snapshot_path: Path


@dataclass(frozen=True)
class RecoveryIssue:
    snapshot_path: Path
    message: str


@dataclass(frozen=True)
class RecoveryScan:
    entries: tuple[RecoveryEntry, ...]
    issues: tuple[RecoveryIssue, ...]


class RecoveryConflictError(ValueError):
    """Raised when a canonical file no longer matches a recovery snapshot."""


class RecoveryStore:
    """Persist recoverable editor buffers without modifying their source files."""

    FORMAT_VERSION = 1

    def __init__(self, root: str | Path | None = None, *, retention: int = 5) -> None:
        if isinstance(retention, bool) or retention < 1:
            raise ValueError("Recovery retention must be at least one snapshot.")
        self.root = Path(root) if root is not None else self._default_root()
        self.retention = retention

    @staticmethod
    def _default_root() -> Path:
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", Path.home())) / "UTextEditor"
        elif os.uname().sysname == "Darwin":
            base = Path.home() / "Library" / "Application Support" / "UTextEditor"
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "utexteditor"
        return base / "recovery"

    def save(
        self,
        document_id: str,
        text: str,
        *,
        canonical_path: str | Path | None = None,
        project_path: str | Path | None = None,
        canonical_digest: str | None = None,
        project_id: str | None = None,
    ) -> RecoveryEntry:
        if not document_id.strip():
            raise ValueError("A document ID is required for recovery.")
        if not isinstance(text, str):
            raise TypeError("Recovery text must be a string.")
        canonical_existed = False
        if canonical_path is not None:
            canonical = Path(canonical_path)
            canonical_existed = canonical.is_file()
            if canonical_existed and canonical_digest is None:
                canonical_digest = self.digest(canonical.read_bytes())

        captured_at = datetime.now(timezone.utc).isoformat()
        snapshot_id = uuid4().hex
        safe_id = hashlib.sha256(document_id.encode("utf-8")).hexdigest()
        directory = self.root / safe_id
        directory.mkdir(parents=True, exist_ok=True)
        try:
            directory.resolve().relative_to(self.root.resolve())
        except ValueError as exc:
            raise OSError("Recovery storage path resolves outside the configured directory.") from exc
        target = directory / f"{captured_at.replace(':', '-')}-{snapshot_id}.json"
        payload = {
            "format_version": self.FORMAT_VERSION,
            "snapshot_id": snapshot_id,
            "document_id": document_id,
            "canonical_path": str(canonical_path) if canonical_path is not None else None,
            "project_path": str(project_path) if project_path is not None else None,
            "text": text,
            "captured_at": captured_at,
            "canonical_digest": canonical_digest,
            "canonical_existed": canonical_existed,
            "project_id": project_id,
        }
        self._atomic_write(target, json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        self._prune(directory, keep=target)
        return RecoveryEntry(
            snapshot_id=snapshot_id,
            document_id=document_id,
            canonical_path=payload["canonical_path"],
            project_path=payload["project_path"],
            text=text,
            captured_at=captured_at,
            canonical_digest=canonical_digest,
            canonical_existed=canonical_existed,
            project_id=project_id,
            snapshot_path=target,
        )

    def scan(self) -> RecoveryScan:
        if not self.root.exists():
            return RecoveryScan((), ())
        entries: list[RecoveryEntry] = []
        issues: list[RecoveryIssue] = []
        root = self.root.resolve()
        for directory in sorted(self.root.iterdir()):
            if not directory.is_dir():
                continue
            try:
                directory.resolve().relative_to(root)
            except ValueError:
                issues.append(RecoveryIssue(directory, "Recovery directory resolves outside the configured location."))
                continue
            for path in sorted(directory.glob("*.json")):
                try:
                    entries.append(self._read_entry(path))
                except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                    issues.append(RecoveryIssue(path, str(exc)))
        entries.sort(key=lambda entry: entry.captured_at, reverse=True)
        return RecoveryScan(tuple(entries), tuple(issues))

    def discard(self, entries: Iterable[RecoveryEntry] | None = None) -> None:
        targets = [entry.snapshot_path for entry in entries] if entries is not None else list(self.root.glob("*/*.json"))
        for target in targets:
            resolved_parent = target.parent.resolve()
            if not target.is_file() or self.root.resolve() not in resolved_parent.parents:
                continue
            target.unlink()
            try:
                target.parent.rmdir()
            except OSError:
                pass

    def discard_document(self, document_id: str) -> None:
        safe_id = hashlib.sha256(document_id.encode("utf-8")).hexdigest()
        directory = self.root / safe_id
        if not directory.exists():
            return
        try:
            directory.resolve().relative_to(self.root.resolve())
        except ValueError as exc:
            raise OSError("Recovery directory resolves outside the configured location.") from exc
        for path in directory.glob("*.json"):
            path.unlink()
        try:
            directory.rmdir()
        except OSError:
            pass

    def restore(self, entry: RecoveryEntry) -> Document:
        canonical_digest = None
        if entry.canonical_path is not None:
            canonical = Path(entry.canonical_path)
            if canonical.exists():
                if not entry.canonical_existed or entry.canonical_digest is None:
                    raise RecoveryConflictError(
                        f"{canonical} appeared after this recovery snapshot; save recovered text elsewhere."
                    )
                current_digest = self.digest(canonical.read_bytes())
                if current_digest != entry.canonical_digest:
                    raise RecoveryConflictError(
                        f"{canonical} changed after this recovery snapshot; compare or save the recovered text elsewhere."
                    )
                canonical_digest = current_digest
            elif entry.canonical_existed:
                raise RecoveryConflictError(
                    f"{canonical} was removed after this recovery snapshot; locate it or save the recovered text elsewhere."
                )
        document = Document(
            text=entry.text,
            path=Path(entry.canonical_path) if entry.canonical_path else None,
            dirty=True,
        )
        document.disk_digest = canonical_digest
        return document

    @staticmethod
    def compare(entry: RecoveryEntry) -> str:
        if entry.canonical_path is None:
            return "No canonical file exists for this untitled document."
        canonical = Path(entry.canonical_path)
        if not canonical.is_file():
            return f"Canonical file is missing: {canonical}"
        current = canonical.read_text(encoding="utf-8-sig")
        difference = "".join(
            difflib.unified_diff(
                current.splitlines(keepends=True),
                entry.text.splitlines(keepends=True),
                fromfile=f"{canonical} (disk)",
                tofile="Recovery snapshot",
            )
        )
        return difference or "The recovery snapshot matches the current canonical file."

    @staticmethod
    def digest(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def _read_entry(cls, path: Path) -> RecoveryEntry:
        with path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
        if not isinstance(payload, dict) or payload.get("format_version") != cls.FORMAT_VERSION:
            raise ValueError("Unsupported recovery snapshot format.")
        required = ("snapshot_id", "document_id", "text", "captured_at")
        if any(not isinstance(payload.get(key), str) or not payload[key] for key in required):
            raise ValueError("Recovery snapshot is missing required fields.")
        if payload.get("canonical_digest") is not None and not isinstance(payload["canonical_digest"], str):
            raise ValueError("Recovery snapshot has an invalid canonical digest.")
        if not isinstance(payload.get("canonical_existed"), bool):
            raise ValueError("Recovery snapshot has an invalid canonical file state.")
        for field in ("canonical_path", "project_path"):
            if payload.get(field) is not None and not isinstance(payload[field], str):
                raise ValueError(f"Recovery snapshot has an invalid {field}.")
        if payload.get("project_id") is not None and not isinstance(payload["project_id"], str):
            raise ValueError("Recovery snapshot has an invalid project ID.")
        return RecoveryEntry(
            snapshot_id=payload["snapshot_id"],
            document_id=payload["document_id"],
            canonical_path=payload.get("canonical_path"),
            project_path=payload.get("project_path"),
            text=payload["text"],
            captured_at=payload["captured_at"],
            canonical_digest=payload.get("canonical_digest"),
            canonical_existed=payload["canonical_existed"],
            project_id=payload.get("project_id"),
            snapshot_path=path,
        )

    def _prune(self, directory: Path, *, keep: Path) -> None:
        snapshots = sorted(
            (path for path in directory.glob("*.json") if path != keep),
            key=lambda path: path.stat().st_mtime_ns,
            reverse=True,
        )
        for path in snapshots[max(0, self.retention - 1):]:
            path.unlink()

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
