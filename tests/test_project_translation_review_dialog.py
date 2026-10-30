from PySide6.QtWidgets import QApplication

from app.ui.project_translation_review_dialog import ProjectTranslationReviewDialog


def test_translation_review_navigates_original_and_translated_items():
    app = QApplication.instance() or QApplication([])
    dialog = ProjectTranslationReviewDialog((("Title", "Novel", "Роман"), ("Scene", "Draft", "Чернетка")))
    assert dialog.original.toPlainText() == "Novel"
    assert dialog.translated.toPlainText() == "Роман"
    dialog.list.setCurrentRow(1)
    assert dialog.original.toPlainText() == "Draft"
    assert dialog.translated.toPlainText() == "Чернетка"
    dialog.close()
    assert app is not None
