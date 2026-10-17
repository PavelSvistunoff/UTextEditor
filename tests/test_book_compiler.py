import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from app.document.book_compiler import compile_book_pdf
from app.document.export import ExportChapter, ExportScene


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
