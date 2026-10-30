from PySide6.QtWidgets import QApplication, QLabel

from app.ui.completion_context_dialog import CompletionContextDialog


def test_completion_context_dialog_displays_captured_text_read_only():
    app = QApplication.instance() or QApplication([])
    dialog = CompletionContextDialog("https://example.test", "<characters>\nMara\n</characters>", "Unsaved note")
    assert dialog.context.isReadOnly()
    assert dialog.context.toPlainText() == "<characters>\nMara\n</characters>"
    assert "example.test" in dialog.findChildren(QLabel)[0].text()
    dialog.close()
    assert app is not None
