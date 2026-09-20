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
    raw = text[suggestion.start:suggestion.end]
    original = suggestion.original_text
    normalized_raw = raw.strip()
    normalized_original = original.strip()
    return (
        suggestion.revision == revision
        and 0 <= suggestion.start <= suggestion.end <= len(text)
        and (raw == original or normalized_raw == normalized_original)
        and (not suggestion.source_text or suggestion.source_text == text)
    )
