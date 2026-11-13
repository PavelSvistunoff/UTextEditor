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


def test_character_review_uses_ukrainian_field_names_and_stable_ids():
    from app.i18n import install_translation
    from app.project.character_translation import CharacterTextField

    app = QApplication.instance() or QApplication([])
    _, translator = install_translation(app, "uk")
    try:
        field = CharacterTextField(("characters", 0, "primary_motivation"), "stable-id", "Мара", "Мотивація")
        label = ProjectTranslationReviewDialog.character_field_label(field)
        assert "Мара [stable-id]" in label
        assert "Головна мотивація" in label
        assert "primary_motivation" not in label
    finally:
        app.removeTranslator(translator)
        _, english = install_translation(app, "en")
        if english is not None:
            app.removeTranslator(english)
