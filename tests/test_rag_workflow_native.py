"""Direct Cocoa controls; fake generation, separate from live retrieval evidence."""

import os

import pytest
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QInputDialog

from app.project import SceneCharacterAssociation
from app.ui.character_dialog import CharacterDialog
from app.ui.generated_text_dialog import GeneratedTextDialog
from app.ui.project_brief_dialog import ProjectBriefDialog
from app.ui.project_translation_review_dialog import ProjectTranslationReviewDialog
from app.ui.rag_completion import RAGCompletionDialog
from app.ui.rag_generation import request_project_generation
from app.ui.settings_dialog import SettingsDialog
from app.ui.translation_glossary_dialog import TranslationGlossaryDialog
from tests.test_analysis_retrieval_ui import select_scene
from tests.test_inline_retrieval_ui import wait
from tests.test_rag_completion_ui import application, scene_window

pytestmark = pytest.mark.skipif(os.environ.get("QT_QPA_PLATFORM") != "cocoa",
                                reason="Direct native Cocoa walkthrough only")


@pytest.mark.parametrize("mode", ["generation", "planning", "analysis", "profile", "development", "translation", "spelling"])
def test_native_context_controls_review_send_and_author_rejection(scene_window, monkeypatch, application, mode):
    window, project, scene, note, editor = scene_window
    window.settings.completion_enabled = False
    window.show()
    window.activateWindow()
    errors, reviews, calls, finals = [], [], [], []
    original = editor.toPlainText()
    base_exec = QDialog.exec
    monkeypatch.setattr(window, "_ensure_ai_context_consent", lambda **kw: True)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: errors.append(str(args[-1])))
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *args: ("Write about the hidden door", True))
    monkeypatch.setattr(QInputDialog, "getItem", lambda *args: (args[3][0], True))

    def native_exec(dialog, drive):
        def keys():
            try:
                assert dialog.isVisible()
                drive(dialog)
            except Exception as exc:
                errors.append(repr(exc))
                dialog.reject()
        QTimer.singleShot(80, keys)
        return base_exec(dialog)

    def source_keys(dialog):
        assert dialog.context.isReadOnly() and dialog.send_button.isEnabled()
        assert dialog.context.toPlainText()
        reviews.append(dialog.context.toPlainText().split("\n\n--- SOURCE MANIFEST")[0])
        dialog.send_button.setFocus()
        QTest.keyClick(dialog.send_button, Qt.Key.Key_Space)
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda dialog: native_exec(dialog, source_keys))

    def reject_keys(dialog):
        finals.append(True)
        QTest.keyClick(dialog, Qt.Key.Key_Escape)
    monkeypatch.setattr(GeneratedTextDialog, "exec", lambda dialog: native_exec(dialog, reject_keys))
    monkeypatch.setattr(ProjectTranslationReviewDialog, "exec", lambda dialog: native_exec(dialog, reject_keys))

    def generate(prompt, **options):
        calls.append(prompt)
        if mode == "translation":
            return '{"translation":"Translated"}'
        if mode == "spelling":
            return '[{"start":4,"end":10,"replacement":"secret","original_text":"hidden"}]'
        if mode == "profile":
            return '{"primary_motivation":"Find the hidden door"}'
        if mode == "development":
            return '{"proposals":[{"field":"current_state","value":"Curious","evidence":"hidden door"}]}'
        return "An idea about the hidden door"
    monkeypatch.setattr(window.provider, "generate_private", generate)
    dialog = None
    if mode == "generation":
        request_project_generation(window)
        wait(lambda: bool(finals), application)
    elif mode == "planning":
        dialog = ProjectBriefDialog(window)
        dialog.show()
        dialog.retrieval.setFocus()
        QTest.keyClick(dialog.retrieval, Qt.Key.Key_Space)
        assert dialog.retrieval.isChecked()
        dialog.editor.setPlainText("A hidden door story")
        window._project_setup_brief_dialog = dialog
        window._suggest_project_brief(project, dialog, dialog.brief())
        wait(lambda: dialog.brief() == "An idea about the hidden door", application)
    elif mode == "analysis":
        window._analysis_retrieval_action.trigger()
        assert window._analysis_retrieval_action.isChecked()
        select_scene(window, scene)
        window._start_project_analysis("summary")
        wait(lambda: bool(window._analysis_windows), application)
        window._analysis_windows[-1].reject()
    elif mode in {"profile", "development"}:
        character = project.add_character("Mara")
        project.associate_character(scene.id, SceneCharacterAssociation(character.id))
        dialog = CharacterDialog(character)
        dialog.show()
        dialog.retrieval.setFocus()
        QTest.keyClick(dialog.retrieval, Qt.Key.Key_Space)
        assert dialog.retrieval.isChecked()
        if mode == "profile":
            window._suggest_character_profile(dialog, project)
        else:
            def arc_exec(review):
                if review.windowTitle() == "Review character development":
                    return native_exec(review, reject_keys)
                return base_exec(review)
            monkeypatch.setattr(QDialog, "exec", arc_exec)
            window._suggest_scene_development(dialog, project)
        wait(lambda: bool(finals), application)
        assert not dialog.motivation.toPlainText()
    elif mode == "translation":
        window._translation_retrieval_action.trigger()
        assert window._translation_retrieval_action.isChecked()
        def glossary_keys(review):
            assert review.table.isVisible()
            button = review.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok)
            button.setFocus()
            QTest.keyClick(button, Qt.Key.Key_Space)
        monkeypatch.setattr(TranslationGlossaryDialog, "exec", lambda review: native_exec(review, glossary_keys))
        window.translate_project_to_ukrainian()
        wait(lambda: bool(finals) and not window._project_busy, application)
    else:
        settings = SettingsDialog(window.settings)
        settings.show()
        from PySide6.QtWidgets import QTabWidget
        tabs = settings.findChild(QTabWidget)
        page = settings.spelling_project_dictionary.parentWidget()
        while page is not None and tabs.indexOf(page) < 0:
            page = page.parentWidget()
        assert page is not None
        tabs.setCurrentWidget(page)
        settings.spelling_project_dictionary.setFocus()
        QTest.keyClick(settings.spelling_project_dictionary, Qt.Key.Key_Space)
        assert settings.spelling_project_dictionary.isChecked()
        settings.accept()
        window.check_spelling()
        wait(lambda: bool(editor.spell_suggestions), application)
        editor.apply_spell_suggestions(editor.spell_suggestions)
        editor.undo()
    wait(lambda: not window._workers, application)
    assert not errors, errors
    assert calls == reviews and calls
    assert editor.toPlainText() == original == project.read_scene(scene.id)
    if dialog is not None:
        dialog.reject()
    window._project_setup_brief_dialog = None
    print({"native_workflow": mode, "reviewed_requests": len(reviews), "manuscript_preserved": True})
