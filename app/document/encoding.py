"""Encoding and line-ending helpers."""


def detect_line_ending(text: str) -> str:
    if "\r\n" in text:
        return "CRLF"
    if "\r" in text:
        return "CR"
    return "LF"


def normalize_line_endings(text: str, line_ending: str = "LF") -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.replace("\n", {"LF": "\n", "CRLF": "\r\n", "CR": "\r"}.get(line_ending, "\n"))
