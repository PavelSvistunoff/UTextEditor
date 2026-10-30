"""Bounded, cancellable search over captured project document descriptors."""

from dataclasses import dataclass
import hashlib
from pathlib import Path
from threading import Event

from .model import ProjectError
from .paths import validate_project_path

MAX_DOCUMENT_BYTES = 4 * 1024 * 1024
MAX_MATCHES = 1000


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


def search_project(root: Path, documents: tuple[SearchDocument, ...], query: str,
                   cancel: Event | None = None) -> SearchResult:
    """Search literal, case-sensitive text without modifying any project data."""
    if not query:
        raise ValueError("Search text cannot be empty.")
    matches: list[SearchMatch] = []
    errors: list[str] = []
    cancelled = False
    limited = False
    for item in documents:
        if cancel is not None and cancel.is_set():
            cancelled = True
            break
        try:
            if item.text is not None:
                text = item.text
                if len(text.encode("utf-8")) > MAX_DOCUMENT_BYTES:
                    raise ValueError("Document exceeds the search size limit")
            else:
                path = validate_project_path(root, item.path)
                with path.open("rb") as stream:
                    raw = stream.read(MAX_DOCUMENT_BYTES + 1)
                if len(raw) > MAX_DOCUMENT_BYTES:
                    raise ValueError("Document exceeds the search size limit")
                text = raw.decode("utf-8")
                if "\x00" in text:
                    raise ValueError("Document contains binary data")
                text = text.replace("\r\n", "\n").replace("\r", "\n")
        except (OSError, UnicodeError, ValueError, ProjectError) as exc:
            errors.append(f"{item.title} ({item.path}): {exc}")
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
            excerpt = text[excerpt_start:min(line_end, index + len(query) + 80)]
            matches.append(SearchMatch(item.kind, item.id, item.title, index, line,
                                       index - line_start + 1, excerpt, digest))
            if len(matches) >= MAX_MATCHES:
                limited = True
                break
            position = index + len(query)
            counted_through = index
        if cancelled or limited:
            break
    return SearchResult(tuple(matches), tuple(errors), cancelled, limited)
