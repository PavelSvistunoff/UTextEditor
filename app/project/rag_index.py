"""Disposable SQLite FTS5 generations, scoped to a project ID and root."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import logging
import os
from pathlib import Path
import sqlite3
import tempfile
from threading import Lock
from uuid import uuid4
from weakref import WeakValueDictionary

from .model import ProjectError
from .rag_sources import (CHUNK_POLICY_VERSION, CaptureCancelled, CaptureLimits,
                          ProjectSourceCapture, SourceChunk, SourceSnapshot)

SCHEMA_VERSION = "1"
_locks = WeakValueDictionary()
_locks_guard = Lock()
logger = logging.getLogger("utexteditor.project.rag_index")


class IndexUnavailable(ProjectError):
    """Cache maintenance failed; normal document editing can continue."""


def fts5_available() -> bool:
    try:
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.execute("CREATE VIRTUAL TABLE probe USING fts5(text)")
        return True
    except sqlite3.Error:
        return False


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(source: SourceSnapshot) -> str:
    return hashlib.sha256(_json(asdict(source)).encode("utf-8")).hexdigest()


def _check_cancelled(is_cancelled: Callable[[], bool]) -> None:
    if is_cancelled():
        raise CaptureCancelled("Retrieval index operation was cancelled or became stale.")


@dataclass(frozen=True)
class IndexStatus:
    state: str
    source_count: int = 0
    chunk_count: int = 0
    generation: str = ""
    manifest_digest: str = ""
    diagnostics: tuple[str, ...] = ()
    changed_sources: int = 0
    removed_sources: int = 0


@dataclass(frozen=True)
class IndexedMatch:
    chunk_id: str
    source_id: str
    title: str
    text: str
    start: int
    end: int
    field: str
    score: float
    source_json: str = ""


@dataclass(frozen=True)
class IndexLookup:
    generation: str
    state: str
    current_source_ids: frozenset[str]
    matches: tuple[IndexedMatch, ...]


class LexicalIndex:
    def __init__(self, cache_root: Path, project_root: Path, project_id: str) -> None:
        self.project_root = Path(project_root).resolve()
        self.project_id = project_id
        scope = hashlib.sha256(_json((project_id, str(self.project_root))).encode("utf-8")).hexdigest()
        self.path = (Path(cache_root) / "retrieval").resolve() / f"{scope}.sqlite3"
        if self.path.is_relative_to(self.project_root):
            raise IndexUnavailable("The retrieval cache must live outside the project directory.")
        with _locks_guard:
            lock = _locks.get(self.path)
            if lock is None:
                lock = Lock()
                _locks[self.path] = lock
            self._lock = lock

    @contextmanager
    def _writing(self, is_cancelled: Callable[[], bool]) -> Iterator[None]:
        while not self._lock.acquire(timeout=0.05):
            _check_cancelled(is_cancelled)
        try:
            _check_cancelled(is_cancelled)
            yield
        finally:
            self._lock.release()

    def _guard_path(self) -> None:
        if self.path.is_symlink() or (self.path.exists() and not self.path.is_file()):
            raise IndexUnavailable("Retrieval cache target must be a regular file, not a symbolic link.")

    def _open_readonly(self) -> sqlite3.Connection:
        self._guard_path()
        return sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, timeout=1)

    def _expected_metadata(self, limits: CaptureLimits) -> dict[str, str]:
        return {
            "schema_version": SCHEMA_VERSION,
            "chunk_policy": _json((CHUNK_POLICY_VERSION, limits.chunk_characters, limits.overlap_characters)),
            "project_id": self.project_id,
            "project_root": str(self.project_root),
        }

    def _status(self, connection: sqlite3.Connection, limits: CaptureLimits) -> IndexStatus:
        if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
            raise IndexUnavailable("Retrieval cache integrity check failed; rebuild it.")
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        if any(metadata.get(key) != value for key, value in self._expected_metadata(limits).items()):
            return IndexStatus("rebuild_required")
        diagnostics = json.loads(metadata["diagnostics"])
        if not isinstance(diagnostics, list) or any(not isinstance(item, str) for item in diagnostics):
            raise IndexUnavailable("Retrieval cache diagnostics are malformed; rebuild it.")
        return IndexStatus(
            state="incomplete" if diagnostics else "ready",
            source_count=connection.execute("SELECT count(*) FROM sources").fetchone()[0],
            chunk_count=connection.execute("SELECT count(*) FROM chunks").fetchone()[0],
            generation=metadata["generation"], manifest_digest=metadata["manifest_digest"],
            diagnostics=tuple(diagnostics),
        )

    def status(self, *, limits: CaptureLimits = CaptureLimits()) -> IndexStatus:
        """Inspect the committed snapshot only; this does not assert source freshness."""
        if not fts5_available():
            return IndexStatus("unavailable", diagnostics=("SQLite FTS5 is not available in this Python installation.",))
        try:
            self._guard_path()
            if not self.path.exists():
                return IndexStatus("missing")
            with closing(self._open_readonly()) as connection:
                return self._status(connection, limits)
        except (sqlite3.Error, OSError, ValueError, KeyError, IndexUnavailable) as exc:
            return IndexStatus("error", diagnostics=(str(exc),))

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.executescript("""
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE sources (source_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                                  snapshot_json TEXT NOT NULL);
            CREATE VIRTUAL TABLE chunks USING fts5(
                chunk_id UNINDEXED, source_id UNINDEXED, start UNINDEXED,
                end UNINDEXED, field UNINDEXED, title, text, tokenize='unicode61'
            );
        """)

    def _write_source(self, connection: sqlite3.Connection, source: SourceSnapshot,
                      chunks: tuple[SourceChunk, ...]) -> None:
        connection.execute("DELETE FROM chunks WHERE source_id = ?", (source.id,))
        connection.execute("INSERT OR REPLACE INTO sources VALUES (?, ?, ?)",
                           (source.id, _fingerprint(source), _json(asdict(source))))
        connection.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?)", (
            (chunk.id, source.id, chunk.start, chunk.end, chunk.field, source.title, chunk.text)
            for chunk in chunks
        ))

    def refresh(self, capture: ProjectSourceCapture, *, force: bool = False,
                is_cancelled: Callable[[], bool] = lambda: False) -> IndexStatus:
        """Copy then incrementally update; publish a verified complete generation."""
        if not fts5_available():
            raise IndexUnavailable("SQLite FTS5 is not available in this Python installation.")
        if capture.root != self.project_root or capture.project_id != self.project_id:
            raise IndexUnavailable("Retrieval capture belongs to another project scope.")
        if any(source.buffer_revision is not None for source in capture.disk_sources):
            raise IndexUnavailable("Unsaved sources cannot be persisted in the disk index.")
        disk_capture = replace(capture, sources=capture.disk_sources, chunks=capture.disk_chunks)
        with self._writing(is_cancelled):
            self._guard_path()
            disk_capture.verify_current(is_cancelled=is_cancelled)
            old = self.status(limits=capture.limits)
            try:
                return self._build(disk_capture, old, force, is_cancelled)
            except (OSError, sqlite3.Error) as exc:
                raise IndexUnavailable(f"Could not update retrieval cache: {exc}") from exc

    def _build(self, capture: ProjectSourceCapture, old: IndexStatus, force: bool,
               is_cancelled: Callable[[], bool]) -> IndexStatus:
        _check_cancelled(is_cancelled)
        fingerprints = {source.id: _fingerprint(source) for source in capture.disk_sources}
        diagnostics = tuple(f"{item.source_id}: {item.reason}" for item in capture.diagnostics)
        compatible = old.state in {"ready", "incomplete"} and not force
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=self.path.stem + ".", suffix=".building",
                                         dir=self.path.parent, delete=False) as stream:
            staging = Path(stream.name)
        try:
            with closing(sqlite3.connect(staging)) as connection:
                if compatible:
                    with closing(self._open_readonly()) as previous:
                        previous.backup(connection)
                else:
                    self._create_schema(connection)
                existing = dict(connection.execute("SELECT source_id, fingerprint FROM sources"))
                changed = {key for key, value in fingerprints.items() if existing.get(key) != value}
                removed = set(existing) - set(fingerprints)
                if (compatible and not changed and not removed and old.manifest_digest == capture.manifest_digest
                        and old.diagnostics == diagnostics):
                    capture.verify_current(is_cancelled=is_cancelled)
                    _check_cancelled(is_cancelled)
                    return replace(old, changed_sources=0, removed_sources=0)
                grouped = defaultdict(list)
                for chunk in capture.disk_chunks:
                    grouped[chunk.source.id].append(chunk)
                with connection:
                    for source_id in removed:
                        _check_cancelled(is_cancelled)
                        connection.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
                        connection.execute("DELETE FROM sources WHERE source_id = ?", (source_id,))
                    for source in capture.disk_sources:
                        _check_cancelled(is_cancelled)
                        if source.id in changed:
                            parts = tuple(grouped[source.id])
                            if any(chunk.source != source for chunk in parts):
                                raise IndexUnavailable("Chunk provenance does not match its disk source.")
                            self._write_source(connection, source, parts)
                    generation = str(uuid4())
                    metadata = self._expected_metadata(capture.limits) | {
                        "generation": generation, "manifest_digest": capture.manifest_digest,
                        "diagnostics": _json(diagnostics),
                    }
                    connection.executemany("INSERT OR REPLACE INTO metadata VALUES (?, ?)", metadata.items())
                result = replace(self._status(connection, capture.limits),
                                 changed_sources=len(changed), removed_sources=len(removed))
            capture.verify_current(is_cancelled=is_cancelled)
            _check_cancelled(is_cancelled)
            self._guard_path()
            os.replace(staging, self.path)
            return result
        finally:
            for path in (staging, Path(str(staging) + "-journal")):
                try:
                    path.unlink(missing_ok=True)
                except OSError as exc:
                    logger.warning("Could not remove retrieval staging cache %s: %s", path, exc)

    def delete(self, *, is_cancelled: Callable[[], bool] = lambda: False) -> IndexStatus:
        with self._writing(is_cancelled):
            try:
                self._guard_path()
                candidates = [self.path, *(Path(str(self.path) + suffix)
                                          for suffix in ("-journal", "-wal", "-shm"))]
                if self.path.parent.exists():
                    candidates.extend(self.path.parent.glob(self.path.stem + ".*.building*"))
                for path in candidates:
                    if path.is_symlink() or (path.exists() and not path.is_file()):
                        raise IndexUnavailable("Refusing a non-regular retrieval cache file.")
                for path in candidates:
                    _check_cancelled(is_cancelled)
                    path.unlink(missing_ok=True)
                return IndexStatus("missing")
            except OSError as exc:
                raise IndexUnavailable(f"Could not delete retrieval cache: {exc}") from exc

    def search_terms(self, terms: tuple[str, ...], *, limit: int = 20,
                     limits: CaptureLimits = CaptureLimits()) -> tuple[IndexedMatch, ...]:
        """Literal lexical matches; workflow ranking and exclusions belong to RAG-04."""
        if type(limit) is not int or not 1 <= limit <= 100 or len(terms) > 64:
            raise ValueError("Retrieval query exceeds its term/result limit.")
        if any(not isinstance(term, str) or len(term) > 256 for term in terms):
            raise ValueError("Retrieval terms must be bounded strings.")
        query = " OR ".join('"' + term.replace('"', '""') + '"' for term in terms if term.strip())
        if not query:
            return ()
        try:
            with closing(self._open_readonly()) as connection:
                if self._status(connection, limits).state not in {"ready", "incomplete"}:
                    raise IndexUnavailable("Retrieval index requires a rebuild.")
                rows = connection.execute("""
                    SELECT chunk_id, chunks.source_id, title, text, start, end, field,
                           bm25(chunks), snapshot_json
                    FROM chunks JOIN sources ON chunks.source_id = sources.source_id
                    WHERE chunks MATCH ? ORDER BY bm25(chunks), chunks.source_id, start, chunk_id LIMIT ?
                """, (query, limit))
                return tuple(IndexedMatch(*row) for row in rows)
        except (OSError, sqlite3.Error, ValueError, KeyError) as exc:
            raise IndexUnavailable(f"Could not read retrieval cache: {exc}") from exc

    def lookup_capture(self, terms: tuple[str, ...], sources: tuple[SourceSnapshot, ...], *,
                       limits: CaptureLimits = CaptureLimits(),
                       is_cancelled: Callable[[], bool] = lambda: False) -> IndexLookup:
        """Filter request scope and freshness before ranking, in one read snapshot.

        The temporary allowlist lives only in memory, even on a read-only main
        connection. Stored source JSON is not returned for every passage; callers
        already hold authoritative source captures and must validate chunk spans.
        """
        if len(terms) > 64 or any(not isinstance(term, str) or len(term) > 256 for term in terms):
            raise ValueError("Retrieval query exceeds its term limit.")
        if len(sources) > limits.sources or any(source.project_id != self.project_id for source in sources):
            raise IndexUnavailable("Retrieval allowlist exceeds its source limit or project scope.")
        query = " OR ".join('"' + term.replace('"', '""') + '"' for term in terms if term.strip())
        _check_cancelled(is_cancelled)
        cancellation_observed = False

        def progress() -> int:
            nonlocal cancellation_observed
            cancellation_observed = cancellation_observed or is_cancelled()
            return int(cancellation_observed)

        try:
            with closing(self._open_readonly()) as connection:
                connection.set_progress_handler(progress, 1000)
                connection.execute("PRAGMA temp_store=MEMORY")
                connection.execute("BEGIN")
                status = self._status(connection, limits)
                if status.state not in {"ready", "incomplete"}:
                    raise IndexUnavailable("Retrieval index requires a rebuild.")
                connection.execute("CREATE TEMP TABLE request_sources (source_id TEXT PRIMARY KEY, fingerprint TEXT)")
                connection.executemany("INSERT INTO request_sources VALUES (?, ?)", (
                    (source.id, _fingerprint(replace(source, buffer_revision=None))) for source in sources
                ))
                current = frozenset(row[0] for row in connection.execute("""
                    SELECT sources.source_id FROM sources JOIN request_sources
                    ON sources.source_id = request_sources.source_id
                    AND sources.fingerprint = request_sources.fingerprint
                """))
                matches = []
                if query:
                    rows = connection.execute("""
                        SELECT chunk_id, chunks.source_id, title, text, start, end, field, bm25(chunks)
                        FROM chunks JOIN sources ON chunks.source_id = sources.source_id
                        JOIN request_sources ON sources.source_id = request_sources.source_id
                            AND sources.fingerprint = request_sources.fingerprint
                        WHERE chunks MATCH ?
                        ORDER BY bm25(chunks), chunks.source_id, start, chunk_id LIMIT ?
                    """, (query, limits.chunks))
                    for row in rows:
                        _check_cancelled(is_cancelled)
                        matches.append(IndexedMatch(*row))
                _check_cancelled(is_cancelled)
                return IndexLookup(status.generation, status.state, current, tuple(matches))
        except sqlite3.Error as exc:
            if cancellation_observed:
                raise CaptureCancelled("Retrieval query was cancelled or became stale.") from exc
            _check_cancelled(is_cancelled)
            raise IndexUnavailable(f"Could not query retrieval cache: {exc}") from exc
        except (OSError, ValueError, KeyError) as exc:
            raise IndexUnavailable(f"Could not query retrieval cache: {exc}") from exc
