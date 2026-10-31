import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QDialogButtonBox

from app.document.book_compiler import _build_document, compile_book_pdf
from app.document.export import ExportChapter, ExportScene
from app.ui.pdf_options_dialog import PdfOptionsDialog


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


def test_compile_book_pdf_creates_pages_in_project_layout(application, tmp_path: Path) -> None:
    first = ExportScene("s1", "Opening")
    second = ExportScene("s2", "The Journey")
    afterword = ExportScene("s3", "Afterword")
    target = tmp_path / "book.pdf"

    compile_book_pdf(
        target,
        "A Story",
        [
            ExportChapter("Chapter One", (first,)),
            ExportChapter("Chapter Two", (second,)),
        ],
        [afterword],
        {
            "s1": "First paragraph.\n\nA second paragraph.",
            "s2": "The next part.",
            "s3": "The end.",
        },
    )

    assert target.read_bytes().startswith(b"%PDF-")
    pdf = Path(target)
    from PySide6.QtPdf import QPdfDocument

    rendered = QPdfDocument(application)
    rendered.load(str(pdf))
    assert rendered.pageCount() >= 5
    page_text = [
        rendered.getAllText(index).text()
        for index in range(rendered.pageCount())
    ]
    assert "A Story" in page_text[0]
    assert "Contents" in page_text[1]
    assert "First paragraph." in page_text[2]
    assert "The next part." in page_text[3]
    assert "The end." in page_text[4]


def test_compile_book_colors_are_independent_of_dark_application_palette(
    application, tmp_path: Path
) -> None:
    previous_palette = application.palette()
    dark_palette = QPalette(previous_palette)
    dark_palette.setColor(QPalette.ColorRole.Text, QColor("white"))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))
    dark_palette.setColor(QPalette.ColorRole.Window, QColor("black"))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor("black"))
    application.setPalette(dark_palette)
    target = tmp_path / "dark-palette-book.pdf"
    try:
        compile_book_pdf(
            target,
            "A Story",
            [ExportChapter("Chapter One", (ExportScene("s1", "Opening"),))],
            [],
            {"s1": "Black text remains readable."},
        )

        from PySide6.QtPdf import QPdfDocument

        rendered = QPdfDocument(application)
        rendered.load(str(target))
        image = rendered.render(0, QSize(600, 850))

        assert image.pixelColor(image.width() // 2, image.height() // 2) == QColor("white")
        assert any(
            image.pixelColor(x, y).lightness() < 128
            for y in range(0, image.height(), 2)
            for x in range(0, image.width(), 2)
        )
    finally:
        application.setPalette(previous_palette)


def test_book_prose_uses_indented_left_aligned_paragraphs(application) -> None:
    document = _build_document(
        "A Story",
        [ExportChapter("Chapter One", (ExportScene("s1", "Opening"),))],
        [],
        {"s1": "First paragraph.\n\nSecond paragraph."},
    )
    body_block = document.begin()
    while body_block.isValid() and not body_block.text().startswith("First paragraph."):
        body_block = body_block.next()

    assert body_block.isValid()
    body_format = body_block.blockFormat()
    assert body_format.alignment() == Qt.AlignmentFlag.AlignLeft
    assert body_format.textIndent() > 0
    assert body_format.bottomMargin() == 0


def test_compile_book_does_not_replace_existing_destination_without_approval(
    application, tmp_path: Path
) -> None:
    target = tmp_path / "book.pdf"
    target.write_bytes(b"keep this")

    with pytest.raises(FileExistsError):
        compile_book_pdf(target, "A Story", [], [], {})

    assert target.read_bytes() == b"keep this"


def test_compile_book_rejects_missing_scene_text(application, tmp_path: Path) -> None:
    scene = ExportScene("s1", "Opening")

    with pytest.raises(ValueError, match="unavailable"):
        compile_book_pdf(
            tmp_path / "book.pdf",
            "A Story",
            [ExportChapter("Chapter One", (scene,))],
            [],
            {},
        )


@pytest.mark.parametrize("page_size, width", [("A5", 420), ("A4", 595), ("Letter", 612)])
def test_pdf_page_size_and_title_page_author(application, tmp_path, page_size, width):
    from PySide6.QtPdf import QPdfDocument

    path = tmp_path / f"{page_size}.pdf"
    compile_book_pdf(path, "Title", [], [], {}, page_size=page_size, author="Author Name")
    pdf = QPdfDocument(application)
    pdf.load(str(path))
    assert abs(pdf.pagePointSize(0).width() - width) < 3
    assert "Author Name" in pdf.getAllText(0).text()


def test_pdf_rejects_unknown_page_size_before_writing(application, tmp_path):
    target = tmp_path / "book.pdf"
    with pytest.raises(ValueError, match="page size"):
        compile_book_pdf(target, "Title", [], [], {}, page_size="unknown")
    assert not target.exists()


def test_pdf_options_require_a_title_and_default_to_a5(application):
    dialog = PdfOptionsDialog("Novel")
    ok = dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok)
    assert dialog.page_size.currentText() == "A5"
    assert dialog.scene_headings.isChecked()
    assert ok.isEnabled()
    dialog.title.setText("  ")
    assert not ok.isEnabled()
    dialog.title.setText("New title")
    assert ok.isEnabled()


def test_pdf_options_select_scenes_by_stable_id(application):
    dialog = PdfOptionsDialog("Novel", scenes=[("one", "Chapter A — Scene [one]"),
                                               ("two", "Chapter B — Scene [two]")])
    assert dialog.selected_scene_ids() == {"one", "two"}
    dialog.scenes.item(1).setCheckState(Qt.CheckState.Unchecked)
    assert dialog.selected_scene_ids() == {"one"}


def test_pdf_can_omit_scene_headings_from_contents_and_body(application, tmp_path):
    from PySide6.QtPdf import QPdfDocument

    path = tmp_path / "without-scene-headings.pdf"
    compile_book_pdf(path, "Novel", [ExportChapter("Chapter", (ExportScene("s", "Hidden scene title"),))],
                     [ExportScene("u", "Hidden ungrouped title")],
                     {"s": "Chapter prose", "u": "Ungrouped prose"}, include_scene_headings=False)
    pdf = QPdfDocument(application)
    pdf.load(str(path))
    text = "\n".join(pdf.getAllText(i).text() for i in range(pdf.pageCount()))
    assert "Hidden scene title" not in text
    assert "Hidden ungrouped title" not in text
    assert "Chapter prose" in text and "Ungrouped prose" in text
    assert "Chapter" in text


def test_failed_book_compilation_preserves_existing_destination(
    application, tmp_path: Path, monkeypatch
) -> None:
    target = tmp_path / "book.pdf"
    target.write_bytes(b"prior book")

    def fail_write(*_args) -> None:
        raise OSError("PDF write failed")

    monkeypatch.setattr("app.document.book_compiler._write_pdf", fail_write)
    with pytest.raises(OSError, match="PDF write failed"):
        compile_book_pdf(target, "A Story", [], [], {}, replace_existing=True)

    assert target.read_bytes() == b"prior book"
