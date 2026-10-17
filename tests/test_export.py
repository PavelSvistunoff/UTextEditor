from pathlib import Path

import pytest

from app.document.export import ExportChapter, ExportScene, export_manuscript, render_manuscript


@pytest.fixture
def manuscript():
    return (
        [ExportChapter("Chapter One", (ExportScene("s1", "Opening"), ExportScene("s2", "Empty scene")))],
        [ExportScene("s3", "Afterword")],
        {"s1": "Привіт, світ.", "s2": "", "s3": "The end."},
    )


def test_markdown_export_preserves_order_unicode_and_headings(manuscript) -> None:
    chapters, ungrouped, texts = manuscript

    rendered = render_manuscript(chapters, ungrouped, texts)

    assert rendered == "# Chapter One\n\n## Opening\n\nПривіт, світ.\n\n## Empty scene\n\n\n\n## Afterword\n\nThe end."


def test_text_export_supports_subset_and_heading_choices(manuscript) -> None:
    chapters, ungrouped, texts = manuscript

    rendered = render_manuscript(
        chapters,
        ungrouped,
        texts,
        format="text",
        selected_scene_ids={"s2", "s3"},
        include_chapter_headings=False,
        include_scene_headings=False,
        separator="\n---\n",
    )

    assert rendered == "\n---\nThe end."


def test_empty_chapter_is_included_only_when_chapter_headings_are_enabled() -> None:
    chapter = ExportChapter("Planned", ())

    assert render_manuscript([chapter], [], {}) == "# Planned"
    assert render_manuscript([chapter], [], {}, include_chapter_headings=False) == ""


def test_export_requires_confirmation_to_replace_existing_destination(tmp_path: Path, manuscript) -> None:
    target = tmp_path / "manuscript.md"
    target.write_text("prior", encoding="utf-8")

    with pytest.raises(FileExistsError):
        export_manuscript(target, *manuscript)

    assert target.read_text(encoding="utf-8") == "prior"
    export_manuscript(target, *manuscript, replace_existing=True)
    assert target.read_text(encoding="utf-8").startswith("# Chapter One")


def test_failed_export_preserves_existing_destination(tmp_path: Path, manuscript, monkeypatch) -> None:
    target = tmp_path / "manuscript.md"
    target.write_text("prior", encoding="utf-8")

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr("app.document.export.os.replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        export_manuscript(target, *manuscript, replace_existing=True)

    assert target.read_text(encoding="utf-8") == "prior"


def test_missing_selected_scene_text_is_reported_instead_of_exporting_partial_text() -> None:
    scene = ExportScene("s1", "Opening")

    with pytest.raises(ValueError, match="unavailable"):
        render_manuscript([ExportChapter("Chapter", (scene,))], [], {})


def test_duplicate_scene_ids_are_rejected() -> None:
    duplicate = ExportScene("same", "Duplicate")

    with pytest.raises(ValueError, match="Duplicate or empty"):
        render_manuscript([ExportChapter("One", (duplicate,)), ExportChapter("Two", (duplicate,))], [], {"same": "text"})
