"""Version 1 project manifest models and validation.

The UTF-8 YAML manifest, ``utexteditor.yaml``, has this schema::

    format_version: 1
    project_id: <stable UUID>
    title: <project title>
    chapters:
      - id: <stable UUID>
        title: <chapter title>
        scenes:
          - {id: <stable UUID>, title: <title>, path: manuscript/file.txt}
    ungrouped_scenes: [<scene records>]
    notes:
      - {id: <stable UUID>, type: character|setting|timeline|research|general,
         title: <title>, path: notes/file.txt}
    links:
      - {source_id: <note ID>, target_id: <scene or note ID>}

IDs are unique across the project. Paths are project-relative POSIX paths.
Unknown fields are rejected so an older implementation cannot silently erase
metadata it does not understand. Missing link targets are allowed to remain
as orphans after an explicitly removed or unavailable target.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
import re
from uuid import UUID

FORMAT_VERSION = 1
MANIFEST_NAME = "utexteditor.yaml"
NOTE_TYPES = frozenset({"character", "setting", "timeline", "research", "general"})
CHARACTER_GOAL_STATES = frozenset({"active", "completed", "abandoned", "blocked"})
CHARACTER_KNOWLEDGE_KINDS = frozenset({
    "objective_truth", "knows", "believes", "suspects", "does_not_know",
    "conceals", "others_believe",
})
CHARACTER_PRESENCE = frozenset({"present", "mentioned"})
CHARACTER_BACKGROUND_FIELDS = frozenset({
    "age", "occupation", "origin", "appearance", "history", "social_status",
})
CHARACTER_PERSONALITY_FIELDS = frozenset({
    "traits", "strengths", "weaknesses", "fears", "values", "habits",
    "emotional_triggers", "contradictions", "speech_patterns", "attitudes",
})
CHARACTER_ARC_FIELDS = frozenset({
    "initial_worldview", "initial_state", "desired_transformation", "lessons",
    "turning_points", "expected_end_state", "current_state", "unresolved_conflicts",
})


class ProjectError(Exception):
    """Base class for recoverable project-domain errors."""


class ProjectFormatError(ProjectError):
    """The manifest is malformed, unsupported, or internally inconsistent."""


class ProjectPathError(ProjectError):
    """A project-relative path is invalid or escapes the project root."""


@dataclass
class Scene:
    id: str
    title: str
    path: str
    character_associations: list[SceneCharacterAssociation] = field(default_factory=list)


@dataclass
class Chapter:
    id: str
    title: str
    scenes: list[Scene] = field(default_factory=list)


@dataclass
class Note:
    id: str
    type: str
    title: str
    path: str


@dataclass(frozen=True)
class Link:
    source_id: str
    target_id: str


@dataclass
class CharacterGoal:
    description: str
    status: str = "active"
    priority: int = 3
    notes: str = ""


@dataclass
class CharacterKnowledge:
    kind: str
    statement: str


@dataclass
class CharacterRelationship:
    id: str
    source_id: str
    target_id: str
    relationship_type: str = "unknown"
    description: str = ""
    attitude: str = ""
    trust: int | None = None
    status: str = "active"
    history: str = ""
    shared_secrets: str = ""
    development_notes: str = ""


@dataclass
class SceneCharacterAssociation:
    character_id: str
    presence: str = "present"
    purpose: str = ""
    relevant_goals: list[str] = field(default_factory=list)
    development_notes: list[str] = field(default_factory=list)


@dataclass
class Character:
    id: str
    full_name: str
    display_name: str = ""
    aliases: list[str] = field(default_factory=list)
    role: str = "supporting character"
    description: str = ""
    background: dict[str, str] = field(default_factory=dict)
    personality: dict[str, list[str]] = field(default_factory=dict)
    primary_motivation: str = ""
    secondary_motivations: list[str] = field(default_factory=list)
    goals: list[CharacterGoal] = field(default_factory=list)
    desires: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    obstacles: list[str] = field(default_factory=list)
    accepted_risks: list[str] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)
    internal_conflicts: list[str] = field(default_factory=list)
    knowledge: list[CharacterKnowledge] = field(default_factory=list)
    arc: dict[str, str] = field(default_factory=dict)


@dataclass
class Manifest:
    project_id: str
    title: str
    chapters: list[Chapter] = field(default_factory=list)
    ungrouped_scenes: list[Scene] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    characters: list[Character] = field(default_factory=list)
    character_relationships: list[CharacterRelationship] = field(default_factory=list)
    format_version: int = FORMAT_VERSION

    @classmethod
    def from_mapping(cls, data: object) -> Manifest:
        root = _mapping(data, "manifest")
        _keys(
            root,
            {"format_version", "project_id", "title", "chapters",
             "ungrouped_scenes", "notes", "links"},
            {"format_version", "project_id", "title", "chapters",
             "ungrouped_scenes", "notes", "links", "characters",
             "character_relationships"},
            "manifest",
        )
        version = root["format_version"]
        if type(version) is not int or version != FORMAT_VERSION:
            raise ProjectFormatError(
                f"Unsupported project format version: {version!r} "
                f"(supported: {FORMAT_VERSION})"
            )
        manifest = cls(
            project_id=_string(root["project_id"], "project_id"),
            title=_title(root["title"], "project title"),
            chapters=[
                _chapter(item, f"chapters[{index}]")
                for index, item in enumerate(_list(root["chapters"], "chapters"))
            ],
            ungrouped_scenes=[
                _scene(item, f"ungrouped_scenes[{index}]")
                for index, item in enumerate(
                    _list(root["ungrouped_scenes"], "ungrouped_scenes")
                )
            ],
            notes=[
                _note(item, f"notes[{index}]")
                for index, item in enumerate(_list(root["notes"], "notes"))
            ],
            links=[
                _link(item, f"links[{index}]")
                for index, item in enumerate(_list(root["links"], "links"))
            ],
            characters=[
                _character(item, f"characters[{index}]")
                for index, item in enumerate(_list(root.get("characters", []), "characters"))
            ],
            character_relationships=[
                _character_relationship(item, f"character_relationships[{index}]")
                for index, item in enumerate(
                    _list(root.get("character_relationships", []), "character_relationships")
                )
            ],
            format_version=version,
        )
        manifest.validate()
        return manifest

    def validate(self) -> None:
        _uuid(self.project_id, "project_id")
        _title(self.title, "project title")
        if type(self.format_version) is not int or self.format_version != FORMAT_VERSION:
            raise ProjectFormatError(f"Unsupported project format version: {self.format_version!r}")

        seen_ids = {self.project_id}
        scene_ids: set[str] = set()
        note_ids: set[str] = set()
        character_ids: set[str] = set()
        paths: set[str] = set()

        def unique_id(value: str, label: str) -> None:
            _uuid(value, label)
            if value in seen_ids:
                raise ProjectFormatError(f"Duplicate project ID: {value}")
            seen_ids.add(value)

        def add_scene(scene: Scene, label: str) -> None:
            _validate_scene(scene, label)
            unique_id(scene.id, f"{label}.id")
            scene_ids.add(scene.id)
            add_path(scene.path, label)

        def add_path(path: str, label: str) -> None:
            _relative_path(path, label)
            if path in paths:
                raise ProjectFormatError(f"Duplicate project path: {path!r}")
            paths.add(path)

        for ci, chapter in enumerate(self.chapters):
            label = f"chapters[{ci}]"
            _validate_chapter(chapter, label)
            unique_id(chapter.id, f"{label}.id")
            for si, scene in enumerate(chapter.scenes):
                add_scene(scene, f"{label}.scenes[{si}]")
        for si, scene in enumerate(self.ungrouped_scenes):
            add_scene(scene, f"ungrouped_scenes[{si}]")
        for ni, note in enumerate(self.notes):
            label = f"notes[{ni}]"
            _validate_note(note, label)
            unique_id(note.id, f"{label}.id")
            note_ids.add(note.id)
            add_path(note.path, label)

        for ci, character in enumerate(self.characters):
            label = f"characters[{ci}]"
            _validate_character(character, label)
            unique_id(character.id, f"{label}.id")
            character_ids.add(character.id)

        for ci, chapter in enumerate(self.chapters):
            for si, scene in enumerate(chapter.scenes):
                _validate_scene_associations(scene, character_ids, f"chapters[{ci}].scenes[{si}]")
        for si, scene in enumerate(self.ungrouped_scenes):
            _validate_scene_associations(scene, character_ids, f"ungrouped_scenes[{si}]")

        relationship_pairs: set[tuple[str, str]] = set()
        for ri, relationship in enumerate(self.character_relationships):
            label = f"character_relationships[{ri}]"
            _validate_character_relationship(relationship, label)
            unique_id(relationship.id, f"{label}.id")
            if relationship.source_id not in character_ids or relationship.target_id not in character_ids:
                raise ProjectFormatError(f"{label} references an unknown character")
            if relationship.source_id == relationship.target_id:
                raise ProjectFormatError(f"{label} cannot link a character to itself")
            pair = (relationship.source_id, relationship.target_id)
            if pair in relationship_pairs:
                raise ProjectFormatError(f"Duplicate directed character relationship: {pair!r}")
            relationship_pairs.add(pair)

        link_pairs: set[tuple[str, str]] = set()
        for link in self.links:
            if link.source_id not in note_ids:
                raise ProjectFormatError(
                    f"Link source {link.source_id!r} is not a reference note"
                )
            _uuid(link.target_id, "link.target_id")
            pair = (link.source_id, link.target_id)
            if pair in link_pairs:
                raise ProjectFormatError(f"Duplicate note link: {pair!r}")
            link_pairs.add(pair)

    def to_mapping(self) -> dict[str, object]:
        self.validate()
        result = {
            "format_version": self.format_version,
            "project_id": self.project_id,
            "title": self.title,
            "chapters": [
                {
                    "id": chapter.id,
                    "title": chapter.title,
                    "scenes": [_scene_mapping(scene) for scene in chapter.scenes],
                }
                for chapter in self.chapters
            ],
            "ungrouped_scenes": [_scene_mapping(scene) for scene in self.ungrouped_scenes],
            "notes": [
                {"id": note.id, "type": note.type, "title": note.title, "path": note.path}
                for note in self.notes
            ],
            "links": [
                {"source_id": link.source_id, "target_id": link.target_id}
                for link in self.links
            ],
        }
        if self.characters:
            result["characters"] = [_character_mapping(item) for item in self.characters]
        if self.character_relationships:
            result["character_relationships"] = [
                _character_relationship_mapping(item)
                for item in self.character_relationships
            ]
        return result


def _mapping(value: object, label: str) -> dict:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ProjectFormatError(f"{label} must be a mapping with string keys")
    return value


def _keys(value: dict, required: set[str], allowed: set[str], label: str) -> None:
    missing = required - value.keys()
    extra = value.keys() - allowed
    if missing:
        raise ProjectFormatError(f"{label} is missing fields: {', '.join(sorted(missing))}")
    if extra:
        raise ProjectFormatError(f"{label} has unknown fields: {', '.join(sorted(extra))}")


def _list(value: object, label: str) -> list:
    if not isinstance(value, list):
        raise ProjectFormatError(f"{label} must be a list")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ProjectFormatError(f"{label} must be a non-empty string")
    return value


def _title(value: object, label: str) -> str:
    result = _string(value, label)
    if not result.strip() or any(ord(char) < 32 for char in result):
        raise ProjectFormatError(f"{label} must contain visible text without control characters")
    return result


def _uuid(value: str, label: str) -> None:
    try:
        parsed = UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ProjectFormatError(f"{label} must be a UUID") from exc
    if str(parsed) != value:
        raise ProjectFormatError(f"{label} must use canonical lowercase UUID form")


def _scene(value: object, label: str) -> Scene:
    row = _mapping(value, label)
    _keys(row, {"id", "title", "path"}, {"id", "title", "path", "character_associations"}, label)
    return Scene(
        _string(row["id"], f"{label}.id"),
        _title(row["title"], f"{label}.title"),
        _string(row["path"], f"{label}.path"),
        [_scene_association(item, f"{label}.character_associations[{index}]")
         for index, item in enumerate(_list(row.get("character_associations", []), f"{label}.character_associations"))],
    )


def _chapter(value: object, label: str) -> Chapter:
    row = _mapping(value, label)
    _keys(row, {"id", "title", "scenes"}, {"id", "title", "scenes"}, label)
    return Chapter(
        _string(row["id"], f"{label}.id"),
        _title(row["title"], f"{label}.title"),
        [
            _scene(item, f"{label}.scenes[{index}]")
            for index, item in enumerate(_list(row["scenes"], f"{label}.scenes"))
        ],
    )


def _note(value: object, label: str) -> Note:
    row = _mapping(value, label)
    _keys(row, {"id", "type", "title", "path"}, {"id", "type", "title", "path"}, label)
    note_type = _string(row["type"], f"{label}.type")
    if note_type not in NOTE_TYPES:
        raise ProjectFormatError(f"{label}.type must be one of: {', '.join(sorted(NOTE_TYPES))}")
    return Note(
        _string(row["id"], f"{label}.id"),
        note_type,
        _title(row["title"], f"{label}.title"),
        _string(row["path"], f"{label}.path"),
    )


def _link(value: object, label: str) -> Link:
    row = _mapping(value, label)
    _keys(row, {"source_id", "target_id"}, {"source_id", "target_id"}, label)
    return Link(
        _string(row["source_id"], f"{label}.source_id"),
        _string(row["target_id"], f"{label}.target_id"),
    )


def _validate_scene(scene: Scene, label: str) -> None:
    if not isinstance(scene, Scene):
        raise ProjectFormatError(f"{label} must be a scene")
    _uuid(scene.id, f"{label}.id")
    _title(scene.title, f"{label}.title")
    _relative_path(scene.path, f"{label}.path")


def _validate_chapter(chapter: Chapter, label: str) -> None:
    if not isinstance(chapter, Chapter) or not isinstance(chapter.scenes, list):
        raise ProjectFormatError(f"{label} must be a chapter with a scene list")
    _uuid(chapter.id, f"{label}.id")
    _title(chapter.title, f"{label}.title")


def _validate_note(note: Note, label: str) -> None:
    if not isinstance(note, Note):
        raise ProjectFormatError(f"{label} must be a note")
    _uuid(note.id, f"{label}.id")
    if not isinstance(note.type, str) or note.type not in NOTE_TYPES:
        raise ProjectFormatError(f"{label}.type is not a supported note type")
    _title(note.title, f"{label}.title")
    _relative_path(note.path, f"{label}.path")


def _relative_path(value: str, label: str) -> None:
    _string(value, label)
    posix = PurePosixPath(value)
    if (
        "\\" in value
        or posix.is_absolute()
        or re.match(r"^[A-Za-z]:", value)
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise ProjectFormatError(f"{label} must be a safe project-relative POSIX path")


def _scene_association(value: object, label: str) -> SceneCharacterAssociation:
    row = _mapping(value, label)
    _keys(row, {"character_id"}, {"character_id", "presence", "purpose", "relevant_goals", "development_notes"}, label)
    return SceneCharacterAssociation(
        _string(row["character_id"], f"{label}.character_id"),
        _string(row.get("presence", "present"), f"{label}.presence"),
        _text(row.get("purpose", ""), f"{label}.purpose"),
        _text_list(row.get("relevant_goals", []), f"{label}.relevant_goals"),
        _text_list(row.get("development_notes", []), f"{label}.development_notes"),
    )


def _character(value: object, label: str) -> Character:
    row = _mapping(value, label)
    fields = {"id", "full_name", "display_name", "aliases", "role", "description", "background", "personality", "primary_motivation", "secondary_motivations", "goals", "desires", "needs", "obstacles", "accepted_risks", "refusals", "internal_conflicts", "knowledge", "arc"}
    _keys(row, {"id", "full_name"}, fields, label)
    goals = []
    for i, value in enumerate(_list(row.get("goals", []), f"{label}.goals")):
        item = _mapping(value, f"{label}.goals[{i}]")
        _keys(item, {"description"}, {"description", "status", "priority", "notes"}, f"{label}.goals[{i}]")
        goals.append(CharacterGoal(_text(item["description"], f"{label}.goals[{i}].description"), _text(item.get("status", "active"), f"{label}.goals[{i}].status"), item.get("priority", 3), _text(item.get("notes", ""), f"{label}.goals[{i}].notes")))
    knowledge = []
    for i, value in enumerate(_list(row.get("knowledge", []), f"{label}.knowledge")):
        item = _mapping(value, f"{label}.knowledge[{i}]")
        _keys(item, {"kind", "statement"}, {"kind", "statement"}, f"{label}.knowledge[{i}]")
        knowledge.append(CharacterKnowledge(_text(item["kind"], f"{label}.knowledge[{i}].kind"), _text(item["statement"], f"{label}.knowledge[{i}].statement")))
    return Character(
        id=_string(row["id"], f"{label}.id"), full_name=_title(row["full_name"], f"{label}.full_name"),
        display_name=_text(row.get("display_name", ""), f"{label}.display_name"), aliases=_text_list(row.get("aliases", []), f"{label}.aliases"),
        role=_text(row.get("role", "supporting character"), f"{label}.role"), description=_text(row.get("description", ""), f"{label}.description"),
        background=_text_map(row.get("background", {}), f"{label}.background", CHARACTER_BACKGROUND_FIELDS),
        personality=_text_list_map(row.get("personality", {}), f"{label}.personality", CHARACTER_PERSONALITY_FIELDS),
        primary_motivation=_text(row.get("primary_motivation", ""), f"{label}.primary_motivation"), secondary_motivations=_text_list(row.get("secondary_motivations", []), f"{label}.secondary_motivations"),
        goals=goals, desires=_text_list(row.get("desires", []), f"{label}.desires"), needs=_text_list(row.get("needs", []), f"{label}.needs"), obstacles=_text_list(row.get("obstacles", []), f"{label}.obstacles"), accepted_risks=_text_list(row.get("accepted_risks", []), f"{label}.accepted_risks"), refusals=_text_list(row.get("refusals", []), f"{label}.refusals"), internal_conflicts=_text_list(row.get("internal_conflicts", []), f"{label}.internal_conflicts"), knowledge=knowledge,
        arc=_text_map(row.get("arc", {}), f"{label}.arc", CHARACTER_ARC_FIELDS),
    )


def _character_relationship(value: object, label: str) -> CharacterRelationship:
    row = _mapping(value, label)
    fields = {"id", "source_id", "target_id", "relationship_type", "description", "attitude", "trust", "status", "history", "shared_secrets", "development_notes"}
    _keys(row, {"id", "source_id", "target_id"}, fields, label)
    return CharacterRelationship(**{key: row.get(key, default) for key, default in {
        "id": None, "source_id": None, "target_id": None, "relationship_type": "unknown", "description": "", "attitude": "", "trust": None, "status": "active", "history": "", "shared_secrets": "", "development_notes": ""}.items()})


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or "\x00" in value:
        raise ProjectFormatError(f"{label} must be text")
    return value


def _text_list(value: object, label: str) -> list[str]:
    return [_text(item, f"{label}[{i}]") for i, item in enumerate(_list(value, label))]


def _text_map(value: object, label: str, allowed: frozenset[str]) -> dict[str, str]:
    row = _mapping(value, label)
    if row.keys() - allowed:
        raise ProjectFormatError(f"{label} has unknown fields: {', '.join(sorted(row.keys() - allowed))}")
    return {key: _text(item, f"{label}.{key}") for key, item in row.items()}


def _text_list_map(value: object, label: str, allowed: frozenset[str]) -> dict[str, list[str]]:
    row = _mapping(value, label)
    if row.keys() - allowed:
        raise ProjectFormatError(f"{label} has unknown fields: {', '.join(sorted(row.keys() - allowed))}")
    return {key: _text_list(item, f"{label}.{key}") for key, item in row.items()}


def _validate_character(character: Character, label: str) -> None:
    _uuid(character.id, f"{label}.id")
    _title(character.full_name, f"{label}.full_name")
    for attr in ("display_name", "role", "description", "primary_motivation"):
        _text(getattr(character, attr), f"{label}.{attr}")
    for attr in ("aliases", "secondary_motivations", "desires", "needs", "obstacles", "accepted_risks", "refusals", "internal_conflicts"):
        _text_list(getattr(character, attr), f"{label}.{attr}")
    _text_map(character.background, f"{label}.background", CHARACTER_BACKGROUND_FIELDS)
    _text_list_map(character.personality, f"{label}.personality", CHARACTER_PERSONALITY_FIELDS)
    _text_map(character.arc, f"{label}.arc", CHARACTER_ARC_FIELDS)
    for goal in character.goals:
        if (not isinstance(goal, CharacterGoal) or not isinstance(goal.description, str)
                or not goal.description.strip() or not isinstance(goal.status, str)
                or goal.status not in CHARACTER_GOAL_STATES or type(goal.priority) is not int
                or not 1 <= goal.priority <= 5 or not isinstance(goal.notes, str)):
            raise ProjectFormatError(f"{label} contains an invalid goal")
    for item in character.knowledge:
        if (not isinstance(item, CharacterKnowledge) or not isinstance(item.kind, str)
                or item.kind not in CHARACTER_KNOWLEDGE_KINDS
                or not isinstance(item.statement, str) or not item.statement.strip()):
            raise ProjectFormatError(f"{label} contains invalid knowledge")


def _validate_character_relationship(item: CharacterRelationship, label: str) -> None:
    _uuid(item.id, f"{label}.id")
    _uuid(item.source_id, f"{label}.source_id")
    _uuid(item.target_id, f"{label}.target_id")
    for attr in ("relationship_type", "description", "attitude", "status", "history", "shared_secrets", "development_notes"):
        _text(getattr(item, attr), f"{label}.{attr}")
    if item.trust is not None and (type(item.trust) is not int or not 0 <= item.trust <= 100):
        raise ProjectFormatError(f"{label}.trust must be from 0 to 100")


def _validate_scene_associations(scene: Scene, character_ids: set[str], label: str) -> None:
    seen = set()
    for item in scene.character_associations:
        if (not isinstance(item, SceneCharacterAssociation)
                or not isinstance(item.character_id, str) or item.character_id not in character_ids
                or not isinstance(item.presence, str) or item.presence not in CHARACTER_PRESENCE):
            raise ProjectFormatError(f"{label} has an invalid character association")
        if item.character_id in seen:
            raise ProjectFormatError(f"{label} has duplicate character associations")
        seen.add(item.character_id)
        _text(item.purpose, f"{label}.association.purpose")
        _text_list(item.relevant_goals, f"{label}.association.relevant_goals")
        _text_list(item.development_notes, f"{label}.association.development_notes")


def _character_mapping(item: Character) -> dict[str, object]:
    result = {"id": item.id, "full_name": item.full_name, "display_name": item.display_name, "aliases": item.aliases, "role": item.role, "description": item.description, "background": item.background, "personality": item.personality, "primary_motivation": item.primary_motivation, "secondary_motivations": item.secondary_motivations, "goals": [{"description": g.description, "status": g.status, "priority": g.priority, "notes": g.notes} for g in item.goals], "desires": item.desires, "needs": item.needs, "obstacles": item.obstacles, "accepted_risks": item.accepted_risks, "refusals": item.refusals, "internal_conflicts": item.internal_conflicts, "knowledge": [{"kind": k.kind, "statement": k.statement} for k in item.knowledge], "arc": item.arc}
    return result


def _character_relationship_mapping(item: CharacterRelationship) -> dict[str, object]:
    return {key: getattr(item, key) for key in ("id", "source_id", "target_id", "relationship_type", "description", "attitude", "trust", "status", "history", "shared_secrets", "development_notes") if getattr(item, key) is not None}


def _scene_mapping(scene: Scene) -> dict[str, object]:
    result: dict[str, object] = {"id": scene.id, "title": scene.title, "path": scene.path}
    if scene.character_associations:
        result["character_associations"] = [{"character_id": item.character_id, "presence": item.presence, "purpose": item.purpose, "relevant_goals": item.relevant_goals, "development_notes": item.development_notes} for item in scene.character_associations]
    return result
