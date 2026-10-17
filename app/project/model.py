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
class Manifest:
    project_id: str
    title: str
    chapters: list[Chapter] = field(default_factory=list)
    ungrouped_scenes: list[Scene] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    format_version: int = FORMAT_VERSION

    @classmethod
    def from_mapping(cls, data: object) -> Manifest:
        root = _mapping(data, "manifest")
        _keys(
            root,
            {"format_version", "project_id", "title", "chapters",
             "ungrouped_scenes", "notes", "links"},
            {"format_version", "project_id", "title", "chapters",
             "ungrouped_scenes", "notes", "links"},
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
        return {
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
    _keys(row, {"id", "title", "path"}, {"id", "title", "path"}, label)
    return Scene(
        _string(row["id"], f"{label}.id"),
        _title(row["title"], f"{label}.title"),
        _string(row["path"], f"{label}.path"),
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


def _scene_mapping(scene: Scene) -> dict[str, str]:
    return {"id": scene.id, "title": scene.title, "path": scene.path}
