"""Project-domain models and filesystem operations."""

from .model import (
    FORMAT_VERSION,
    Link,
    Manifest,
    Note,
    Scene,
    Chapter,
    Character,
    CharacterGoal,
    CharacterKnowledge,
    CharacterRelationship,
    CharacterStateChange,
    SceneCharacterAssociation,
    character_from_mapping,
    character_to_mapping,
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
    "Character",
    "CharacterGoal",
    "CharacterKnowledge",
    "CharacterRelationship",
    "CharacterStateChange",
    "Link",
    "Manifest",
    "Note",
    "Project",
    "ProjectError",
    "ProjectFormatError",
    "ProjectPathError",
    "Scene",
    "SceneCharacterAssociation",
    "WordCount",
    "count_words",
    "character_from_mapping",
    "character_to_mapping",
    "parse_outline",
    "validate_project_path",
]
