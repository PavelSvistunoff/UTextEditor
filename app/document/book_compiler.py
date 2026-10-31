"""Compile an ordered project manuscript into a print-ready PDF book."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

from PySide6.QtCore import QMarginsF, QRectF, QSizeF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPageLayout,
    QPageSize,
    QPainter,
    QPdfWriter,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
)

from .export import ExportChapter, ExportScene


def compile_book_pdf(
    destination: str | Path,
    title: str,
    chapters: Sequence[ExportChapter],
    ungrouped_scenes: Sequence[ExportScene],
    scene_texts: Mapping[str, str],
    *,
    replace_existing: bool = False,
    page_size: str = "A5",
    author: str = "",
    include_scene_headings: bool = True,
    include_chapter_headings: bool = True,
) -> Path:
    """Write a PDF with a title page, ordered chapters, and page numbers."""
    target = Path(destination)
    if target.exists() and not replace_existing:
        raise FileExistsError(f"Book destination already exists: {target}")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Book title must contain visible text.")
    if page_size not in {"A5", "A4", "Letter"}:
        raise ValueError("Unsupported page size.")
    if not isinstance(author, str):
        raise TypeError("Author must be text.")

    _validate_scenes(chapters, ungrouped_scenes, scene_texts)
    document = _build_document(title, chapters, ungrouped_scenes, scene_texts, author=author,
                               include_scene_headings=include_scene_headings,
                               include_chapter_headings=include_chapter_headings)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        _write_pdf(temporary, title, document, page_size)
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


def _validate_scenes(
    chapters: Sequence[ExportChapter],
    ungrouped_scenes: Sequence[ExportScene],
    scene_texts: Mapping[str, str],
) -> None:
    seen: set[str] = set()
    for chapter in chapters:
        for scene in chapter.scenes:
            _validate_scene(scene, seen, scene_texts)
    for scene in ungrouped_scenes:
        _validate_scene(scene, seen, scene_texts)


def _validate_scene(
    scene: ExportScene,
    seen: set[str],
    scene_texts: Mapping[str, str],
) -> None:
    if not scene.scene_id or scene.scene_id in seen:
        raise ValueError(f"Duplicate or empty scene ID in manuscript: {scene.scene_id!r}")
    seen.add(scene.scene_id)
    if scene.scene_id not in scene_texts:
        raise ValueError(f"Text is unavailable for scene {scene.scene_id!r}.")
    if not isinstance(scene_texts[scene.scene_id], str):
        raise TypeError(f"Text for scene {scene.scene_id!r} must be a string.")


def _build_document(
    title: str,
    chapters: Sequence[ExportChapter],
    ungrouped_scenes: Sequence[ExportScene],
    scene_texts: Mapping[str, str],
    *,
    author: str = "",
    include_scene_headings: bool = True,
    include_chapter_headings: bool = True,
) -> QTextDocument:
    document = QTextDocument()
    document.setDefaultFont(QFont("Georgia", 11))
    document.setDocumentMargin(0)
    cursor = QTextCursor(document)

    cover_format = _block_format(Qt.AlignmentFlag.AlignHCenter)
    cover_format.setTopMargin(150)
    _insert_block(cursor, title, cover_format, _char_format(25, bold=True))
    if author.strip():
        _insert_block(cursor, author.strip(), _block_format(Qt.AlignmentFlag.AlignHCenter), _char_format(14))
    _insert_block(
        cursor,
        "Compiled manuscript",
        _block_format(Qt.AlignmentFlag.AlignHCenter),
        _char_format(10),
    )

    toc_format = _block_format(Qt.AlignmentFlag.AlignHCenter)
    toc_format.setPageBreakPolicy(QTextFormat.PageBreakFlag.PageBreak_AlwaysBefore)
    _insert_block(cursor, "Contents", toc_format, _char_format(20, bold=True))
    for chapter in chapters:
        if include_chapter_headings:
            _insert_block(cursor, chapter.title, _block_format(), _char_format(12, bold=True))
        if include_scene_headings:
            for scene in chapter.scenes:
                _insert_block(cursor, scene.title, _block_format(), _char_format(10))
    if ungrouped_scenes:
        if include_chapter_headings:
            _insert_block(cursor, "Additional Scenes", _block_format(), _char_format(12, bold=True))
        if include_scene_headings:
            for scene in ungrouped_scenes:
                _insert_block(cursor, scene.title, _block_format(), _char_format(10))
    if not chapters and not ungrouped_scenes:
        _insert_block(cursor, "No scenes in this project.", _block_format(), _char_format(10))

    for chapter in chapters:
        heading_format = _block_format(Qt.AlignmentFlag.AlignHCenter)
        heading_format.setPageBreakPolicy(QTextFormat.PageBreakFlag.PageBreak_AlwaysBefore)
        heading_format.setBottomMargin(30)
        # Keep a nonprinting block to carry the page break when the title is hidden.
        _insert_block(cursor, chapter.title if include_chapter_headings else "\u200b",
                      heading_format, _char_format(20 if include_chapter_headings else 1, bold=True))
        for scene in chapter.scenes:
            _insert_scene(cursor, scene, scene_texts[scene.scene_id], include_scene_headings)

    if ungrouped_scenes:
        heading_format = _block_format(Qt.AlignmentFlag.AlignHCenter)
        heading_format.setPageBreakPolicy(QTextFormat.PageBreakFlag.PageBreak_AlwaysBefore)
        heading_format.setBottomMargin(24)
        _insert_block(cursor, "Additional Scenes" if include_chapter_headings else "\u200b",
                      heading_format, _char_format(20 if include_chapter_headings else 1, bold=True))
        for scene in ungrouped_scenes:
            _insert_scene(cursor, scene, scene_texts[scene.scene_id], include_scene_headings)
    return document


def _insert_scene(cursor: QTextCursor, scene: ExportScene, text: str, include_heading: bool) -> None:
    if include_heading:
        heading_format = _block_format(Qt.AlignmentFlag.AlignHCenter)
        heading_format.setTopMargin(12)
        heading_format.setBottomMargin(12)
        _insert_block(cursor, scene.title, heading_format, _char_format(13, bold=True))

    body_format = _block_format(Qt.AlignmentFlag.AlignLeft)
    body_format.setLineHeight(
        140, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value
    )
    # Novel prose uses indented paragraphs without blank-line spacing. Keeping
    # the text left aligned also prevents justified soft wraps from stretching
    # spaces into the printable edge on some Qt PDF backends.
    body_format.setTextIndent(18)
    body_format.setBottomMargin(0)
    body_character_format = _char_format(11)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    if not normalized:
        return
    paragraphs = normalized.split("\n\n")
    for paragraph_index, paragraph in enumerate(paragraphs):
        cursor.setBlockFormat(body_format)
        cursor.setCharFormat(body_character_format)
        lines = paragraph.split("\n")
        for line_index, line in enumerate(lines):
            cursor.insertText(line, body_character_format)
            if line_index < len(lines) - 1:
                cursor.insertText("\u2028", body_character_format)
        if paragraph_index < len(paragraphs) - 1:
            cursor.insertBlock(body_format, body_character_format)
    cursor.insertBlock(body_format, body_character_format)


def _insert_block(
    cursor: QTextCursor,
    text: str,
    block_format: QTextBlockFormat,
    character_format: QTextCharFormat,
) -> None:
    cursor.setBlockFormat(block_format)
    cursor.setCharFormat(character_format)
    cursor.insertText(text, character_format)
    cursor.insertBlock()


def _block_format(
    alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
) -> QTextBlockFormat:
    block = QTextBlockFormat()
    block.setAlignment(alignment)
    block.setBottomMargin(5)
    return block


def _char_format(size: int, *, bold: bool = False) -> QTextCharFormat:
    result = QTextCharFormat()
    weight = QFont.Weight.Bold if bold else QFont.Weight.Normal
    result.setFont(QFont("Georgia", size, weight))
    result.setForeground(QColor(Qt.GlobalColor.black))
    return result


def _write_pdf(path: Path, title: str, document: QTextDocument, page_size: str = "A5") -> None:
    writer = QPdfWriter(str(path))
    writer.setTitle(title)
    writer.setCreator("UTextEditor")
    writer.setResolution(72)
    sizes = {"A5": QPageSize.PageSizeId.A5, "A4": QPageSize.PageSizeId.A4,
             "Letter": QPageSize.PageSizeId.Letter}
    writer.setPageSize(QPageSize(sizes[page_size]))
    # Use full-page painter coordinates, then apply the book margins to the
    # document exactly once. QPdfWriter offsets painter coordinates by its
    # configured margins, so adding paintRect.x/y to that would double them.
    writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)

    margin = 18 * writer.resolution() / 25.4
    page_size = QSizeF(
        writer.width() - 2 * margin,
        writer.height() - 2 * margin,
    )
    content_rect = QRectF(margin, margin, page_size.width(), page_size.height())
    document.setPageSize(page_size)
    document.documentLayout().documentSize()
    page_count = max(1, document.pageCount())

    painter = QPainter()
    if not painter.begin(writer):
        raise OSError(f"Cannot open PDF destination for writing: {path}")
    try:
        for page_index in range(page_count):
            if page_index:
                writer.newPage()
            painter.fillRect(
                QRectF(0, 0, writer.width(), writer.height()),
                QColor(Qt.GlobalColor.white),
            )
            painter.save()
            painter.translate(
                content_rect.x(),
                content_rect.y() - page_index * content_rect.height(),
            )
            painter.setClipRect(
                QRectF(
                    0,
                    page_index * content_rect.height(),
                    page_size.width(),
                    page_size.height(),
                )
            )
            document.drawContents(
                painter,
                QRectF(
                    0,
                    page_index * content_rect.height(),
                    page_size.width(),
                    page_size.height(),
                ),
            )
            painter.restore()
            if page_index:
                painter.setPen(QColor(Qt.GlobalColor.black))
                painter.setFont(QFont("Georgia", 8))
                painter.drawText(
                    QRectF(0, writer.height() - 30, writer.width(), 12),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                    str(page_index + 1),
                )
    finally:
        painter.end()
