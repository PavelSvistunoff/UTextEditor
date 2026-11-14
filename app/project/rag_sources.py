"""Bounded, reproducible source captures for future project retrieval workers."""

from collections.abc import Callable, Iterator, Mapping
from dataclasses import asdict, dataclass, replace
import hashlib
from itertools import islice
import json
import os
from pathlib import Path
import re
import stat

from app.document.encoding import has_binary_controls
from .model import ProjectError, character_to_mapping
from .paths import validate_project_path
from .service import Project

CHUNK_POLICY_VERSION = 1


class CaptureCancelled(ProjectError):
    """Cancellation aborts the capture, rather than becoming a partial result."""


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class BufferText:
    text: str
    revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or type(self.revision) is not int or self.revision < 0:
            raise ValueError("Buffer capture requires text and a nonnegative revision.")


@dataclass(frozen=True)
class CaptureLimits:
    source_bytes: int = 1024 * 1024
    total_bytes: int = 16 * 1024 * 1024
    sources: int = 10000
    chunks: int = 20000
    chunk_characters: int = 1200
    overlap_characters: int = 160

    def __post_init__(self) -> None:
        for name in ("source_bytes", "total_bytes", "sources", "chunks", "chunk_characters"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")
        if type(self.overlap_characters) is not int or not 0 <= self.overlap_characters < self.chunk_characters:
            raise ValueError("Overlap must be nonnegative and smaller than the chunk size.")


@dataclass(frozen=True)
class TextSection:
    field: str
    start: int
    end: int


@dataclass(frozen=True)
class SourceSnapshot:
    project_id: str
    id: str
    kind: str
    title: str
    relative_path: str | None
    note_type: str | None
    scene_order: int | None
    text: str
    content_digest: str
    metadata_json: str
    metadata_digest: str
    sections: tuple[TextSection, ...] = ()
    buffer_revision: int | None = None


@dataclass(frozen=True)
class SourceChunk:
    id: str
    source: SourceSnapshot
    start: int
    end: int
    field: str

    @property
    def text(self) -> str:
        return self.source.text[self.start:self.end]


@dataclass(frozen=True)
class CaptureDiagnostic:
    source_id: str
    reason: str


def chunk_source(source: SourceSnapshot, *, chunk_characters: int = 1200,
                 overlap_characters: int = 160, maximum_chunks: int = 20000,
                 is_cancelled: Callable[[], bool] = lambda: False) -> tuple[SourceChunk, ...]:
    """Keep exact source offsets, preferring paragraph and profile field ends."""
    CaptureLimits(chunk_characters=chunk_characters, overlap_characters=overlap_characters)
    if type(maximum_chunks) is not int or maximum_chunks < 0:
        raise ValueError("Chunk work limit must be a nonnegative integer.")
    chunks = []
    sections = source.sections or (TextSection("", 0, len(source.text)),)
    for section in sections:
        start = section.start
        while start < section.end:
            if is_cancelled():
                raise CaptureCancelled("Project retrieval chunking was cancelled.")
            if len(chunks) >= maximum_chunks:
                raise ProjectError("Chunk-count limit exceeded; source omitted in full.")
            end = min(start + chunk_characters, section.end)
            if end < section.end:
                boundaries = list(re.finditer(r"\r?\n[ \t]*\r?\n", source.text[start:end]))
                if boundaries:
                    end = start + boundaries[-1].end()
            identity = _json((CHUNK_POLICY_VERSION, chunk_characters, overlap_characters,
                              source.project_id, source.kind, source.id, source.content_digest,
                              source.metadata_digest, section.field, start, end))
            chunks.append(SourceChunk(_digest(identity), source, start, end, section.field))
            if end == section.end:
                break
            # Small paragraphs should not create a series of one-character steps.
            overlap = min(overlap_characters, (end - start) // 2)
            start = end - overlap
    return tuple(chunks)


def _read_source(project: Project, relative_path: str, maximum_bytes: int) -> str:
    path = validate_project_path(project.root, relative_path)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ProjectError("Retrieval source is not a regular file.")
        raw = stream.read(maximum_bytes + 1)
    if len(raw) > maximum_bytes:
        raise ProjectError("Retrieval source exceeds the byte limit; coverage is incomplete.")
    text = raw.decode("utf-8")
    if has_binary_controls(text):
        raise ProjectError("Retrieval source contains binary controls.")
    return text


@dataclass(frozen=True)
class ProjectSourceCapture:
    root: Path
    project_id: str
    manifest_digest: str
    disk_sources: tuple[SourceSnapshot, ...]
    sources: tuple[SourceSnapshot, ...]
    disk_chunks: tuple[SourceChunk, ...]
    chunks: tuple[SourceChunk, ...]
    diagnostics: tuple[CaptureDiagnostic, ...]
    limits: CaptureLimits

    @property
    def complete(self) -> bool:
        return not self.diagnostics

    def verify_current(self, open_buffers: Mapping[str, BufferText] | None = None, *,
                       is_cancelled: Callable[[], bool] = lambda: False) -> None:
        """Verify disk independently of overlays; UI supplies fresh buffer stamps."""
        fresh = Project.open(self.root)
        if _digest(_json(fresh.manifest.to_mapping())) != self.manifest_digest:
            raise ProjectError("Project retrieval metadata changed; recapture before using the result.")
        buffers = open_buffers or {}
        for disk, source in zip(self.disk_sources, self.sources, strict=True):
            if is_cancelled():
                raise CaptureCancelled("Project retrieval verification was cancelled.")
            if disk.relative_path is None:
                continue
            try:
                text = _read_source(fresh, disk.relative_path, self.limits.source_bytes)
            except (OSError, UnicodeError, ProjectError) as exc:
                raise ProjectError("Retrieval source changed or became unreadable.") from exc
            if _digest(text) != disk.content_digest:
                raise ProjectError("Retrieval source changed on disk.")
            current = buffers.get(source.id)
            if source.buffer_revision is None:
                if current is not None:
                    raise ProjectError("Retrieval buffer provenance changed.")
            elif current is None or current.revision != source.buffer_revision or _digest(current.text) != source.content_digest:
                raise ProjectError("Retrieval buffer changed.")


def _records(project: Project) -> Iterator[SourceSnapshot]:
    """Yield textless file records and canonical semantic profile snapshots."""
    project_id = project.manifest.project_id
    scene_order = 0
    scene_groups = [(chapter.id, chapter.title, chapter.scenes) for chapter in project.manifest.chapters]
    scene_groups.append((None, None, project.manifest.ungrouped_scenes))
    for chapter_id, chapter_title, scenes in scene_groups:
        for scene in scenes:
            metadata = _json(asdict(scene) | {"chapter_id": chapter_id, "chapter_title": chapter_title,
                                            "scene_order": scene_order})
            yield SourceSnapshot(
                project_id=project_id, id=scene.id, kind="scene", title=scene.title,
                relative_path=scene.path, note_type=None, scene_order=scene_order,
                text="", content_digest="", metadata_json=metadata, metadata_digest=_digest(metadata),
            )
            scene_order += 1
    for note in project.manifest.notes:
        metadata = _json(asdict(note))
        yield SourceSnapshot(
            project_id=project_id, id=note.id, kind="note", title=note.title,
            relative_path=note.path, note_type=note.type, scene_order=None,
            text="", content_digest="", metadata_json=metadata, metadata_digest=_digest(metadata),
        )
    for character in project.manifest.characters:
        mapping = character_to_mapping(character)
        mapping.pop("portrait", None)
        parts = []
        sections = []
        offset = 0
        for field, value in sorted(mapping.items()):
            if field == "id":
                continue
            part = f"{field}: {_json(value)}\n"
            parts.append(part)
            sections.append(TextSection(field, offset, offset + len(part)))
            offset += len(part)
        text = "".join(parts)
        metadata = _json({"id": character.id, "kind": "character"})
        yield SourceSnapshot(
            project_id=project_id, id=character.id, kind="character",
            title=character.display_name or character.full_name,
            relative_path=None, note_type=None, scene_order=None,
            text=text, content_digest=_digest(text), metadata_json=metadata,
            metadata_digest=_digest(metadata), sections=tuple(sections),
        )
    for relationship in project.manifest.character_relationships:
        text = _json(asdict(relationship))
        metadata = _json({"source_id": relationship.source_id, "target_id": relationship.target_id})
        yield SourceSnapshot(
            project_id=project_id, id=relationship.id, kind="relationship", title=relationship.relationship_type,
            relative_path=None, note_type=None, scene_order=None, text=text,
            content_digest=_digest(text), metadata_json=metadata, metadata_digest=_digest(metadata),
        )


def capture_project_sources(project: Project, open_buffers: Mapping[str, BufferText] | None = None, *,
                            limits: CaptureLimits = CaptureLimits(),
                            is_cancelled: Callable[[], bool] = lambda: False) -> ProjectSourceCapture:
    """Capture bounded sources off-thread; diagnostics make every omission explicit."""
    def check_cancelled() -> None:
        if is_cancelled():
            raise CaptureCancelled("Project retrieval capture was cancelled.")

    check_cancelled()
    buffers = dict(open_buffers or {})
    file_ids = {item.id for item in (*tuple(project.iter_scenes()), *project.manifest.notes)}
    if any(key not in file_ids or not isinstance(value, BufferText) for key, value in buffers.items()):
        raise ProjectError("Retrieval buffer map contains an unknown source or invalid buffer capture.")
    manifest_digest = _digest(_json(project.manifest.to_mapping()))
    fresh = Project.open(project.root)
    if _digest(_json(fresh.manifest.to_mapping())) != manifest_digest:
        raise ProjectError("Project retrieval metadata changed before capture.")
    disk_sources = []
    sources = []
    disk_chunks = []
    chunks = []
    diagnostics = []
    record_count = len(file_ids) + len(fresh.manifest.characters) + len(fresh.manifest.character_relationships)
    if record_count > limits.sources:
        diagnostics.append(CaptureDiagnostic("*", f"Source-count limit exceeded; {record_count - limits.sources} sources omitted."))
    used_bytes = 0
    used_chunks = 0
    for record in islice(_records(fresh), limits.sources):
        check_cancelled()
        try:
            disk_text = (_read_source(fresh, record.relative_path, limits.source_bytes)
                         if record.relative_path is not None else record.text)
            disk = replace(record, text=disk_text, content_digest=_digest(disk_text))
            source = disk
            buffer = buffers.get(record.id)
            if buffer is not None:
                if len(buffer.text) > limits.source_bytes:
                    raise ProjectError("Buffer byte limit exceeded; no disk fallback used.")
                source = replace(disk, text=buffer.text, content_digest=_digest(buffer.text),
                                 buffer_revision=buffer.revision)
            if any(len(item.text.encode("utf-8")) > limits.source_bytes for item in (disk, source)):
                raise ProjectError("Source/buffer byte limit exceeded; no disk fallback used.")
            byte_cost = len((disk.text + disk.metadata_json).encode("utf-8"))
            if source is not disk:
                byte_cost += len((source.text + source.metadata_json).encode("utf-8"))
            if used_bytes + byte_cost > limits.total_bytes:
                raise ProjectError("Total source byte limit exceeded.")
            disk_parts = chunk_source(disk, chunk_characters=limits.chunk_characters,
                                      overlap_characters=limits.overlap_characters,
                                      maximum_chunks=limits.chunks - used_chunks, is_cancelled=is_cancelled)
            parts = (disk_parts if source is disk else chunk_source(
                source, chunk_characters=limits.chunk_characters, overlap_characters=limits.overlap_characters,
                maximum_chunks=limits.chunks - used_chunks - len(disk_parts), is_cancelled=is_cancelled))
            chunk_cost = len(disk_parts) + (len(parts) if source is not disk else 0)
        except CaptureCancelled:
            raise
        except (OSError, UnicodeError, ProjectError) as exc:
            diagnostics.append(CaptureDiagnostic(record.id, str(exc)))
            continue
        disk_sources.append(disk)
        sources.append(source)
        disk_chunks.extend(disk_parts)
        chunks.extend(parts)
        used_bytes += byte_cost
        used_chunks += chunk_cost
    check_cancelled()
    capture = ProjectSourceCapture(
        root=fresh.root, project_id=fresh.manifest.project_id, manifest_digest=manifest_digest,
        disk_sources=tuple(disk_sources), sources=tuple(sources), disk_chunks=tuple(disk_chunks),
        chunks=tuple(chunks), diagnostics=tuple(diagnostics), limits=limits,
    )
    capture.verify_current(buffers, is_cancelled=is_cancelled)
    check_cancelled()
    return capture
