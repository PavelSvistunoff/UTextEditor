import os
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from app.project import Project, ProjectError, parse_outline
from app.ui.main_window import MainWindow
from app.ui.project_brief_dialog import PROJECT_BRIEF_TEMPLATE, ProjectBriefDialog
from app.ui.project_setup_dialog import ProjectSetupDialog


def test_parse_outline_returns_chapters_and_scenes():
    assert parse_outline(
        "\n# Arrival\n- Find the signal\n- Meet the guide\n\n# Departure\n"
    ) == (
        ("Arrival", ("Find the signal", "Meet the guide")),
        ("Departure", ()),
    )


@pytest.mark.parametrize(
    "text",
    [
        "",
        "- Scene before chapter",
        "# \n- Scene",
        "# Chapter\nUnstructured prose",
        "# " + ("x" * 161),
    ],
)
def test_parse_outline_rejects_invalid_or_oversized_content(text):
    with pytest.raises(ProjectError):
        parse_outline(text)


def test_add_outline_creates_empty_files_and_preserves_existing_project(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    original = project.add_scene("Existing", content="keep this prose")

    chapters = project.add_outline(
        (
            ("New Chapter", ("Opening", "Turning Point")),
            ("New Chapter", ("Opening",)),
        )
    )

    assert [chapter.title for chapter in chapters] == ["New Chapter", "New Chapter"]
    assert [scene.path for scene in chapters[0].scenes] == [
        "manuscript/opening.txt",
        "manuscript/turning-point.txt",
    ]
    assert chapters[1].scenes[0].path == "manuscript/opening-2.txt"
    assert all(project.read_scene(scene.id) == "" for chapter in chapters for scene in chapter.scenes)
    assert project.read_scene(original.id) == "keep this prose"
    reopened = Project.open(project.root)
    assert [chapter.title for chapter in reopened.manifest.chapters] == [
        "New Chapter",
        "New Chapter",
    ]


def test_add_outline_rolls_back_new_files_when_manifest_write_fails(tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    original_manifest = project.manifest.to_mapping()

    def fail_write():
        raise ProjectError("manifest write failed")

    monkeypatch.setattr(project, "_write_manifest", fail_write)
    with pytest.raises(ProjectError, match="manifest write failed"):
        project.add_outline((("Chapter", ("Scene",)),))

    assert project.manifest.to_mapping() == original_manifest
    assert not (project.root / "manuscript" / "scene.txt").exists()
    assert Project.open(project.root).manifest.to_mapping() == original_manifest


def test_project_outline_generation_uses_private_provider_and_limited_tokens():
    class FakeProvider:
        prompt = None
        options = None

        def generate_private(self, prompt, **options):
            self.prompt = prompt
            self.options = options
            return "# First Steps\n- Begin"

    provider = FakeProvider()
    result = MainWindow._generate_project_outline(provider, "A quiet mystery", 3000, 0.4)

    assert result == "# First Steps\n- Begin"
    assert "A quiet mystery" in provider.prompt
    assert "write any scene content" in provider.prompt
    assert provider.options["maximum_tokens"] == 1800
    assert provider.options["temperature"] == 0.4
    assert "Return an outline for author review" in provider.options["role"]


def test_project_setup_dialog_requires_a_valid_author_reviewed_outline():
    application = QApplication.instance() or QApplication([])
    dialog = ProjectSetupDialog("# Chapter\nUnstructured text")
    assert not dialog.apply_button.isEnabled()

    dialog.editor.setPlainText("# Chapter\n- Opening")
    assert dialog.apply_button.isEnabled()
    assert dialog.outline() == (("Chapter", ("Opening",)),)

    dialog.apply_button.click()
    assert dialog.result() == QDialog.DialogCode.Accepted
    dialog.close()


def test_project_brief_dialog_starts_with_editable_template():
    application = QApplication.instance() or QApplication([])
    dialog = ProjectBriefDialog()

    assert dialog.brief() == PROJECT_BRIEF_TEMPLATE
    assert "Story premise:" in dialog.brief()
    assert "Structure preferences:" in dialog.brief()
    dialog.editor.setPlainText("My story details")
    assert dialog.brief() == "My story details"
    dialog.close()


def test_suggest_action_fills_template_using_private_local_ai(tmp_path, monkeypatch):
    application = QApplication.instance() or QApplication([])
    project = Project.create(tmp_path / "novel", "Novel")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    dialog = ProjectBriefDialog(window)
    window._project_setup_brief_dialog = dialog
    dialog.suggest_requested.connect(
        lambda text: window._suggest_project_brief(project, dialog, text)
    )
    submitted = "Story premise:\nA quiet mystery\n\nGenre:\n[unknown]"
    dialog.editor.setPlainText(submitted)
    prompt_capture = []

    def generate_private(prompt, **_options):
        prompt_capture.append(prompt)
        return "Story premise:\nA quiet mystery\n\nGenre:\n[Suggestion: cozy mystery]"

    monkeypatch.setattr(window.provider, "generate_private", generate_private)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args: QMessageBox.StandardButton.Yes,
    )
    dialog.suggest_button.click()

    loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)

    def check_complete():
        if dialog.brief().endswith("[Suggestion: cozy mystery]"):
            loop.quit()

    timeout.start(3000)
    while not dialog.brief().endswith("[Suggestion: cozy mystery]") and timeout.isActive():
        QTimer.singleShot(10, check_complete)
        loop.exec()

    assert dialog.brief().endswith("[Suggestion: cozy mystery]")
    assert submitted in prompt_capture[0]
    assert "other project" not in prompt_capture[0]
    assert not window._project_busy
    window._project_setup_brief_dialog = None
    dialog.close()
    window.close()
