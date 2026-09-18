"""Safe parsing and validation of untrusted model output."""

import json
from typing import Any

from .models import Suggestion


def parse_suggestions(payload: str | list[dict[str, Any]], source: str, revision: int) -> list[Suggestion]:
    try:
        value: Any = json.loads(payload) if isinstance(payload, str) else payload
        if isinstance(value, dict):
            value = value.get("suggestions", [])
        if not isinstance(value, list):
            return []
    except (json.JSONDecodeError, TypeError):
        return []

    result: list[Suggestion] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        start, end = item.get("start"), item.get("end")
        replacement, kind = item.get("replacement"), item.get("type", "spelling")
        if not isinstance(start, int) or not isinstance(end, int) or not isinstance(replacement, str):
            continue
        if start < 0 or end < start or end > len(source) or not isinstance(kind, str):
            continue
        result.append(
            Suggestion(
                start,
                end,
                replacement,
                kind,
                str(item.get("explanation", "")),
                source[start:end],
                revision,
                source,
            )
        )
    return result


def valid_suggestion(suggestion: Suggestion, text: str, revision: int) -> bool:
    return (
        suggestion.revision == revision
        and 0 <= suggestion.start <= suggestion.end <= len(text)
        and text[suggestion.start:suggestion.end] == suggestion.original_text
        and (not suggestion.source_text or suggestion.source_text == text)
    )
