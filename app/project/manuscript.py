"""Captured project manuscript export operations for background workers.

Open buffers take precedence over disk; caller owns UI consent and stale-state
checks. Destination validation still happens before any source reads.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

from .service import Project
from app.document.encoding import normalize_line_endings
from app.document.export import (
    ExportChapter, ExportScene, ensure_destination_not_source, export_manuscript, render_manuscript,
    write_rendered_manuscript,
)


def project_export_sources(project: Project) -> tuple[Path, ...]:
    return (project.manifest_path, *(project.root / item.path for item in project.iter_scenes()),
            *(project.root / item.path for item in project.manifest.notes))


def export_project_snapshot(
    project: Project,
    chapters: Sequence[ExportChapter],
    ungrouped: Sequence[ExportScene],
    scene_text: Mapping[str, str],
    target: str | Path,
    format_name: str,
    replace_existing: bool,
    selected_scene_ids: set[str] | None,
    include_chapter_headings: bool,
    include_scene_headings: bool,
    separator: str,
    source_paths: tuple[Path, ...] | None = None,
    *,
    preview_only: bool = False,
) -> Path | str:
    ensure_destination_not_source(target, source_paths or project_export_sources(project))
    texts = _capture_scene_texts(project, chapters, ungrouped, scene_text, selected_scene_ids)
    if preview_only:
        return normalize_line_endings(render_manuscript(
            chapters, ungrouped, texts, format=format_name,
            selected_scene_ids=selected_scene_ids,
            include_chapter_headings=include_chapter_headings,
            include_scene_headings=include_scene_headings, separator=separator,
        ))
    return export_manuscript(
        target,
        chapters,
        ungrouped,
        texts,
        format=format_name,
        replace_existing=replace_existing,
        selected_scene_ids=selected_scene_ids,
        include_chapter_headings=include_chapter_headings,
        include_scene_headings=include_scene_headings,
        separator=separator,
    )


def compile_project_book_snapshot(
    project: Project,
    title: str,
    chapters: Sequence[ExportChapter],
    ungrouped: Sequence[ExportScene],
    open_text: Mapping[str, str],
    target: str | Path,
    replace_existing: bool,
    page_size: str = "A5",
    author: str = "",
    include_scene_headings: bool = True,
    source_paths: tuple[Path, ...] | None = None,
    include_chapter_headings: bool = True,
) -> Path:
    ensure_destination_not_source(target, source_paths or project_export_sources(project))
    texts = _capture_scene_texts(project, chapters, ungrouped, open_text)
    from app.document.book_compiler import compile_book_pdf

    return compile_book_pdf(
        target,
        title,
        chapters,
        ungrouped,
        texts,
        replace_existing=replace_existing,
        page_size=page_size,
        author=author,
        include_scene_headings=include_scene_headings,
        include_chapter_headings=include_chapter_headings,
    )


def write_reviewed_export(
    target: Path, content: str, replace_existing: bool, source_paths: tuple[Path, ...],
) -> Path:
    ensure_destination_not_source(target, source_paths)
    return write_rendered_manuscript(target, content, replace_existing=replace_existing)



def _capture_scene_texts(
    project: Project, chapters: Sequence[ExportChapter], ungrouped: Sequence[ExportScene],
    open_text: Mapping[str, str], selected_scene_ids: set[str] | None = None,
) -> dict[str, str]:
    """Read only selected captured scenes, giving unsaved buffers precedence."""
    scenes = [scene for chapter in chapters for scene in chapter.scenes]
    scenes.extend(ungrouped)
    return {
        scene.scene_id: (open_text[scene.scene_id] if scene.scene_id in open_text
                         else project.read_scene(scene.scene_id))
        for scene in scenes
        if selected_scene_ids is None or scene.scene_id in selected_scene_ids
    }
