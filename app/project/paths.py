"""Validation helpers for paths stored in a project manifest."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import re

from .model import ProjectPathError


def validate_project_path(root: Path | str, relative_path: str) -> Path:
    """Return the safely resolved target for a canonical project-relative path.

    Absolute paths, traversal, platform-ambiguous separators, and any path
    whose existing symlink components resolve outside the project are rejected.
    ``strict=False`` also checks the nearest existing parent of a new target.
    """
    project_root = Path(root).resolve()
    if not isinstance(relative_path, str) or not relative_path or "\x00" in relative_path:
        raise ProjectPathError("Project path must be a non-empty relative path")
    if "\\" in relative_path:
        raise ProjectPathError("Project paths must use POSIX '/' separators")
    posix = PurePosixPath(relative_path)
    if (
        posix.is_absolute()
        or re.match(r"^[A-Za-z]:", relative_path)
        or any(part in {"", ".", ".."} for part in relative_path.split("/"))
    ):
        raise ProjectPathError(f"Unsafe project-relative path: {relative_path!r}")
    resolved = (project_root / Path(*posix.parts)).resolve(strict=False)
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ProjectPathError(f"Path escapes the project root: {relative_path!r}") from exc
    return resolved
