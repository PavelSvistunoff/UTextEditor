"""Localization validation works without a compiled Qt catalog."""

import xml.etree.ElementTree as ET

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
