"""Spellcheck service with revision-aware validation."""

from dataclasses import replace

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

        candidates = [replace(item, revision=revision) for item in suggestions]
        candidates = [item for item in candidates if valid_suggestion(item, text, revision)]
        validated: list[Suggestion] = []
        for suggestion in sorted(candidates, key=lambda item: (item.start, item.end)):
            if validated and suggestion.start < validated[-1].end:
                continue
            validated.append(suggestion)
            if len(validated) == 200:
                break
        return validated
