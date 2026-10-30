"""Pure completion context and request-generation logic."""

from dataclasses import dataclass
import hashlib

from .provider import AIProvider
from .prompts import DEFAULT_AI_ROLE, DEFAULT_COMPLETION_TEMPLATE

STALE_PROJECT_CONTEXT = object()


def build_context(text: str, cursor: int, *, maximum_characters: int = 4000) -> str:
    """Return a bounded, current-paragraph context ending at ``cursor``.

    Cursor positions can originate from UI events, so clamp them before
    slicing rather than relying on Python's negative-index behaviour.
    """
    if maximum_characters <= 0:
        return ""
    cursor = max(0, min(cursor, len(text)))
    start = max(0, cursor - maximum_characters)
    # Only a separator overlapping or following the window can change its
    # start. Include one preceding character for a boundary-spanning separator.
    separator = text.rfind("\n\n", max(0, start - 1), cursor)
    if separator >= 0:
        start = max(start, separator + 2)
    return text[start:cursor]


class CompletionService:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def complete(
        self,
        context: str,
        language: str,
        *,
        role: str = DEFAULT_AI_ROLE,
        template: str = DEFAULT_COMPLETION_TEMPLATE,
        maximum_tokens: int = 100,
        temperature: float = 0.2,
    ) -> str:
        return self.provider.complete(
            context,
            language,
            role=role,
            template=template,
            maximum_tokens=maximum_tokens,
            temperature=temperature,
        )

    def generate(
        self,
        prompt: str,
        *,
        role: str = DEFAULT_AI_ROLE,
        maximum_tokens: int = 300,
        temperature: float = 0.2,
    ) -> str:
        return self.provider.generate(
            prompt,
            role=role,
            maximum_tokens=maximum_tokens,
            temperature=temperature,
        )


@dataclass(frozen=True)
class CapturedNote:
    id: str
    title: str
    from_buffer: bool
    truncated: bool
    digest: str | None


@dataclass(frozen=True)
class CapturedProjectCompletion:
    context: str
    notes: tuple[CapturedNote, ...]
    omitted_note_count: int


def capture_project_completion(project, notes, open_notes, characters: str,
                               context: str) -> CapturedProjectCompletion:
    """Capture the exact bounded context and its provenance in a worker."""
    remaining = 10000
    parts = []
    included = []
    for note_id, title, note_type in notes:
        if remaining <= 0:
            break
        text = open_notes[note_id] if note_id in open_notes else project.read_note(note_id)
        entry = f"{note_type}: {title}\n{text}"
        parts.append(entry[:remaining])
        remaining -= len(parts[-1])
        digest = None if note_id in open_notes else hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest()
        included.append(CapturedNote(note_id, title, note_id in open_notes, len(entry) > len(parts[-1]), digest))
    reference = "\n\n".join(parts)
    project_context = (
        "Project reference material (background only; continue the text below):\n"
        f"<characters>\n{characters}\n</characters>\n"
        f"<reference_notes>\n{reference}\n</reference_notes>\n\n"
        f"Text to continue:\n{context}"
    )
    return CapturedProjectCompletion(project_context, tuple(included), len(notes) - len(included))


def complete_project_scene(service: CompletionService, project, notes, open_notes, characters: str,
                           context: str, language: str, **options) -> str | object:
    """Read bounded project reference material in the completion worker."""
    captured = capture_project_completion(project, notes, open_notes, characters, context)
    return complete_captured_project_scene(service, project, captured, language, **options)


def complete_captured_project_scene(service: CompletionService, project, captured: CapturedProjectCompletion,
                                    language: str, **options) -> str | object:
    """Discard requests or results when a captured closed note has changed."""
    def unchanged() -> bool:
        for note in captured.notes:
            if note.digest is not None:
                text = project.read_note(note.id)
                if hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest() != note.digest:
                    return False
        return True

    if not unchanged():
        return STALE_PROJECT_CONTEXT
    result = service.complete(captured.context, language, **options)
    return result if unchanged() else STALE_PROJECT_CONTEXT
