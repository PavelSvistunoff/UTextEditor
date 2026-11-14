"""Bounded semantic ranking and disposable saved-text vector cache."""

from collections.abc import Callable, Mapping
from contextlib import closing
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import struct
import tempfile

from app.ai.embeddings import (EMBEDDING_FORMAT_VERSION, MAX_EMBEDDING_BATCH,
                               EmbeddingError, EmbeddingIdentity, EmbeddingProvider,
                               embedding_input, normalized_vector)
from .rag_index import LexicalIndex
from .rag_sources import BufferText, CaptureCancelled, ProjectSourceCapture, SourceChunk

MAX_SEMANTIC_CHUNKS = 512
MAX_VECTOR_CACHE_BYTES = 16 * 1024 * 1024
SEMANTIC_MINIMUM_SIMILARITY = 0.35
SEMANTIC_CANDIDATES = 20
RRF_CONSTANT = 60


def _check_cancelled(cancelled: Callable[[], bool]) -> None:
    if cancelled():
        raise CaptureCancelled("Semantic retrieval was cancelled or became stale.")


def fuse_rankings(lexical: tuple[str, ...], semantic: tuple[str, ...]) -> dict[str, float]:
    """Equal-weight reciprocal-rank fusion, independent of incomparable scores."""
    scores: dict[str, float] = {}
    for ranking in (lexical, semantic):
        for rank, chunk_id in enumerate(dict.fromkeys(ranking), 1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (RRF_CONSTANT + rank)
    return scores


def semantic_order(vectors: Mapping[str, tuple[float, ...]], query: tuple[float, ...]) -> tuple[str, ...]:
    """Exact cosine scan of the bounded, normalized captured candidate set."""
    scores = {chunk_id: math.fsum(a * b for a, b in zip(query, vector, strict=True))
              for chunk_id, vector in vectors.items()}
    return tuple(sorted((key for key in scores if scores[key] >= SEMANTIC_MINIMUM_SIMILARITY),
                        key=lambda key: (-scores[key], key))[:SEMANTIC_CANDIDATES])


def _cache_key(chunk: SourceChunk, identity: EmbeddingIdentity) -> str:
    value = (EMBEDDING_FORMAT_VERSION, asdict(identity), chunk.id,
             embedding_input(identity.model, chunk.text, query=False))
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


class VectorCache:
    """Small exact-scan cache; saved vectors only, atomically replaced as a unit."""

    def __init__(self, index: LexicalIndex) -> None:
        self.index = index
        self.path = index.path.with_suffix(".vectors.sqlite3")

    def _guard(self) -> None:
        if self.path.is_symlink() or (self.path.exists() and not self.path.is_file()):
            raise EmbeddingError("Vector cache must be a regular file, not a symbolic link.")
        if self.path.exists() and self.path.stat().st_size > MAX_VECTOR_CACHE_BYTES:
            raise EmbeddingError("Vector cache exceeds its storage limit; delete the cache.")

    @staticmethod
    def _metadata(identity: EmbeddingIdentity) -> str:
        return json.dumps((1, EMBEDDING_FORMAT_VERSION, asdict(identity)), sort_keys=True)

    def read(self, identity: EmbeddingIdentity) -> dict[str, tuple[float, ...]]:
        self._guard()
        if not self.path.exists():
            return {}
        try:
            with closing(sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, timeout=1)) as connection:
                if connection.execute("SELECT value FROM metadata LIMIT 2").fetchall() != [(self._metadata(identity),)]:
                    return {}
                rows = connection.execute("SELECT key, vector FROM vectors LIMIT ?", (MAX_SEMANTIC_CHUNKS + 1,)).fetchall()
                if len(rows) > MAX_SEMANTIC_CHUNKS:
                    raise EmbeddingError("Vector cache exceeds its entry limit.")
                values = {}
                for key, blob in rows:
                    if not isinstance(key, str) or len(key) != 64 or not isinstance(blob, bytes) or len(blob) != identity.dimensions * 4:
                        raise EmbeddingError("Vector cache contains malformed data; delete the cache.")
                    values[key] = normalized_vector(struct.unpack(f"<{identity.dimensions}f", blob), identity.dimensions)
                return values
        except (sqlite3.Error, struct.error) as exc:
            raise EmbeddingError("Vector cache is unreadable; delete it to rebuild.") from exc

    def write(self, identity: EmbeddingIdentity, values: Mapping[str, tuple[float, ...]], *,
              verify: Callable[[], None], is_cancelled: Callable[[], bool]) -> None:
        if len(values) > MAX_SEMANTIC_CHUNKS:
            raise EmbeddingError("Vector cache exceeds its entry limit.")
        # Share the lexical scope lock with maintenance/delete; do not hold it over HTTP.
        with self.index._writing(is_cancelled):
            self._guard()
            verify()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, name = tempfile.mkstemp(prefix=self.index.path.stem + ".vectors.",
                                                suffix=".building", dir=self.path.parent)
            os.close(descriptor)
            staging = Path(name)
            try:
                with closing(sqlite3.connect(staging)) as connection:
                    with connection:
                        connection.execute("CREATE TABLE metadata(value TEXT NOT NULL)")
                        connection.execute("INSERT INTO metadata VALUES (?)", (self._metadata(identity),))
                        connection.execute("CREATE TABLE vectors(key TEXT PRIMARY KEY, vector BLOB NOT NULL)")
                        for key, vector in sorted(values.items()):
                            _check_cancelled(is_cancelled)
                            vector = normalized_vector(vector, identity.dimensions)
                            connection.execute("INSERT INTO vectors VALUES (?, ?)", (key, struct.pack(f"<{identity.dimensions}f", *vector)))
                if staging.stat().st_size > MAX_VECTOR_CACHE_BYTES:
                    raise EmbeddingError("Vector cache exceeds its storage limit.")
                verify()
                _check_cancelled(is_cancelled)
                self._guard()
                os.replace(staging, self.path)
            finally:
                staging.unlink(missing_ok=True)
                Path(str(staging) + "-journal").unlink(missing_ok=True)


@dataclass(frozen=True)
class SemanticRanking:
    scores: Mapping[str, float]
    identity: EmbeddingIdentity
    cached_vectors: int
    embedded_vectors: int


class SemanticRetriever:
    def __init__(self, provider: EmbeddingProvider, index: LexicalIndex) -> None:
        self.provider = provider
        self.cache = VectorCache(index)

    def rank(self, capture: ProjectSourceCapture, chunks: tuple[SourceChunk, ...],
             query: str, lexical: tuple[str, ...], *,
             is_cancelled: Callable[[], bool] = lambda: False) -> SemanticRanking:
        _check_cancelled(is_cancelled)
        if not chunks or len(chunks) > MAX_SEMANTIC_CHUNKS:
            raise EmbeddingError("Semantic retrieval requires 1–512 eligible chunks; lexical fallback used.")
        captured = {chunk.id: chunk for chunk in capture.chunks}
        if (self.cache.index.project_root != capture.root or self.cache.index.project_id != capture.project_id
                or len({chunk.id for chunk in chunks}) != len(chunks)
                or any(captured.get(chunk.id) != chunk for chunk in chunks)):
            raise EmbeddingError("Semantic candidates do not belong to the captured project.")
        index_status = self.cache.index.status(limits=capture.limits)
        if index_status.state not in {"ready", "incomplete"} or not index_status.generation:
            raise EmbeddingError("A current lexical index is required for semantic retrieval.")
        previous_generation = index_status.generation
        identity = self.provider.embedding_identity()
        if not isinstance(identity, EmbeddingIdentity):
            raise EmbeddingError("Embedding provider returned an invalid model identity.")
        _check_cancelled(is_cancelled)
        buffers = {source.id: BufferText(source.text, source.buffer_revision)
                   for source in capture.sources if source.buffer_revision is not None}

        def verify() -> None:
            _check_cancelled(is_cancelled)
            capture.verify_current(buffers, is_cancelled=is_cancelled)
            if self.cache.index.status(limits=capture.limits).generation != previous_generation:
                raise EmbeddingError("Lexical cache changed during semantic retrieval; retry after review.")

        verify()
        cached = self.cache.read(identity)
        vectors = {}
        missing = []
        saved = {}
        hits = 0
        for chunk in chunks:
            _check_cancelled(is_cancelled)
            key = _cache_key(chunk, identity)
            # Buffers are request-local even when their text equals a saved chunk.
            vector = cached.get(key) if chunk.source.buffer_revision is None else None
            if vector is None:
                missing.append(chunk)
            else:
                hits += 1
                vectors[chunk.id] = vector
                saved[key] = vector
        for offset in range(0, len(missing), MAX_EMBEDDING_BATCH):
            _check_cancelled(is_cancelled)
            batch = missing[offset:offset + MAX_EMBEDDING_BATCH]
            values = self.provider.embed(tuple(embedding_input(identity.model, chunk.text, query=False)
                                               for chunk in batch), identity)
            if not isinstance(values, (tuple, list)) or len(values) != len(batch):
                raise EmbeddingError("Embedding provider returned a partial batch.")
            for chunk, value in zip(batch, values, strict=True):
                vector = normalized_vector(value, identity.dimensions)
                vectors[chunk.id] = vector
                if chunk.source.buffer_revision is None:
                    saved[_cache_key(chunk, identity)] = vector
            verify()
        _check_cancelled(is_cancelled)
        query_values = self.provider.embed((embedding_input(identity.model, query, query=True),), identity)
        if not isinstance(query_values, (tuple, list)) or len(query_values) != 1:
            raise EmbeddingError("Embedding provider returned an invalid query batch.")
        query_vector = normalized_vector(query_values[0], identity.dimensions)
        if self.provider.embedding_identity() != identity:
            raise EmbeddingError("Embedding model changed during retrieval.")
        verify()
        semantic = semantic_order(vectors, query_vector)
        # No partial cache publication on provider/query failure or cancellation.
        if saved != cached:
            self.cache.write(identity, saved, verify=verify, is_cancelled=is_cancelled)
        verify()
        return SemanticRanking(fuse_rankings(lexical, semantic), identity, hits, len(missing))
