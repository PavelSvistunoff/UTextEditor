"""Validation for the editable Markdown outline used by project setup."""

from __future__ import annotations

from .model import ProjectError

MAX_OUTLINE_CHAPTERS = 40
MAX_OUTLINE_SCENES = 200
MAX_OUTLINE_TITLE_LENGTH = 160


def parse_outline(text: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Parse ``# Chapter`` and ``- Scene`` lines, rejecting other content."""
    if not isinstance(text, str) or not text.strip():
        raise ProjectError("The outline is empty.")

    chapters: list[tuple[str, list[str]]] = []
    scene_count = 0
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            _validate_outline_title(title, line_number)
            chapters.append((title, []))
            if len(chapters) > MAX_OUTLINE_CHAPTERS:
                raise ProjectError(f"An outline can contain at most {MAX_OUTLINE_CHAPTERS} chapters.")
        elif line.startswith("- "):
            if not chapters:
                raise ProjectError(f"Scene on line {line_number} must follow a chapter heading.")
            title = line[2:].strip()
            _validate_outline_title(title, line_number)
            chapters[-1][1].append(title)
            scene_count += 1
            if scene_count > MAX_OUTLINE_SCENES:
                raise ProjectError(f"An outline can contain at most {MAX_OUTLINE_SCENES} scenes.")
        else:
            raise ProjectError(
                f"Unsupported outline text on line {line_number}; use '# Chapter' "
                "and '- Scene' lines only."
            )

    if not chapters:
        raise ProjectError("Add at least one '# Chapter' heading.")
    return tuple((title, tuple(scenes)) for title, scenes in chapters)


def _validate_outline_title(title: str, line_number: int) -> None:
    if not title:
        raise ProjectError(f"Missing title on line {line_number}.")
    if len(title) > MAX_OUTLINE_TITLE_LENGTH:
        raise ProjectError(
            f"Titles must be no longer than {MAX_OUTLINE_TITLE_LENGTH} characters "
            f"(line {line_number})."
        )
    if any(ord(character) < 32 for character in title):
        raise ProjectError(f"Control characters are not allowed in titles (line {line_number}).")
