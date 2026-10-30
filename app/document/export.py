"""Deterministic, non-destructive plain-text and Markdown manuscript export."""

from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

from .encoding import normalize_line_endings


@dataclass(frozen=True)
class ExportScene:
    scene_id: str
    title: str


@dataclass(frozen=True)
class ExportChapter:
    title: str
    scenes: tuple[ExportScene, ...]


def render_manuscript(
    chapters: Sequence[ExportChapter],
    ungrouped_scenes: Sequence[ExportScene],
    scene_texts: Mapping[str, str],
    *,
    format: str = "markdown",
    selected_scene_ids: set[str] | None = None,
    include_chapter_headings: bool = True,
    include_scene_headings: bool = True,
    separator: str = "\n\n",
) -> str:
    """Render one captured manuscript state; notes are never included implicitly."""
    if format not in {"markdown", "text"}:
        raise ValueError("Export format must be 'markdown' or 'text'.")
    if not isinstance(separator, str):
        raise TypeError("Export separator must be text.")
    seen: set[str] = set()
    for chapter in chapters:
        for scene in chapter.scenes:
            _add_unique_scene(seen, scene)
    for scene in ungrouped_scenes:
        _add_unique_scene(seen, scene)

    if selected_scene_ids is not None:
        unknown = selected_scene_ids - seen
        if unknown:
            raise ValueError(f"Selected scene IDs are not in the manuscript: {', '.join(sorted(unknown))}")
    if format == "markdown":
        chapter_prefix, scene_prefix = "# ", "## "
    else:
        chapter_prefix = scene_prefix = ""

    blocks: list[str] = []
    for chapter in chapters:
        selected = [
            scene for scene in chapter.scenes
            if selected_scene_ids is None or scene.scene_id in selected_scene_ids
        ]
        if not selected and not (include_chapter_headings and not chapter.scenes):
            continue
        if include_chapter_headings:
            blocks.append(f"{chapter_prefix}{chapter.title}")
        for scene in selected:
            _append_scene_block(blocks, scene, scene_texts, scene_prefix, include_scene_headings)

    for scene in ungrouped_scenes:
        if selected_scene_ids is None or scene.scene_id in selected_scene_ids:
            _append_scene_block(blocks, scene, scene_texts, scene_prefix, include_scene_headings)
    return separator.join(blocks)


def export_manuscript(
    destination: str | Path,
    chapters: Sequence[ExportChapter],
    ungrouped_scenes: Sequence[ExportScene],
    scene_texts: Mapping[str, str],
    *,
    format: str = "markdown",
    replace_existing: bool = False,
    selected_scene_ids: set[str] | None = None,
    include_chapter_headings: bool = True,
    include_scene_headings: bool = True,
    separator: str = "\n\n",
) -> Path:
    """Atomically write UTF-8 with LF newlines; existing files need explicit approval."""
    target = Path(destination)
    if target.exists() and not replace_existing:
        raise FileExistsError(f"Export destination already exists: {target}")
    content = normalize_line_endings(render_manuscript(
        chapters,
        ungrouped_scenes,
        scene_texts,
        format=format,
        selected_scene_ids=selected_scene_ids,
        include_chapter_headings=include_chapter_headings,
        include_scene_headings=include_scene_headings,
        separator=separator,
    ))
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if target.exists() and replace_existing:
            os.chmod(temporary, target.stat().st_mode)
            os.replace(temporary, target)
        else:
            os.link(temporary, target)
            temporary.unlink()
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return target


def _add_unique_scene(
    seen: set[str],
    scene: ExportScene,
) -> None:
    if not scene.scene_id or scene.scene_id in seen:
        raise ValueError(f"Duplicate or empty scene ID in manuscript: {scene.scene_id!r}")
    seen.add(scene.scene_id)


def _append_scene_block(
    blocks: list[str],
    scene: ExportScene,
    scene_texts: Mapping[str, str],
    scene_prefix: str,
    include_heading: bool,
) -> None:
    if scene.scene_id not in scene_texts:
        raise ValueError(f"Text is unavailable for scene {scene.scene_id!r}.")
    text = scene_texts[scene.scene_id]
    if not isinstance(text, str):
        raise TypeError(f"Text for scene {scene.scene_id!r} must be a string.")
    content = f"{scene_prefix}{scene.title}\n\n{text}" if include_heading else text
    blocks.append(content)
