"""Spellcheck service with revision-aware validation."""

from .models import Suggestion
from .provider import AIProvider
from .validation import parse_suggestions, valid_suggestion


class SpellcheckService:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def check(self, text: str, language: str, revision: int) -> list[Suggestion]:
        raw = self.provider.check_spelling(text, language)
        if isinstance(raw, str):
            suggestions = parse_suggestions(raw, text, revision)
        elif isinstance(raw, list):
            suggestions = [item for item in raw if isinstance(item, Suggestion)]
        else:
            return []

        validated: list[Suggestion] = []
        for suggestion in suggestions:
            revisioned = Suggestion(
                suggestion.start,
                suggestion.end,
                suggestion.replacement,
                suggestion.type,
                suggestion.explanation,
                suggestion.original_text,
                revision,
                suggestion.source_text,
            )
            if valid_suggestion(revisioned, text, revision):
                validated.append(revisioned)
        return validated
