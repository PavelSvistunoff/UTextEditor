"""Encoding and line-ending helpers."""


def detect_line_ending(text: str) -> str:
    counts = {"CRLF": text.count("\r\n"), "CR": text.count("\r") - text.count("\r\n")}
    counts["LF"] = text.count("\n") - text.count("\r\n")
    if not any(counts.values()):
        return "LF"
    first_positions = {"CRLF": len(text), "CR": len(text), "LF": len(text)}
    index = 0
    while index < len(text):
        if text.startswith("\r\n", index):
            first_positions["CRLF"] = min(first_positions["CRLF"], index)
            index += 2
        elif text[index] == "\r":
            first_positions["CR"] = min(first_positions["CR"], index)
            index += 1
        elif text[index] == "\n":
            first_positions["LF"] = min(first_positions["LF"], index)
            index += 1
        else:
            index += 1
    return max(counts, key=lambda style: (counts[style], -first_positions[style]))


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
