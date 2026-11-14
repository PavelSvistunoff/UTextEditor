"""Free-prompt retrieval is explicit, reviewed and safe in either output mode."""

import pytest
from threading import Event
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog, QMessageBox

from app.ui.generated_text_dialog import GeneratedTextDialog
from app.ui.rag_completion import RAGCompletionDialog
from app.ui.rag_generation import request_project_generation
from tests.test_rag_completion_ui import application, scene_window
from tests.test_inline_retrieval_ui import wait


def prepare(window, monkeypatch, *, streaming=False, include=False):
    window.settings.streaming_preview = streaming
    monkeypatch.setattr("app.ui.rag_generation.QInputDialog.getMultiLineText",
                        lambda *args: ("Write about the hidden door", True))
    monkeypatch.setattr(QMessageBox, "question", lambda *args: (
        QMessageBox.StandardButton.Yes if include else QMessageBox.StandardButton.No))
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(GeneratedTextDialog, "exec", lambda self: QDialog.DialogCode.Accepted)


@pytest.mark.parametrize("streaming", [False, True])
@pytest.mark.parametrize("include", [False, True])
def test_exact_reviewed_prompt_in_both_modes_and_undo(scene_window, monkeypatch, application, streaming, include):
    window, project, scene, note, editor = scene_window
    original = editor.toPlainText()
    prepare(window, monkeypatch, streaming=streaming, include=include)
    reviewed, sent = [], []

    def review(dialog):
        reviewed.append(dialog.context.toPlainText().split("\n\n--- SOURCE MANIFEST")[0])
        return QDialog.DialogCode.Accepted

    def generate(prompt, **kwargs):
        sent.append((prompt, kwargs))
        if streaming:
            kwargs["on_chunk"]("A new scene.")
        return "A new scene."

    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_stream" if streaming else "generate_private", generate)
    request_project_generation(window)
    wait(lambda: editor.toPlainText() != original, application)
    assert sent[0][0] == reviewed[0]
    assert sent[0][1]["require_full_context"] is True
    assert sent[0][1]["maximum_tokens"] == window.settings.maximum_suggestion_length
    assert ("Author-selected scene context:" in sent[0][0]) is include
    assert project.read_scene(scene.id) == original
    editor.undo()
    assert editor.toPlainText() == original


@pytest.mark.parametrize("stage", ["source_review", "generation", "output_review"])
@pytest.mark.parametrize("change", ["disk", "settings", "buffer", "cancel"])
def test_changed_context_cannot_insert(scene_window, monkeypatch, application, stage, change):
    window, project, scene, note, editor = scene_window
    original = editor.toPlainText()
    prepare(window, monkeypatch)
    completed, errors = [], []
    monkeypatch.setattr(window, "_generation_failed", lambda *args: errors.append(args))

    def mutate():
        if change == "disk":
            (project.root / note.path).write_text("A different closed source.", encoding="utf-8")
        elif change == "settings":
            window._settings_generation += 1
        elif change == "buffer":
            editor.insertPlainText("author edit")
        else:
            window._generate_generation += 1

    def source_review(dialog):
        if stage == "source_review":
            mutate()
        completed.append(True)
        return QDialog.DialogCode.Accepted

    def generate(*args, **kwargs):
        if stage == "generation":
            changed = Event()

            def on_gui():
                mutate()
                changed.set()

            QTimer.singleShot(0, window, on_gui)
            assert changed.wait(5), "GUI mutation was not dispatched"
        completed.append(True)
        return "generated"

    def output_review(dialog):
        if stage == "output_review":
            mutate()
        completed.append(True)
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(RAGCompletionDialog, "exec", source_review)
    monkeypatch.setattr(GeneratedTextDialog, "exec", output_review)
    monkeypatch.setattr(window.provider, "generate_private", generate)
    request_project_generation(window)
    wait(lambda: bool(completed) and window._generate_worker is None, application)
    assert editor.toPlainText() == original + ("author edit" if change == "buffer" else "")
    assert project.read_scene(scene.id) == original
    assert "generated" not in editor.toPlainText()


@pytest.mark.parametrize("reject", ["source", "output"])
def test_rejected_review_keeps_author_undo(scene_window, monkeypatch, application, reject):
    window, project, scene, note, editor = scene_window
    prepare(window, monkeypatch)
    original = editor.toPlainText()
    editor.insertPlainText("author")
    reviewed = []

    def review(dialog):
        reviewed.append(True)
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(RAGCompletionDialog if reject == "source" else GeneratedTextDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: "generated")
    request_project_generation(window)
    wait(lambda: bool(reviewed) and window._generate_worker is None, application)
    assert editor.toPlainText() == original + "author"
    editor.undo()
    assert editor.toPlainText() == original


def test_no_project_refuses_without_dispatch(scene_window, monkeypatch):
    window, project, scene, note, editor = scene_window
    window.project = None
    monkeypatch.setattr("app.ui.rag_generation.QInputDialog.getMultiLineText",
                        lambda *a: pytest.fail("Must refuse before prompting"))
    request_project_generation(window)
    assert "requires an open project" in window.statusBar().currentMessage()


def test_source_exclusion_requires_rebuild(scene_window, monkeypatch, application):
    from PySide6.QtCore import Qt
    window, project, scene, note, editor = scene_window
    prepare(window, monkeypatch)
    reviews, sent = [], []

    def review(dialog):
        reviews.append(dialog.context.toPlainText())
        if len(reviews) == 1:
            item = next(dialog.sources.item(i) for i in range(dialog.sources.count())
                        if dialog.sources.item(i).data(Qt.ItemDataRole.UserRole) == note.id)
            item.setCheckState(Qt.CheckState.Checked)
            assert not dialog.send_button.isEnabled()
            return dialog.REBUILD
        assert '"reason":"excluded"' in reviews[-1]
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda prompt, **kw: (sent.append(prompt) or "Draft"))
    request_project_generation(window)
    wait(lambda: bool(sent) and window._generate_worker is None, application)
    assert len(reviews) == 2
    assert sent[0] == reviews[-1].split("\n\n--- SOURCE MANIFEST")[0]


def test_missing_index_is_visible_and_keeps_prompt(scene_window, monkeypatch, application, tmp_path):
    from app.project.rag_index import LexicalIndex
    window, project, scene, note, editor = scene_window
    prepare(window, monkeypatch)
    LexicalIndex(tmp_path / "cache", project.root, project.manifest.project_id).delete()
    reviews, sent = [], []

    def review(dialog):
        reviews.append(dialog.context.toPlainText())
        assert "unavailable" in reviews[-1].lower() or "missing" in reviews[-1].lower()
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda prompt, **kw: (sent.append(prompt) or "Draft"))
    request_project_generation(window)
    wait(lambda: bool(sent) and window._generate_worker is None, application)
    assert "Write about the hidden door" in sent[0]


def test_selected_scene_is_explicit_and_preserves_selection_undo(scene_window, monkeypatch, application):
    from PySide6.QtGui import QTextCursor
    window, project, scene, note, editor = scene_window
    prepare(window, monkeypatch, include=True)
    original = editor.toPlainText()
    cursor = editor.textCursor()
    cursor.setPosition(4)
    cursor.setPosition(10, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)
    sent = []
    monkeypatch.setattr(window.provider, "generate_private", lambda prompt, **kw: (sent.append(prompt) or "Draft"))
    request_project_generation(window)
    wait(lambda: bool(sent) and window._generate_worker is None, application)
    assert "Author-selected scene context:" in sent[0]
    assert editor.toPlainText() == original[:4] + "Draft" + original[10:]
    editor.undo()
    assert editor.toPlainText() == original
