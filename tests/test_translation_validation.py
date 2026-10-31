"""Localization validation works without a compiled Qt catalog."""

import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess
import sys

import pytest
from PySide6.QtCore import QTranslator

from tools.check_translations import main, validate


def catalog(path, entries, language="uk_UA"):
    root = ET.Element("TS", language=language)
    context = ET.SubElement(root, "context")
    ET.SubElement(context, "name").text = "Window"
    for source, translated, numerus in entries:
        message = ET.SubElement(context, "message", {"numerus": "yes"} if numerus else {})
        ET.SubElement(message, "source").text = source
        translation = ET.SubElement(message, "translation")
        if numerus:
            for text in translated:
                ET.SubElement(translation, "numerusform").text = text
        else:
            translation.text = translated
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def test_missing_translation_and_placeholders_fail(tmp_path, capsys):
    reference = tmp_path / "reference.ts"
    target = tmp_path / "uk.ts"
    catalog(reference, [("Welcome %1", "", False), ("Missing", "", False)])
    catalog(target, [("Welcome %1", "Вітаю %2", False)])
    assert main([str(target), "--reference", str(reference)]) == 1
    output = capsys.readouterr().err
    assert "missing translation" in output
    assert "placeholder mismatch" in output


def test_plural_and_named_placeholders_are_checked(tmp_path):
    target = tmp_path / "uk.ts"
    catalog(target, [("%n entries for {name}", ["%n для {name}", "%n для {name}", "%n для {other}"], True)])
    assert any("placeholder mismatch" in error for error in validate(target))
    catalog(target, [("%n entries", ["%n запис"], True)])
    assert any("3 plural forms" in error for error in validate(target))


def test_empty_malformed_and_valid_catalogs(tmp_path):
    target = tmp_path / "uk.ts"
    catalog(target, [("Save", "", False)])
    assert any("empty translation" in error for error in validate(target))
    target.write_text("<TS>", encoding="utf-8")
    assert any("invalid catalog" in error for error in validate(target))
    catalog(target, [("Hello {name} %1", "Привіт {name} %1", False)])
    assert validate(target) == []


def test_duplicate_messages_are_reported_instead_of_masking_errors(tmp_path):
    target = tmp_path / "uk.ts"
    catalog(target, [("Hello %1", "Привіт %2", False), ("Hello %1", "Привіт %1", False)])
    errors = validate(target)
    assert any("duplicate message" in error and "Hello %1" in error for error in errors)


def test_compiled_ukrainian_character_strings_use_runtime_context(tmp_path):
    lrelease = Path(sys.executable).parent / "pyside6-lrelease"
    if not lrelease.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    target = tmp_path / "uk.qm"
    subprocess.run([str(lrelease), "translations/utexteditor_uk.ts", "-qm", str(target)], check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(target))
    assert translator.translate("CharacterDialog", "Choose Portrait…") == "Вибрати портрет…"
    assert translator.translate("CharacterDialog", "No open associated scene") == "Немає відкритої пов’язаної сцени"
    assert translator.translate("CharacterDialog", "Current recorded state:") == "Поточний записаний стан:"
    assert translator.translate("CharacterDialog", "No character state changes recorded.") == "Змін стану персонажа не записано."
    assert translator.translate("CharacterDialog", "Scene history:") == "Історія сцен:"
    assert translator.translate("MainWindow", "Open failed") == "Не вдалося відкрити"
    assert translator.translate("MainWindow", "Opening {title}…").format(title="Сцена") == "Відкриття: Сцена…"
    assert translator.translate("MainWindow", "Document could not be opened") == "Не вдалося відкрити документ"
    assert translator.translate("MainWindow", "Save failed") == "Не вдалося зберегти"
    assert translator.translate("MainWindow", "Book PDF compiled to {path}").format(path="книга.pdf") == "Книгу PDF створено: книга.pdf"
    assert translator.translate("MainWindow", "Plain text (*.txt)") == "Звичайний текст (*.txt)"
    assert translator.translate("MainWindow", "Recover unsaved work") == "Відновити незбережену роботу"
    assert translator.translate("MainWindow", "Recovery restore failed: {error}").format(error="помилка") == "Не вдалося відновити дані: помилка"
    assert translator.translate("MainWindow", "Canonical file is missing: {path}").format(path="файл") == "Основний файл відсутній: файл"
    assert translator.translate("MainWindow", "Recovery snapshot") == "Копія для відновлення"
    assert translator.translate("MainWindow", "The link is no longer available.") == "Посилання більше недоступне."
    assert translator.translate("MainWindow", "Save changes to {name}?").format(name="розділ.txt") == "Зберегти зміни в документі розділ.txt?"
    assert translator.translate("MainWindow", "Permanently delete {path}? This cannot be undone.").format(path="сцена.txt") == "Остаточно видалити сцена.txt? Цю дію неможливо скасувати."
    assert translator.translate("SettingsDialog", "The context template must include {context}.") == "Шаблон контексту має містити {context}."
    assert translator.translate("AIDebugWindow", "Requests can contain document text. This debug history is kept only in memory.") == "Запити можуть містити текст документа. Ця історія діагностики зберігається лише в пам’яті."
    assert translator.translate("MainWindow", "{document_id}: an editor for the canonical path is already open; recovered content was opened separately.").format(document_id="abc") == "abc: редактор для основного файлу вже відкрито; відновлений вміст відкрито окремо."
    assert translator.translate("MainWindow", "Unreadable recovery entry: {path} ({message})").format(path="файл", message="помилка") == "Не вдалося прочитати запис відновлення: файл (помилка)"
    assert translator.translate("MainWindow", "Manuscript exported to {path}").format(path="роман.txt") == "Рукопис експортовано до роман.txt"
    assert translator.translate("MainWindow", "Replace the existing file {path}?").format(path="книга.pdf") == "Замінити наявний файл книга.pdf?"
    assert translator.translate("MainWindow", "Autosave failed: {error}").format(error="помилка") == "Не вдалося автоматично зберегти: помилка"
    assert translator.translate("EditorWidget", 'Replace "{original}" with "{replacement}"').format(
        original="помлка", replacement="помилка"
    ) == 'Замінити "помлка" на "помилка"'
    assert translator.translate("EditorWidget", "Ignore") == "Ігнорувати"


def test_extracted_sources_match_ukrainian_catalog(tmp_path):
    lupdate = Path(sys.executable).parent / "pyside6-lupdate"
    if not lupdate.exists():
        pytest.skip("Qt Linguist extractor is unavailable")
    reference = tmp_path / "extracted.ts"
    sources = sorted(Path("app/ui").glob("*.py"))
    subprocess.run([str(lupdate), *(str(path) for path in sources), "-ts", str(reference)],
                   check=True, capture_output=True)
    assert validate(Path("translations/utexteditor_uk.ts"), reference) == []
