"""Translate character prose while preserving manifest keys and references."""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass

from .model import Manifest, ProjectError

FieldPath = tuple[str | int, ...]
# These string values are schema tokens, identifiers, or encoded image data.
_PRESERVED_KEYS = {"id", "source_id", "target_id", "character_id", "portrait", "presence", "field", "kind"}


@dataclass(frozen=True)
class CharacterTextField:
    path: FieldPath
    owner_id: str
    owner_name: str
    text: str


@dataclass(frozen=True)
class CharacterFieldTranslation:
    source: CharacterTextField
    text: str


def character_text_fields(mapping: Mapping[str, object]) -> tuple[CharacterTextField, ...]:
    """Capture prose from a validated manifest mapping.

    Mapping keys are never sent for translation. Goal states, knowledge kinds,
    presence and state-change field names keep their machine-readable meanings.
    Blank values retain their original whitespace and need no model request.
    """
    fields: list[CharacterTextField] = []

    def collect(value: object, path: FieldPath, owner_id: str, owner_name: str) -> None:
        if isinstance(value, str):
            if value.strip():
                fields.append(CharacterTextField(path, owner_id, owner_name, value))
        elif isinstance(value, dict):
            for key, child in value.items():
                is_goal_state = key == "status" and len(path) >= 2 and path[-2] == "goals"
                if key in _PRESERVED_KEYS or is_goal_state:
                    continue
                collect(child, (*path, key), owner_id, owner_name)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                collect(child, (*path, index), owner_id, owner_name)

    names = {item["id"]: item["full_name"] for item in mapping.get("characters", [])}
    for index, character in enumerate(mapping.get("characters", [])):
        collect(character, ("characters", index), character["id"], character["full_name"])
    for index, relationship in enumerate(mapping.get("character_relationships", [])):
        collect(relationship, ("character_relationships", index), relationship["id"],
                f"{names[relationship['source_id']]} → {names[relationship['target_id']]}")

    def scene_fields(scenes: list[dict], prefix: FieldPath) -> None:
        for index, scene in enumerate(scenes):
            associations = scene.get("character_associations", [])
            for association_index, association in enumerate(associations):
                collect(association, (*prefix, index, "character_associations", association_index),
                        association["character_id"], f"{names[association['character_id']]} — {scene['title']}")

    for index, chapter in enumerate(mapping.get("chapters", [])):
        scene_fields(chapter["scenes"], ("chapters", index, "scenes"))
    scene_fields(mapping.get("ungrouped_scenes", []), ("ungrouped_scenes",))
    return tuple(fields)


def apply_character_translations(manifest: Manifest, translations: Mapping[FieldPath, str]) -> Manifest:
    """Apply a complete set to a copy; reject missing, foreign or malformed fields."""
    mapping = manifest.to_mapping()
    expected = {field.path for field in character_text_fields(mapping)}
    if set(translations) != expected:
        raise ProjectError("Translation does not contain every character text field, or contains unexpected fields.")
    if any(not isinstance(text, str) or not text.strip() or "\x00" in text for text in translations.values()):
        raise ProjectError("Translated character text is invalid.")
    updated = deepcopy(mapping)
    for path, text in translations.items():
        parent = updated
        for component in path[:-1]:
            parent = parent[component]
        parent[path[-1]] = text
    return Manifest.from_mapping(updated)
