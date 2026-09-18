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
    before = text[:cursor]
    separator = before.rfind("\n\n")
    paragraph_start = separator + 2 if separator >= 0 else 0
    return before[max(paragraph_start, len(before) - maximum_characters):]


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
