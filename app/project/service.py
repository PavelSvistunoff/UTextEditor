"""Filesystem-backed project operations, independent of the Qt interface."""

from __future__ import annotations

import os
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

from .model import (
    FORMAT_VERSION,
    MANIFEST_NAME,
    NOTE_TYPES,
    Chapter,
    Link,
    Manifest,
    Note,
    ProjectError,
    ProjectFormatError,
    ProjectPathError,
    Scene,
)
from .paths import validate_project_path

_WORD = re.compile(r"(?u)[^\W_]+(?:['’‐‑‒–—-][^\W_]+)*")


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: _UniqueKeyLoader, node: MappingNode, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConstructorError("while constructing a mapping", node.start_mark,
                                   "found an unhashable key", key_node.start_mark) from exc
        if duplicate:
            raise ConstructorError("while constructing a mapping", node.start_mark,
                                   f"found duplicate key {key!r}", key_node.start_mark)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


@dataclass(frozen=True)
class WordCount:
    """A partial count is explicitly marked incomplete when files are missing."""

    count: int
    complete: bool


def count_words(text: str) -> int:
    """Count non-empty Unicode letter/digit runs with internal apostrophes/hyphens."""
    return len(_WORD.findall(text))


class Project:
    """A validated project and its on-disk manifest.

    Mutating methods persist organization metadata immediately. Manuscript and
    note text is always stored in ordinary UTF-8 files separate from YAML.
    """

    def __init__(self, root: Path, manifest: Manifest):
        self.root = root.resolve()
        self.manifest = manifest

    @classmethod
    def create(cls, root: Path | str, title: str) -> Project:
        """Create a project only in a new or empty directory, rolling back on error."""
        project_root = Path(root).expanduser()
        if project_root.exists() and not project_root.is_dir():
            raise ProjectError(f"Project location is not a directory: {project_root}")
        existed = project_root.exists()
        if existed and any(project_root.iterdir()):
            raise ProjectError("Project can only be created in a new or empty directory")
        try:
            project_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ProjectError(f"Cannot create project directory: {exc}") from exc
        project_root = project_root.resolve()
        manifest_path = project_root / MANIFEST_NAME
        if manifest_path.exists() or manifest_path.is_symlink():
            raise ProjectError(f"Project manifest already exists: {manifest_path}")
        created: list[Path] = []
        manifest = Manifest(project_id=str(uuid4()), title=title)
        try:
            for directory in (project_root / "manuscript", project_root / "notes"):
                directory.mkdir()
                created.append(directory)
            project = cls(project_root, manifest)
            project._write_manifest()
            created.append(manifest_path)
            return project
        except Exception:
            for path in reversed(created):
                try:
                    if path.is_dir() and not path.is_symlink():
                        path.rmdir()
                    else:
                        path.unlink(missing_ok=True)
                except OSError:
                    pass
            if not existed:
                try:
                    project_root.rmdir()
                except OSError:
                    pass
            raise

    @classmethod
    def open(cls, root: Path | str) -> Project:
        """Validate a project manifest and its referenced paths without rewriting it."""
        project_root = Path(root).expanduser().resolve()
        if not project_root.is_dir():
            raise ProjectError(f"Project directory does not exist: {project_root}")
        manifest_path = validate_project_path(project_root, MANIFEST_NAME)
        if not manifest_path.is_file():
            raise ProjectError(f"Project manifest is missing: {manifest_path}")
        if (project_root / MANIFEST_NAME).is_symlink():
            raise ProjectPathError("Project manifest must not be a symbolic link")
        try:
            raw = manifest_path.read_text(encoding="utf-8")
        except UnicodeError as exc:
            raise ProjectFormatError("Project manifest is not valid UTF-8") from exc
        except OSError as exc:
            raise ProjectError(f"Cannot read project manifest: {exc}") from exc
        try:
            data = yaml.load(raw, Loader=_UniqueKeyLoader)
        except yaml.YAMLError as exc:
            raise ProjectFormatError(f"Malformed project manifest: {exc}") from exc
        manifest = Manifest.from_mapping(data)
        project = cls(project_root, manifest)
        project._validate_manifest_paths()
        return project

    @property
    def manifest_path(self) -> Path:
        return self.root / MANIFEST_NAME

    def save(self) -> None:
        self._write_manifest()

    def add_chapter(self, title: str, index: int | None = None) -> Chapter:
        chapter = Chapter(id=str(uuid4()), title=title)

        def change() -> None:
            self.manifest.chapters.insert(_index(index, len(self.manifest.chapters)), chapter)

        self._update(change)
        return chapter

    def add_outline(
        self, outline: tuple[tuple[str, tuple[str, ...]], ...]
    ) -> tuple[Chapter, ...]:
        """Atomically add an author-approved chapter/scene outline."""
        if not outline:
            raise ProjectError("An outline must contain at least one chapter.")

        new_chapters: list[Chapter] = []
        reserved_paths = {
            entry.path for entry in (*tuple(self.iter_scenes()), *self.manifest.notes)
        }
        created_paths: list[Path] = []
        for chapter_title, scene_titles in outline:
            _validate_title(chapter_title)
            chapter = Chapter(id=str(uuid4()), title=chapter_title)
            for scene_title in scene_titles:
                _validate_title(scene_title)
                relative_path = self._unique_new_path(scene_title, reserved_paths)
                reserved_paths.add(relative_path)
                chapter.scenes.append(
                    Scene(id=str(uuid4()), title=scene_title, path=relative_path)
                )
            new_chapters.append(chapter)

        original_manifest = self.manifest
        candidate = deepcopy(original_manifest)
        candidate.chapters.extend(new_chapters)
        candidate.validate()

        try:
            for chapter in new_chapters:
                for scene in chapter.scenes:
                    target = validate_project_path(self.root, scene.path)
                    try:
                        with target.open("x", encoding="utf-8", newline="") as stream:
                            created_paths.append(target)
                            stream.flush()
                            os.fsync(stream.fileno())
                    except FileExistsError as exc:
                        raise ProjectError(
                            f"Refusing to overwrite existing file: {scene.path}"
                        ) from exc
                    except OSError as exc:
                        raise ProjectError(
                            f"Cannot create project text file {scene.path!r}: {exc}"
                        ) from exc
            self.manifest = candidate
            self._write_manifest()
        except Exception as exc:
            self.manifest = original_manifest
            cleanup_failures: list[str] = []
            for path in reversed(created_paths):
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    cleanup_failures.append(str(path.relative_to(self.root)))
            if cleanup_failures:
                raise ProjectError(
                    f"Could not finish adding the outline ({exc}); these empty files "
                    f"remain unreferenced: {', '.join(cleanup_failures)}"
                ) from exc
            raise
        return tuple(new_chapters)

    def rename_chapter(self, chapter_id: str, title: str) -> None:
        chapter = self._chapter(chapter_id)
        self._update(lambda: setattr(chapter, "title", title))

    def reorder_chapter(self, chapter_id: str, index: int) -> None:
        chapter = self._chapter(chapter_id)

        def change() -> None:
            self.manifest.chapters.remove(chapter)
            self.manifest.chapters.insert(_index(index, len(self.manifest.chapters)), chapter)

        self._update(change)

    def remove_chapter(
        self,
        chapter_id: str,
        *,
        move_scenes_to: str | None = None,
        move_to_ungrouped: bool = False,
    ) -> None:
        """Remove an empty chapter or explicitly move its scenes before removal.

        A non-empty chapter requires exactly one explicit destination.
        """
        chapter = self._chapter(chapter_id)
        if move_to_ungrouped and move_scenes_to is not None:
            raise ProjectError("Choose either a destination chapter or the ungrouped list")
        if chapter.scenes and move_scenes_to is None and not move_to_ungrouped:
            raise ProjectError(
                "Chapter contains scenes; choose a destination chapter or the ungrouped list"
            )
        destination = (
            self.manifest.ungrouped_scenes
            if move_to_ungrouped
            else self._chapter(move_scenes_to).scenes
            if move_scenes_to is not None
            else []
        )
        if move_scenes_to == chapter_id:
            raise ProjectError("A chapter cannot be its own removal destination")

        def change() -> None:
            destination.extend(chapter.scenes)
            chapter.scenes.clear()
            self.manifest.chapters.remove(chapter)

        self._update(change)

    def add_scene(
        self,
        title: str,
        *,
        chapter_id: str | None = None,
        index: int | None = None,
        content: str = "",
    ) -> Scene:
        scene = Scene(id=str(uuid4()), title=title, path=self._new_path(title, "manuscript"))
        self._create_text_entry(
            scene, content, lambda: self._scene_list(chapter_id).insert(
                _index(index, len(self._scene_list(chapter_id))), scene
            )
        )
        return scene

    def import_scene(
        self,
        source_path: str,
        *,
        title: str | None = None,
        chapter_id: str | None = None,
        index: int | None = None,
    ) -> Scene:
        source = validate_project_path(self.root, source_path)
        if (self.root / source_path).is_symlink():
            raise ProjectPathError("Import through a symbolic link is not allowed")
        if not source.is_file():
            raise ProjectError(f"Import source is not a file: {source_path}")
        if any(scene.path == source_path for scene in self.iter_scenes()):
            raise ProjectError("That file is already included as a scene")
        try:
            content = source.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProjectError("Imported scene is not valid UTF-8 text") from exc
        except OSError as exc:
            raise ProjectError(f"Cannot read imported scene: {exc}") from exc
        if "\x00" in content:
            raise ProjectError("Imported file appears to be binary (contains NUL bytes)")
        scene = Scene(
            id=str(uuid4()),
            title=title if title is not None else source.stem,
            path=self._new_path(title if title is not None else source.stem, "manuscript"),
        )
        self._create_text_entry(
            scene,
            content,
            lambda: self._scene_list(chapter_id).insert(
                _index(index, len(self._scene_list(chapter_id))), scene
            ),
        )
        return scene

    def import_external_scene(
        self,
        source_path: Path | str,
        *,
        confirmed: bool = False,
        title: str | None = None,
        chapter_id: str | None = None,
        index: int | None = None,
    ) -> Scene:
        """Copy a UTF-8 text file from outside the project after explicit confirmation."""
        if not confirmed:
            raise ProjectError("Importing an external file requires explicit confirmation")
        source = Path(source_path).expanduser()
        if source.is_symlink() or not source.is_file():
            raise ProjectError("External import source must be a regular, non-symlink file")
        try:
            content = source.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProjectError("Imported scene is not valid UTF-8 text") from exc
        except OSError as exc:
            raise ProjectError(f"Cannot read imported scene: {exc}") from exc
        if "\x00" in content:
            raise ProjectError("Imported file appears to be binary (contains NUL bytes)")
        scene_title = title if title is not None else source.stem
        scene = Scene(
            id=str(uuid4()),
            title=scene_title,
            path=self._new_path(scene_title, "manuscript"),
        )
        self._create_text_entry(
            scene,
            content,
            lambda: self._scene_list(chapter_id).insert(
                _index(index, len(self._scene_list(chapter_id))), scene
            ),
        )
        return scene

    def duplicate_scene(
        self,
        scene_id: str,
        *,
        chapter_id: str | None = None,
        index: int | None = None,
        title: str | None = None,
    ) -> Scene:
        original = self.get_scene(scene_id)
        content = self.read_scene(scene_id)
        copy_title = title if title is not None else f"{original.title} copy"
        duplicate = Scene(
            id=str(uuid4()),
            title=copy_title,
            path=self._new_path(copy_title, "manuscript"),
        )
        self._create_text_entry(
            duplicate,
            content,
            lambda: self._scene_list(chapter_id).insert(
                _index(index, len(self._scene_list(chapter_id))), duplicate
            ),
        )
        return duplicate

    def move_scene(
        self, scene_id: str, *, chapter_id: str | None, index: int | None = None
    ) -> None:
        scene = self.get_scene(scene_id)

        def change() -> None:
            old_list = self._scene_list_containing(scene)
            old_list.remove(scene)
            new_list = self._scene_list(chapter_id)
            new_list.insert(_index(index, len(new_list)), scene)

        self._update(change)

    def reorder_scene(self, scene_id: str, index: int) -> None:
        scene = self.get_scene(scene_id)

        def change() -> None:
            items = self._scene_list_containing(scene)
            items.remove(scene)
            items.insert(_index(index, len(items)), scene)

        self._update(change)

    def rename_scene(self, scene_id: str, title: str, *, rename_file: bool = False) -> None:
        scene = self.get_scene(scene_id)
        if not rename_file:
            self._update(lambda: setattr(scene, "title", title))
            return
        target_relative = self._new_path(title, "manuscript", excluding=scene.path)
        self._rename_entry_file(scene, target_relative, title)

    def relink_scene(self, scene_id: str, path: str) -> None:
        self._relink_entry(self.get_scene(scene_id), path)

    def recreate_scene(self, scene_id: str, *, confirmed: bool = False) -> None:
        self._recreate_entry(self.get_scene(scene_id), confirmed=confirmed)

    def remove_scene(
        self,
        scene_id: str,
        *,
        delete_file: bool = False,
        remove_links: bool = False,
        keep_orphan_links: bool = False,
    ) -> None:
        scene = self.get_scene(scene_id)
        incoming = self.links_to(scene_id)
        if incoming and not (remove_links or keep_orphan_links):
            raise ProjectError(
                f"Scene has {len(incoming)} note link(s); explicitly remove or preserve them"
            )
        self._remove_entry(
            scene,
            self._scene_list_containing(scene),
            delete_file=delete_file,
            retained_links=incoming if keep_orphan_links and not remove_links else (),
        )

    def add_note(
        self, title: str, note_type: str = "general", *, content: str = ""
    ) -> Note:
        if note_type not in NOTE_TYPES:
            raise ProjectFormatError(f"Unsupported note type: {note_type!r}")
        note = Note(
            id=str(uuid4()), type=note_type, title=title, path=self._new_path(title, "notes")
        )
        self._create_text_entry(note, content, lambda: self.manifest.notes.append(note))
        return note

    def rename_note(self, note_id: str, title: str, *, rename_file: bool = False) -> None:
        note = self.get_note(note_id)
        if not rename_file:
            self._update(lambda: setattr(note, "title", title))
            return
        target_relative = self._new_path(title, "notes", excluding=note.path)
        self._rename_entry_file(note, target_relative, title)

    def relink_note(self, note_id: str, path: str) -> None:
        self._relink_entry(self.get_note(note_id), path)

    def recreate_note(self, note_id: str, *, confirmed: bool = False) -> None:
        self._recreate_entry(self.get_note(note_id), confirmed=confirmed)

    def retype_note(self, note_id: str, note_type: str) -> None:
        if note_type not in NOTE_TYPES:
            raise ProjectFormatError(f"Unsupported note type: {note_type!r}")
        note = self.get_note(note_id)
        self._update(lambda: setattr(note, "type", note_type))

    def duplicate_note(self, note_id: str, *, copy_links: bool = False) -> Note:
        original = self.get_note(note_id)
        content = self.read_note(note_id)
        duplicate = Note(
            id=str(uuid4()),
            type=original.type,
            title=f"{original.title} copy",
            path=self._new_path(f"{original.title} copy", "notes"),
        )

        def change() -> None:
            self.manifest.notes.append(duplicate)
            if copy_links:
                self.manifest.links.extend(
                    Link(duplicate.id, link.target_id)
                    for link in self.manifest.links
                    if link.source_id == note_id
                )

        self._create_text_entry(duplicate, content, change)
        return duplicate

    def remove_note(
        self,
        note_id: str,
        *,
        delete_file: bool = False,
        remove_links: bool = False,
        keep_orphan_links: bool = False,
    ) -> None:
        note = self.get_note(note_id)
        affected = [link for link in self.manifest.links if note_id in (link.source_id, link.target_id)]
        incoming = [link for link in affected if link.target_id == note_id]
        if affected and not (remove_links or keep_orphan_links):
            raise ProjectError(
                f"Note has {len(affected)} link(s); explicitly remove or preserve incoming links"
            )
        self._remove_entry(
            note,
            self.manifest.notes,
            delete_file=delete_file,
            retained_links=incoming if keep_orphan_links and not remove_links else (),
        )

    def link_note(self, note_id: str, target_id: str) -> Link:
        self.get_note(note_id)
        if target_id not in {scene.id for scene in self.iter_scenes()} | {
            note.id for note in self.manifest.notes
        }:
            raise ProjectError(f"Unknown link target: {target_id}")
        link = Link(note_id, target_id)
        if link in self.manifest.links:
            raise ProjectError("That note link already exists")
        self._update(lambda: self.manifest.links.append(link))
        return link

    def unlink_note(self, note_id: str, target_id: str) -> None:
        link = Link(note_id, target_id)
        if link not in self.manifest.links:
            raise ProjectError("That note link does not exist")
        self._update(lambda: self.manifest.links.remove(link))

    def links_from(self, item_id: str) -> tuple[Link, ...]:
        return tuple(link for link in self.manifest.links if link.source_id == item_id)

    def links_to(self, item_id: str) -> tuple[Link, ...]:
        return tuple(link for link in self.manifest.links if link.target_id == item_id)

    def iter_scenes(self):
        for chapter in self.manifest.chapters:
            yield from chapter.scenes
        yield from self.manifest.ungrouped_scenes

    def get_scene(self, scene_id: str) -> Scene:
        for scene in self.iter_scenes():
            if scene.id == scene_id:
                return scene
        raise ProjectError(f"Unknown scene ID: {scene_id}")

    def get_note(self, note_id: str) -> Note:
        for note in self.manifest.notes:
            if note.id == note_id:
                return note
        raise ProjectError(f"Unknown note ID: {note_id}")

    def read_scene(self, scene_id: str) -> str:
        return self._read_text(self.get_scene(scene_id).path)

    def read_note(self, note_id: str) -> str:
        return self._read_text(self.get_note(note_id).path)

    def write_scene(self, scene_id: str, content: str, *, expected_content: str) -> None:
        """Atomically save a scene only if disk still matches the caller's snapshot."""
        self._write_text(
            self.get_scene(scene_id).path, content, expected_content=expected_content
        )

    def write_note(self, note_id: str, content: str, *, expected_content: str) -> None:
        """Atomically save a note only if disk still matches the caller's snapshot."""
        self._write_text(
            self.get_note(note_id).path, content, expected_content=expected_content
        )

    def scene_word_count(self, scene_id: str) -> WordCount:
        return self._word_count((self.get_scene(scene_id),))

    def chapter_word_count(self, chapter_id: str) -> WordCount:
        chapter = self._chapter(chapter_id)
        return self._word_count(chapter.scenes)

    def project_word_count(self) -> WordCount:
        return self._word_count(tuple(self.iter_scenes()))

    def _word_count(self, scenes) -> WordCount:
        total = 0
        complete = True
        for scene in scenes:
            try:
                total += count_words(self._read_text(scene.path))
            except (OSError, UnicodeError, ProjectError):
                complete = False
        return WordCount(total, complete)

    def _read_text(self, relative_path: str) -> str:
        path = validate_project_path(self.root, relative_path)
        try:
            content = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProjectError(f"Referenced file is not valid UTF-8 text: {relative_path}") from exc
        except OSError as exc:
            raise ProjectError(f"Cannot read referenced file {relative_path!r}: {exc}") from exc
        if "\x00" in content:
            raise ProjectError(f"Referenced file appears to be binary: {relative_path}")
        return content

    def _write_text(
        self, relative_path: str, content: str, *, expected_content: str
    ) -> None:
        if not isinstance(content, str) or "\x00" in content:
            raise ProjectError("Text content must be ordinary UTF-8 text without NUL characters")
        if not isinstance(expected_content, str):
            raise ProjectError("An on-disk text snapshot is required before saving")
        target = validate_project_path(self.root, relative_path)
        lexical_target = self.root / relative_path
        if lexical_target.is_symlink():
            raise ProjectPathError("Saving through a symbolic link is not supported")
        try:
            current = target.read_bytes().decode("utf-8")
        except (OSError, UnicodeError) as exc:
            raise ProjectError(f"Cannot verify the current file before saving: {exc}") from exc
        if "\x00" in current:
            raise ProjectError("Referenced file appears to be binary")
        if current != expected_content:
            raise ProjectError(
                f"File changed on disk since it was read: {relative_path}; reload or compare first"
            )
        temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("x", encoding="utf-8", newline="") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            try:
                directory_fd = os.open(target.parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                pass
        except OSError as exc:
            raise ProjectError(f"Cannot atomically save project text file: {exc}") from exc
        finally:
            temporary.unlink(missing_ok=True)

    def _relink_entry(self, entry, relative_path: str) -> None:
        target = validate_project_path(self.root, relative_path)
        lexical_target = self.root / relative_path
        if lexical_target.is_symlink():
            raise ProjectPathError("Relinking through a symbolic link is not supported")
        if not target.is_file():
            raise ProjectError(f"Relink target is not a regular file: {relative_path}")
        try:
            content = target.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProjectError("Relink target is not valid UTF-8 text") from exc
        except OSError as exc:
            raise ProjectError(f"Cannot read relink target: {exc}") from exc
        if "\x00" in content:
            raise ProjectError("Relink target appears to be binary (contains NUL bytes)")
        old_path = entry.path
        self._update(lambda: setattr(entry, "path", relative_path))
        if entry.path == old_path:
            return

    def _recreate_entry(self, entry, *, confirmed: bool) -> None:
        if not confirmed:
            raise ProjectError("Recreating a missing project file requires explicit confirmation")
        target = validate_project_path(self.root, entry.path)
        lexical_target = self.root / entry.path
        if lexical_target.is_symlink():
            raise ProjectPathError("Cannot recreate a symbolic-link entry")
        if target.exists():
            raise ProjectError(f"Refusing to overwrite existing file: {entry.path}")
        if not target.parent.is_dir():
            raise ProjectError(f"Cannot recreate file because its directory is missing: {entry.path}")
        try:
            with target.open("x", encoding="utf-8", newline="") as stream:
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise ProjectError(f"Refusing to overwrite existing file: {entry.path}") from exc
        except OSError as exc:
            raise ProjectError(f"Cannot recreate project file {entry.path!r}: {exc}") from exc

    def _chapter(self, chapter_id: str) -> Chapter:
        for chapter in self.manifest.chapters:
            if chapter.id == chapter_id:
                return chapter
        raise ProjectError(f"Unknown chapter ID: {chapter_id}")

    def _scene_list(self, chapter_id: str | None) -> list[Scene]:
        return self.manifest.ungrouped_scenes if chapter_id is None else self._chapter(chapter_id).scenes

    def _scene_list_containing(self, scene: Scene) -> list[Scene]:
        for chapter in self.manifest.chapters:
            if scene in chapter.scenes:
                return chapter.scenes
        if scene in self.manifest.ungrouped_scenes:
            return self.manifest.ungrouped_scenes
        raise ProjectError(f"Scene is not in the project: {scene.id}")

    def _new_path(self, title: str, folder: str, *, excluding: str | None = None) -> str:
        _validate_title(title)
        slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-") or "untitled"
        existing = {
            entry.path
            for entry in (*tuple(self.iter_scenes()), *self.manifest.notes)
            if entry.path != excluding
        }
        candidate = f"{folder}/{slug}.txt"
        suffix = 2
        while candidate in existing or validate_project_path(self.root, candidate).exists():
            candidate = f"{folder}/{slug}-{suffix}.txt"
            suffix += 1
        return candidate

    def _unique_new_path(self, title: str, reserved_paths: set[str]) -> str:
        _validate_title(title)
        slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-") or "untitled"
        base = f"manuscript/{slug}.txt"
        candidate = base
        suffix = 2
        while candidate in reserved_paths or validate_project_path(self.root, candidate).exists():
            candidate = f"manuscript/{slug}-{suffix}.txt"
            suffix += 1
        return candidate

    def _create_text_entry(self, entry, content: str, add_to_manifest) -> None:
        _validate_title(entry.title)
        if not isinstance(content, str) or "\x00" in content:
            raise ProjectError("Text content must be ordinary UTF-8 text without NUL characters")
        path = validate_project_path(self.root, entry.path)
        try:
            with path.open("x", encoding="utf-8", newline="") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise ProjectError(f"Refusing to overwrite existing file: {entry.path}") from exc
        except OSError as exc:
            raise ProjectError(f"Cannot create project text file {entry.path!r}: {exc}") from exc
        try:
            self._update(add_to_manifest)
        except Exception:
            try:
                path.unlink(missing_ok=True)
            except OSError as rollback_error:
                raise ProjectError(
                    f"Manifest update failed and new file remains at {entry.path!r}: "
                    f"{rollback_error}"
                )
            raise

    def _rename_entry_file(self, entry, target_relative: str, new_title: str) -> None:
        source = validate_project_path(self.root, entry.path)
        target = validate_project_path(self.root, target_relative)
        source_lexical = self.root / entry.path
        if source_lexical.is_symlink():
            raise ProjectPathError("Renaming a symbolic-link entry is not supported")
        if not source.is_file():
            raise ProjectError(f"Referenced file is missing or unavailable: {entry.path}")
        if target.exists():
            raise ProjectError(f"Refusing to overwrite existing file: {target_relative}")
        old_path, old_title = entry.path, entry.title
        try:
            source_lexical.rename(target)
        except OSError as exc:
            raise ProjectError(f"Cannot rename project file: {exc}") from exc
        try:
            self._update(lambda: (setattr(entry, "path", target_relative), setattr(entry, "title", new_title)))
        except Exception:
            try:
                target.rename(source_lexical)
            except OSError as rollback_error:
                raise ProjectError(
                    f"Manifest update failed and file rollback failed; file remains at "
                    f"{target_relative!r}: {rollback_error}"
                )
            entry.path, entry.title = old_path, old_title
            raise

    def _remove_entry(
        self, entry, collection: list, *, delete_file: bool, retained_links=()
    ) -> None:
        staged: Path | None = None
        source = self.root / entry.path
        validate_project_path(self.root, entry.path)
        if delete_file and source.exists():
            if source.is_symlink():
                raise ProjectPathError("Deleting a symbolic-link entry is not supported")
            if not source.is_file():
                raise ProjectError(f"Referenced path is not a regular file: {entry.path}")
            staged = source.with_name(f".{source.name}.remove-{uuid4().hex}")
            try:
                source.rename(staged)
            except OSError as exc:
                raise ProjectError(f"Cannot stage file for removal: {exc}") from exc
        links = list(self.manifest.links)
        try:
            def change() -> None:
                collection.remove(entry)
                self.manifest.links = [
                    link
                    for link in self.manifest.links
                    if link.source_id != entry.id
                    and (link.target_id != entry.id or link in retained_links)
                ]

            self._update(change)
        except Exception:
            if staged is not None:
                try:
                    staged.rename(source)
                except OSError as rollback_error:
                    raise ProjectError(
                        f"Manifest update failed and original file remains staged at "
                        f"{staged.name!r}: {rollback_error}"
                    )
            self.manifest.links = links
            raise
        if staged is not None:
            try:
                staged.unlink()
            except OSError as exc:
                raise ProjectError(
                    f"Project entry was removed, but its file could not be deleted and "
                    f"remains at {staged.name!r}: {exc}"
                ) from exc

    def _update(self, change) -> None:
        before = deepcopy(self.manifest)
        try:
            change()
            self._write_manifest()
        except Exception:
            self.manifest = before
            raise

    def _validate_manifest_paths(self) -> None:
        validate_project_path(self.root, MANIFEST_NAME)
        if (self.root / MANIFEST_NAME).is_symlink():
            raise ProjectPathError("Project manifest must not be a symbolic link")
        resolved_paths: dict[Path, str] = {}
        for entry in (*tuple(self.iter_scenes()), *self.manifest.notes):
            path = validate_project_path(self.root, entry.path)
            previous = resolved_paths.get(path)
            if previous is not None:
                raise ProjectFormatError(
                    f"Entries {previous!r} and {entry.path!r} resolve to the same file"
                )
            resolved_paths[path] = entry.path
            if path.exists() and not path.is_file():
                raise ProjectFormatError(f"Referenced path is not a regular file: {entry.path}")

    def _write_manifest(self) -> None:
        self.manifest.validate()
        self._validate_manifest_paths()
        destination = validate_project_path(self.root, MANIFEST_NAME)
        if destination.is_symlink():
            raise ProjectPathError("Project manifest must not be a symbolic link")
        encoded = yaml.safe_dump(
            self.manifest.to_mapping(),
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ).encode("utf-8")
        temporary = self.root / f".{MANIFEST_NAME}.{uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
            try:
                directory_fd = os.open(self.root, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                pass
        except OSError as exc:
            raise ProjectError(f"Cannot atomically write project manifest: {exc}") from exc
        finally:
            temporary.unlink(missing_ok=True)


def _index(index: int | None, length: int) -> int:
    value = length if index is None else index
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > length:
        raise ProjectError(f"Index must be between 0 and {length}")
    return value


def _validate_title(title: object) -> None:
    if (
        not isinstance(title, str)
        or not title.strip()
        or "\x00" in title
        or any(ord(char) < 32 for char in title)
    ):
        raise ProjectFormatError("Title must contain visible text without control characters")
