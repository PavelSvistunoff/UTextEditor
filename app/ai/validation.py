"""Safe parsing and validation of untrusted model output."""

import json
import re
from typing import Any

from .models import Suggestion


def _extract_json_value(payload: str) -> str:
    text = payload.strip()
    if not text:
        return ""

    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    if text.lower().startswith("json"):
        text = text[4:].lstrip()

    for marker, closing in (("[", "]"), ("{", "}")):
        start = text.find(marker)
        if start >= 0:
            end = text.rfind(closing)
            if end > start:
                text = text[start : end + 1]
                break

    return text


def parse_suggestions(payload: str | list[dict[str, Any]], source: str, revision: int) -> list[Suggestion]:
    try:
        if isinstance(payload, str):
            payload = _extract_json_value(payload)
            if not payload:
                return []
            value: Any = json.loads(payload)
        else:
            value = payload
        if isinstance(value, dict):
            if {"start", "end", "replacement"}.issubset(value):
                value = [value]
            else:
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
        if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int) or not isinstance(end, int) or not isinstance(replacement, str):
            continue
        if start < 0 or end <= start or end > len(source) or not isinstance(kind, str):
            continue
        explanation = item.get("explanation", "")
        original = item.get("original_text", source[start:end])
        if not isinstance(explanation, str) or not isinstance(original, str) or original != source[start:end]:
            continue
        if len(result) >= 200 or len(replacement) > 2000 or len(str(item.get("explanation", ""))) > 1000:
            continue
        result.append(
            Suggestion(
                start,
                end,
                replacement,
                kind,
                explanation,
                original,
                revision,
                source,
            )
        )
    return result


def valid_suggestion(suggestion: Suggestion, text: str, revision: int) -> bool:
    # Dataclass annotations do not validate provider-created instances. Check
    # their shape before slicing, sorting or passing replacements into Qt.
    if (
        not isinstance(suggestion, Suggestion)
        or isinstance(suggestion.start, bool) or not isinstance(suggestion.start, int)
        or isinstance(suggestion.end, bool) or not isinstance(suggestion.end, int)
        or not 0 <= suggestion.start < suggestion.end <= len(text)
        or not isinstance(suggestion.replacement, str) or len(suggestion.replacement) > 2000
        or not isinstance(suggestion.type, str)
        or not isinstance(suggestion.explanation, str) or len(suggestion.explanation) > 1000
        or not isinstance(suggestion.original_text, str)
        or not isinstance(suggestion.source_text, str)
    ):
        return False
    raw = text[suggestion.start:suggestion.end]
    original = suggestion.original_text
    if suggestion.type == "spelling":
        if suggestion.start > 0 and suggestion.start < len(text) and text[suggestion.start - 1].isalnum() and text[suggestion.start].isalnum():
            return False
        if suggestion.end > 0 and suggestion.end < len(text) and text[suggestion.end - 1].isalnum() and text[suggestion.end].isalnum():
            return False
    return (
        suggestion.revision == revision
        and 0 <= suggestion.start <= suggestion.end <= len(text)
        and (not original or raw == original)
        and (not suggestion.source_text or suggestion.source_text == text)
    )
