"""Encoding and line-ending helpers."""

import re
from collections import Counter

_BINARY_CONTROLS = re.compile(r"[\x00-\x08\x0e-\x1f\x7f]")
_LINE_ENDINGS = re.compile(r"\r\n|\r|\n")
_LINE_ENDING_NAMES = {"\r\n": "CRLF", "\r": "CR", "\n": "LF"}


def detect_line_ending(text: str) -> str:
    """Choose the most frequent ending, breaking ties by first occurrence."""
    counts = Counter(match.group() for match in _LINE_ENDINGS.finditer(text))
    if not counts:
        return "LF"
    # Counter preserves insertion order, so max retains the first style on a tie.
    return _LINE_ENDING_NAMES[max(counts, key=counts.get)]


def normalize_line_endings(text: str, line_ending: str = "LF") -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.replace("\n", {"LF": "\n", "CRLF": "\r\n", "CR": "\r"}.get(line_ending, "\n"))


def qt_position_to_python_index(text: str, position: int) -> int:
    """Translate Qt's UTF-16 cursor position into a Python code-point index."""
    remaining = max(0, position)
    for index, character in enumerate(text):
        width = 2 if ord(character) > 0xFFFF else 1
        if remaining < width:
            return index
        remaining -= width
        if remaining == 0:
            return index + 1
    return len(text)


def python_index_to_qt_position(text: str, index: int) -> int:
    """Translate a Python code-point index into Qt's UTF-16 cursor position."""
    return sum(2 if ord(character) > 0xFFFF else 1 for character in text[: max(0, min(index, len(text)))])


def has_binary_controls(text: str) -> bool:
    """Reject NUL/non-whitespace ASCII controls, retaining Unicode prose.

    This conservative heuristic allows tab, LF, vertical tab, form feed and CR;
    it does not claim to identify every binary format or guess an encoding.
    """
    return _BINARY_CONTROLS.search(text) is not None
