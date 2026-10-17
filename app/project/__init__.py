"""Project-domain models and filesystem operations."""

from .model import (
    FORMAT_VERSION,
    Link,
    Manifest,
    Note,
    Scene,
    Chapter,
    ProjectError,
    ProjectFormatError,
    ProjectPathError,
)
from .paths import validate_project_path
from .outline import parse_outline
from .service import Project, WordCount, count_words

__all__ = [
    "FORMAT_VERSION",
    "Chapter",
    "Link",
    "Manifest",
    "Note",
    "Project",
    "ProjectError",
    "ProjectFormatError",
    "ProjectPathError",
    "Scene",
    "WordCount",
    "count_words",
    "parse_outline",
    "validate_project_path",
]
