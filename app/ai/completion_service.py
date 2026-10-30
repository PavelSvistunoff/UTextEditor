"""Pure completion context and request-generation logic."""

from .provider import AIProvider
from .prompts import DEFAULT_AI_ROLE, DEFAULT_COMPLETION_TEMPLATE


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


def complete_project_scene(service: CompletionService, project, notes, open_notes, characters: str,
                           context: str, language: str, **options) -> str:
    """Read bounded project reference material in the completion worker."""
    remaining = 10000
    parts = []
    for note_id, title, note_type in notes:
        if remaining <= 0:
            break
        text = open_notes[note_id] if note_id in open_notes else project.read_note(note_id)
        entry = f"{note_type}: {title}\n{text}"
        parts.append(entry[:remaining])
        remaining -= len(parts[-1])
    reference = "\n\n".join(parts)
    project_context = (
        "Project reference material (background only; continue the text below):\n"
        f"<characters>\n{characters}\n</characters>\n"
        f"<reference_notes>\n{reference}\n</reference_notes>\n\n"
        f"Text to continue:\n{context}"
    )
    return service.complete(project_context, language, **options)
