"""Keyboard cancellation and focus return across the application's dialog classes."""

import importlib

import pytest
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget
from shiboken6 import isValid

from app.project import Character, CharacterRelationship
from app.settings.settings import AppSettings

PROFILE = Character(id="00000000-0000-4000-8000-000000000001", full_name="Mara")
RELATION = CharacterRelationship("00000000-0000-4000-8000-000000000002", PROFILE.id, "00000000-0000-4000-8000-000000000003")
CASES = [
    ("ai_context_disclosure", "AIContextDisclosure", ("http://localhost:11434",)),
    ("ai_debug_window", "AIDebugWindow", ()),
    ("analysis_window", "AnalysisWindow", ("Analysis", "Captured", "Result")),
    ("auto_writer_dialog", "AutoWriterDialog", (1,)),
    ("auto_writer_dialog", "AutoWriterProgressDialog", ()),
    ("auto_writer_review_dialog", "AutoWriterReviewDialog", ([("s1", "Scene", "Draft")],)),
    ("character_dialog", "CharacterDialog", (PROFILE,)),
    ("character_relationship_dialog", "CharacterRelationshipDialog", (RELATION,)),
    ("completion_context_dialog", "CompletionContextDialog", ("http://localhost:11434", "Context", "Summary")),
    ("completion_notes_dialog", "CompletionNotesDialog", ([], set())),
    ("conflict_dialog", "ConflictDialog", ("base", "disk", "buffer", "proposal", 0)),
    ("export_preview_dialog", "ExportPreviewDialog", ("Captured manuscript",)),
    ("generated_text_dialog", "GeneratedTextDialog", ("Generated draft",)),
    ("generated_text_dialog", "StreamingPreviewDialog", ()),
    ("pdf_options_dialog", "PdfOptionsDialog", ("Title",)),
    ("project_brief_dialog", "ProjectBriefDialog", ()),
    ("project_setup_dialog", "ProjectSetupDialog", ("# Chapter\n- Scene",)),
    ("project_translation_review_dialog", "ProjectTranslationReviewDialog", ([("Scene", "Original", "Переклад")],)),
    ("quick_open_dialog", "QuickOpenDialog", ((),)),
    ("revision_history_dialog", "RevisionHistoryDialog", ()),
    ("settings_dialog", "SettingsDialog", (AppSettings(),)),
    ("spellcheck_review_dialog", "SpellcheckReviewDialog", ([], "original")),
    ("writing_goal_dialog", "WritingGoalDialog", (100, "active_scene")),
    ("writing_goal_history_dialog", "WritingGoalHistoryDialog", ({},)),
]


@pytest.mark.parametrize("module,name,args", CASES, ids=[case[1] for case in CASES])
def test_dialog_keyboard_cancel_preserves_text_and_returns_focus(module, name, args):
    app = QApplication.instance() or QApplication([])
    owner = QWidget()
    layout = QVBoxLayout(owner)
    origin = QLineEdit("unchanged owner text", owner)
    layout.addWidget(origin)
    owner.show()
    owner.activateWindow()
    origin.setFocus()
    QTest.qWait(30)
    dialog_type = getattr(importlib.import_module("app.ui." + module), name)
    dialog = dialog_type(*args, parent=owner)
    finished = []
    dialog.finished.connect(finished.append)
    errors = []

    def exercise_dialog():
        try:
            first = dialog.focusWidget()
            assert first is not None and first.isEnabled(), name
            fields = dialog.findChildren(QLineEdit) + dialog.findChildren(QPlainTextEdit)
            before = {widget: widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText() for widget in fields}
            for backwards in (False, True):
                for _ in range(4):
                    focused = dialog.focusWidget()
                    assert focused is not None and (focused is dialog or dialog.isAncestorOf(focused))
                    modifier = Qt.KeyboardModifier.NoModifier
                    if isinstance(focused, QPlainTextEdit) and not focused.tabChangesFocus():
                        modifier |= Qt.KeyboardModifier.ControlModifier
                    if backwards:
                        modifier |= Qt.KeyboardModifier.ShiftModifier
                    QTest.keyClick(focused, Qt.Key.Key_Tab, modifier)
                    app.processEvents()
            assert before == {widget: widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText() for widget in fields}
            boxes = dialog.findChildren(QDialogButtonBox)
            cancel = next((box.button(QDialogButtonBox.StandardButton.Cancel) for box in boxes if box.button(QDialogButtonBox.StandardButton.Cancel)), None)
            if cancel is not None:
                cancel.setFocus()
                QTest.keyClick(cancel, Qt.Key.Key_Return)
            else:
                QTest.keyClick(dialog, Qt.Key.Key_Escape)
        except Exception as error:
            errors.append(error)
            if isValid(dialog):
                dialog.reject()

    try:
        owner.windowHandle().requestActivate()
        origin.setFocus()
        QTimer.singleShot(100, exercise_dialog)
        result = dialog.exec()
        QTest.qWait(100)
        if errors:
            raise errors[0]
        assert result == QDialog.DialogCode.Rejected and finished == [QDialog.DialogCode.Rejected]
        assert origin.text() == "unchanged owner text"
        assert owner.focusWidget() is origin
        if app.platformName() != "offscreen":
            assert app.focusWidget() is origin
    finally:
        if isValid(dialog):
            dialog.close()
        owner.close()


@pytest.mark.parametrize("allow,key", [(False, Qt.Key.Key_Return), (True, Qt.Key.Key_Return), (True, Qt.Key.Key_Space)])
def test_ai_disclosure_defaults_to_decline_but_supports_explicit_keyboard_allow(allow, key):
    from app.ui.ai_context_disclosure import AIContextDisclosure

    app = QApplication.instance() or QApplication([])
    dialog = AIContextDisclosure("http://localhost:11434")
    results, errors = [], []
    dialog.finished.connect(results.append)

    def choose():
        try:
            decline = dialog.buttons.button(QDialogButtonBox.StandardButton.No)
            assert dialog.focusWidget() is decline
            target = dialog.buttons.button(QDialogButtonBox.StandardButton.Yes) if allow else decline
            if allow:
                target.setFocus()
            QTest.keyClick(target, key)
        except Exception as error:
            errors.append(error)
            if isValid(dialog):
                dialog.reject()

    QTimer.singleShot(100, choose)
    result = dialog.exec()
    if errors:
        raise errors[0]
    assert result == (QDialog.DialogCode.Accepted if allow else QDialog.DialogCode.Rejected)
    assert results == [result]
    assert app is not None
