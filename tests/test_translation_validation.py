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
    assert translator.translate("MainWindow", "Open failed") == "Не вдалося відкрити"


def test_extracted_sources_match_ukrainian_catalog(tmp_path):
    lupdate = Path(sys.executable).parent / "pyside6-lupdate"
    if not lupdate.exists():
        pytest.skip("Qt Linguist extractor is unavailable")
    reference = tmp_path / "extracted.ts"
    sources = sorted(Path("app/ui").glob("*.py"))
    subprocess.run([str(lupdate), *(str(path) for path in sources), "-ts", str(reference)],
                   check=True, capture_output=True)
    assert validate(Path("translations/utexteditor_uk.ts"), reference) == []
