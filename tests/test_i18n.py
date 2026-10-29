import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from app.i18n import format_qt, install_translation, resolve_ui_language
from app.settings.settings import AppSettings
from app.ui.settings_dialog import SettingsDialog
from app.project import WordCount
from app.ui.project_view import ProjectView
from app.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    ("selection", "system", "expected"),
    [
        ("en", ["uk_UA"], "en"),
        ("uk", ["en_US"], "uk"),
        ("system", ["uk_UA"], "uk"),
        ("system", ["en-GB"], "en"),
        ("system", ["fr_FR"], "en"),
        ("invalid", ["uk"], "uk"),
        ("invalid", ["fr"], "en"),
        (["uk"], ["fr"], "en"),
    ],
)
def test_ui_language_resolution(selection, system, expected):
    assert resolve_ui_language(selection, system) == expected


def test_ukrainian_catalog_translations_and_placeholders_are_complete():
    catalog = Path(__file__).parents[1] / "translations" / "utexteditor_uk.ts"
    root = ET.parse(catalog).getroot()
    placeholders = re.compile(r"%n|%[1-9]\d*|\{[A-Za-z_][A-Za-z0-9_]*\}")

    for message in root.findall(".//message"):
        source = message.findtext("source", "")
        translation = message.find("translation")
        assert translation is not None
        if translation.get("type") in {"vanished", "obsolete"}:
            continue
        assert translation.get("type") != "unfinished"
        expected = sorted(placeholders.findall(source))
        forms = translation.findall("numerusform") or [translation]
        for form in forms:
            assert sorted(placeholders.findall(form.text or "")) == expected, source


def test_qt_placeholder_formatting_preserves_placeholder_like_user_text():
    assert format_qt("%1 — %2", "%2 manuscript", 3) == "%2 manuscript — 3"


def test_translation_catalog_loads_and_translates_interface(application):
    language, translator = install_translation(application, "uk")
    try:
        assert language == "uk"
        assert translator is not None
        assert QCoreApplication.translate("MainWindow", "Project") == "Проєкт"
        assert QCoreApplication.translate("MainWindow", "Uncatalogued text") == "Uncatalogued text"
        view = ProjectView()
        assert view._count_label("Сцена", WordCount(1, True)) == "Сцена — 1 слово"
        assert view._count_label("Сцена", WordCount(3, True)) == "Сцена — 3 слова"
        assert view._count_label("Сцена", WordCount(5, True)) == "Сцена — 5 слів"
        assert view._translate_context_action("Find Scenes Mentioning Character…") == "Знайти сцени зі згадкою персонажа…"
        view.close()
    finally:
        application.removeTranslator(translator)


def test_english_catalog_provides_correct_numerus_forms(application):
    language, translator = install_translation(application, "en")
    try:
        view = ProjectView()
        assert language == "en"
        assert view._count_label("Scene", WordCount(1, True)) == "Scene — 1 word"
        assert view._count_label("Scene", WordCount(2, True)) == "Scene — 2 words"
        view.close()
    finally:
        if translator is not None:
            application.removeTranslator(translator)


def test_missing_translation_resource_falls_back_to_english(application, monkeypatch, tmp_path):
    import app.i18n as i18n

    monkeypatch.setattr(i18n, "TRANSLATION_DIR", tmp_path)
    language, translator = install_translation(application, "uk")
    assert language == "en"
    assert translator is None


def test_settings_dialog_persists_language_code_separately(application):
    settings = AppSettings(language="English", ui_language="uk")
    dialog = SettingsDialog(settings)
    dialog.ui_language.setCurrentIndex(dialog.ui_language.findData("en"))
    dialog.language.setCurrentIndex(dialog.language.findData("Ukrainian"))

    dialog.accept()

    assert settings.ui_language == "en"
    assert settings.language == "Ukrainian"
    assert dialog.ui_language.itemData(0) == "system"
    assert dialog.ui_language.itemText(1) == "English"
    assert dialog.ui_language.itemText(2) == "Українська"
    dialog.close()


def test_settings_dialog_uses_loaded_ukrainian_catalog(application):
    language, translator = install_translation(application, "uk")
    try:
        dialog = SettingsDialog(AppSettings())
        assert language == "uk"
        assert dialog.windowTitle() == "Налаштування ШІ"
        assert dialog.ui_language.itemText(0) == "Мова системи"
        dialog.close()
    finally:
        application.removeTranslator(translator)


def test_main_window_installs_saved_language_before_building_menus(
    application, monkeypatch, tmp_path
):
    settings_path = tmp_path / "settings.yaml"
    AppSettings(ui_language="uk").save(settings_path)
    monkeypatch.setattr(
        AppSettings,
        "_default_settings_path",
        staticmethod(lambda: settings_path),
    )
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    try:
        assert window.menuBar().actions()[0].text() == "Файл"
        assert window.menuBar().actions()[4].text() == "Проєкт"
        assert window.menuBar().actions()[-1].text() == "Налаштування"
        language_menu = window.menuBar().actions()[-1].menu().actions()[0].menu()
        assert [action.text() for action in language_menu.actions()] == [
            "Мова системи", "English", "Українська"
        ]
    finally:
        translator = window._ui_translator
        window.close()
        if translator is not None:
            application.removeTranslator(translator)
        assert QCoreApplication.translate("MainWindow", "Project") == "Project"


def test_settings_menu_persists_language_choice_and_requires_restart(
    application, monkeypatch, tmp_path
):
    settings_path = tmp_path / "settings.yaml"
    AppSettings(ui_language="en").save(settings_path)
    monkeypatch.setattr(
        AppSettings,
        "_default_settings_path",
        staticmethod(lambda: settings_path),
    )
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    with patch("app.ui.main_window.QMessageBox.information") as show_information:
        window._ui_language_actions["uk"].trigger()
    try:
        assert AppSettings.load(settings_path).ui_language == "uk"
        assert window.settings.ui_language == "uk"
        assert window._ui_language_actions["uk"].isChecked()
        show_information.assert_called_once()
        assert "restart" in show_information.call_args.args[2].lower()
    finally:
        translator = window._ui_translator
        window.close()
        if translator is not None:
            application.removeTranslator(translator)


def test_settings_menu_restores_selection_when_language_cannot_be_saved(
    application, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        AppSettings,
        "_default_settings_path",
        staticmethod(lambda: tmp_path / "settings.yaml"),
    )
    AppSettings(ui_language="en").save(tmp_path / "settings.yaml")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()

    def fail_save():
        raise OSError("read only")

    monkeypatch.setattr(window.settings, "save", fail_save)
    with patch("app.ui.main_window.QMessageBox.warning") as show_warning:
        window._ui_language_actions["uk"].trigger()
    try:
        assert window.settings.ui_language == "en"
        assert window._ui_language_actions["en"].isChecked()
        assert not window._ui_language_actions["uk"].isChecked()
        show_warning.assert_called_once()
    finally:
        translator = window._ui_translator
        window.close()
        if translator is not None:
            application.removeTranslator(translator)
