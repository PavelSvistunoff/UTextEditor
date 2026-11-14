"""Single-worker, deadline-bound automatic context with one verified memory entry."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
import hashlib
import json
from time import monotonic

from app.ai.embeddings import EmbeddingError

from .model import ProjectError
from .rag_context import CapturedContext, ContextRequest, ProjectContextService
from .rag_embeddings import SemanticRetriever
from .rag_index import LexicalIndex
from .rag_sources import BufferText, CaptureCancelled
from .service import Project

RETRIEVAL_SECONDS = 1.0
MAX_CACHED_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True)
class InlineContextResult:
    captured: CapturedContext
    cache_hit: bool
    retrieval_seconds: float


class InlineContextService:
    """Call only from a serialized worker; never indexes or embeds source text."""

    def __init__(self, *, clock: Callable[[], float] = monotonic) -> None:
        self.clock = clock
        self._entry: tuple[object, CapturedContext] | None = None

    def capture(self, project: Project, index: LexicalIndex, request: ContextRequest,
                buffers: Mapping[str, BufferText], *, semantic: SemanticRetriever | None = None,
                embedding_key: object = None,
                is_cancelled: Callable[[], bool] = lambda: False) -> InlineContextResult:
        started = self.clock()
        if is_cancelled():
            raise CaptureCancelled("Inline retrieval was cancelled before capture.")
        deadline = started + RETRIEVAL_SECONDS

        def stopped() -> bool:
            return is_cancelled() or self.clock() >= deadline

        # Generation is checked even on hits. Byte verification below detects disk
        # changes with unchanged timestamps and unsaved-buffer precedence.
        status = index.status()
        if semantic is not None:
            # Cached contexts may not outlive an installed model replacement.
            try:
                embedding_key = (embedding_key, semantic.provider.embedding_identity())
            except (EmbeddingError, OSError, TimeoutError):
                self._entry = None
        vector_path = index.path.with_suffix(".vectors.sqlite3")
        vector_stat = vector_path.stat() if vector_path.exists() else None
        vector_stamp = ((vector_stat.st_mtime_ns, vector_stat.st_size, vector_stat.st_ino)
                        if vector_stat else None)
        key = (str(project.root), project.manifest.project_id,
               json.dumps(project.manifest.to_mapping(), sort_keys=True, ensure_ascii=False),
               status.state, status.generation, request, embedding_key, vector_stamp,
               tuple(sorted((key, value.revision, hashlib.sha256(value.text.encode()).hexdigest())
                            for key, value in buffers.items())))
        try:
            if self._entry is not None and self._entry[0][0] == key:
                cached = self._entry[1]
                try:
                    # The second key component is the saved/effective source
                    # fingerprints. Verify their bytes instead of trusting mtimes.
                    cached.source_capture.verify_current(buffers, is_cancelled=stopped)
                except (OSError, UnicodeError, ProjectError):
                    self._entry = None
                    if stopped():
                        raise CaptureCancelled("Inline context verification expired.")
                else:
                    if stopped():
                        raise CaptureCancelled("Inline context verification expired.")
                    return InlineContextResult(cached, True, self.clock() - started)
            captured = ProjectContextService(index, semantic=semantic).capture(
                project, request, open_buffers=buffers, is_cancelled=stopped)
            if stopped():
                raise CaptureCancelled("Inline retrieval expired.")
        except CaptureCancelled:
            self._entry = None
            if is_cancelled():
                raise
            # A deadline never authorizes reuse of an old optional passage.
            deadline = self.clock() + RETRIEVAL_SECONDS
            captured = ProjectContextService().capture(
                project, replace(request, policy=replace(request.policy, enabled=False)),
                open_buffers=buffers, is_cancelled=stopped)
            if stopped():
                raise CaptureCancelled("Mandatory inline context could not be captured in time.")
            captured = replace(captured, manifest=replace(captured.manifest, notices=(
                *captured.manifest.notices,
                "Automatic retrieval timed out; optional passages were omitted. Only mandatory context was captured.",
            )))
            return InlineContextResult(captured, False, self.clock() - started)
        size = len(captured.prompt.encode()) + sum(len(s.text.encode())
               for s in captured.source_capture.sources + captured.source_capture.disk_sources)
        # Do not retain transient failures or unknown installed model identities.
        if (size <= MAX_CACHED_BYTES and captured.source_capture.complete
                and captured.manifest.retrieval_method != "lexical_fallback"):
            fingerprints = tuple((disk.id, disk.content_digest, disk.metadata_digest,
                                  source.content_digest, source.metadata_digest, source.buffer_revision)
                                 for disk, source in zip(captured.source_capture.disk_sources,
                                                        captured.source_capture.sources, strict=True))
            self._entry = ((key, fingerprints), captured)
        else:
            self._entry = None
        return InlineContextResult(captured, False, self.clock() - started)
