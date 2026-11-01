"""Bounded, cancellable search over captured project document descriptors."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
from threading import Event

from app.document.encoding import has_binary_controls

from .model import ProjectError
from .paths import validate_project_path

MAX_DOCUMENT_BYTES = 4 * 1024 * 1024
MAX_MATCHES = 1000
MAX_ERRORS = 100
MAX_ERROR_LENGTH = 1024


@dataclass(frozen=True)
class SearchDocument:
    kind: str
    id: str
    title: str
    path: str
    text: str | None = None


@dataclass(frozen=True)
class SearchMatch:
    kind: str
    id: str
    title: str
    offset: int
    line: int
    column: int
    excerpt: str
    digest: str


@dataclass(frozen=True)
class SearchResult:
    matches: tuple[SearchMatch, ...]
    errors: tuple[str, ...]
    cancelled: bool
    limited: bool
    omitted_errors: int = 0


def search_project(root: Path, documents: tuple[SearchDocument, ...], query: str,
                   cancel: Event | None = None, open_buffers: dict[Path, str | None] | None = None) -> SearchResult:
    """Search literal text; a None buffer marks an oversized open document."""
    if not query:
        raise ValueError("Search text cannot be empty.")
    buffers = {path.resolve(): text for path, text in (open_buffers or {}).items()}
    matches: list[SearchMatch] = []
    errors: list[str] = []
    omitted_errors = 0
    cancelled = False
    limited = False
    for item in documents:
        if cancel is not None and cancel.is_set():
            cancelled = True
            break
        try:
            path = validate_project_path(root, item.path) if item.text is None else None
            if item.text is None and path in buffers and buffers[path] is None:
                raise ValueError("Document exceeds the search size limit")
            open_text = item.text if item.text is not None else buffers.get(path)
            if open_text is not None:
                text = open_text
                if len(text.encode("utf-8")) > MAX_DOCUMENT_BYTES:
                    raise ValueError("Document exceeds the search size limit")
            else:
                descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
                with os.fdopen(descriptor, "rb") as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise ValueError("Document is not a regular file")
                    raw = stream.read(MAX_DOCUMENT_BYTES + 1)
                if len(raw) > MAX_DOCUMENT_BYTES:
                    raise ValueError("Document exceeds the search size limit")
                text = raw.decode("utf-8")
                if has_binary_controls(text):
                    raise ValueError("Document contains binary data")
                text = text.replace("\r\n", "\n").replace("\r", "\n")
        except (OSError, UnicodeError, ValueError, ProjectError) as exc:
            if len(errors) < MAX_ERRORS:
                errors.append(f"{item.title} ({item.path}): {exc}"[:MAX_ERROR_LENGTH])
            else:
                omitted_errors += 1
            continue
        digest = hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest()
        position = 0
        counted_through = 0
        line = 1
        line_start = 0
        while True:
            if cancel is not None and cancel.is_set():
                cancelled = True
                break
            index = text.find(query, position)
            if index < 0:
                break
            line += text.count("\n", counted_through, index)
            last_newline = text.rfind("\n", counted_through, index)
            if last_newline >= 0:
                line_start = last_newline + 1
            line_end = text.find("\n", index)
            if line_end < 0:
                line_end = len(text)
            excerpt_start = max(line_start, index - 80)
            excerpt = text[excerpt_start:min(line_end, index + min(len(query), 160) + 80)]
            matches.append(SearchMatch(item.kind, item.id, item.title, index, line,
                                       index - line_start + 1, excerpt, digest))
            if len(matches) >= MAX_MATCHES:
                limited = True
                break
            position = index + len(query)
            counted_through = index
        if cancelled or limited:
            break
    return SearchResult(tuple(matches), tuple(errors), cancelled, limited, omitted_errors)
