"""Plain-text formatting operations shared by editor actions and tests."""

import re


def _lines(text: str) -> list[str]:
    """Split only at the line endings supported by the editor."""
    return re.findall(r"[^\r\n]*(?:\r\n|\r|\n|$)", text)[:-1]


def convert_case(text: str, style: str) -> str:
    if style == "upper":
        return text.upper()
    if style == "lower":
        return text.lower()
    if style == "title":
        return text.title()
    raise ValueError(f"Unsupported case style: {style!r}")


def trim_trailing_whitespace(text: str) -> str:
    return re.sub(r"[ \t]+(?=\r|\n|$)", "", text)


def format_like_book(text: str, indent: str = "    ") -> str:
    """Indent the first line of each non-empty paragraph, preserving its layout."""
    result: list[str] = []
    paragraph_start = True
    for line in _lines(text):
        content = line.rstrip("\r\n")
        ending = line[len(content) :]
        if not content.strip():
            result.append(line)
            paragraph_start = True
            continue
        if paragraph_start:
            content = indent + content.lstrip(" \t")
            paragraph_start = False
        result.append(content + ending)
    return "".join(result)


def indent_lines(text: str, width: int = 4) -> str:
    prefix = " " * width
    return "".join(
        prefix + line if line.strip("\r\n") else line
        for line in _lines(text)
    )


def outdent_lines(text: str, width: int = 4) -> str:
    result = []
    for line in _lines(text):
        content = line.lstrip(" \t")
        indentation = line[: len(line) - len(content)]
        if indentation.startswith("\t"):
            indentation = indentation[1:]
        else:
            indentation = indentation[min(width, len(indentation)) :]
        result.append(indentation + content)
    return "".join(result)
