"""Validate Qt TS translations and optionally compare with an extracted catalog."""

from collections import Counter
from pathlib import Path
import argparse
import re
import string
import sys
import xml.etree.ElementTree as ET


QT_PLACEHOLDER = re.compile(r"(?<!%)%(?:L?\d+|n|(?:\([^)]+\))?[sdif])")
BRACE_FIELD = re.compile(r"(?<!\{)\{(?:[A-Za-z_][A-Za-z_0-9]*|\d+)?(?:[!:}])")


def placeholders(text: str, *, braces: bool) -> Counter:
    found = Counter(QT_PLACEHOLDER.findall(text))
    if braces:
        for _, field, spec, conversion in string.Formatter().parse(text):
            if field is not None:
                found[(field, spec, conversion)] += 1
    return found


def read_catalog(path: Path):
    root = ET.parse(path).getroot()
    if root.tag != "TS":
        raise ValueError("root element must be TS")
    messages = {}
    for context in root.findall("context"):
        name = context.findtext("name") or ""
        for message in context.findall("message"):
            translation = message.find("translation")
            if translation is not None and translation.get("type") in {"obsolete", "vanished"}:
                continue
            source = message.findtext("source")
            if not name or source is None:
                raise ValueError("message is missing context or source")
            key = (name, source, message.findtext("comment") or "")
            if key in messages:
                raise ValueError(f"duplicate message in {name}: {source!r}")
            messages[key] = (message, translation)
    return root.get("language", ""), messages


def validate(path: Path, reference: Path | None = None) -> list[str]:
    errors = []
    try:
        language, messages = read_catalog(path)
        reference_messages = read_catalog(reference)[1] if reference else {}
    except (ET.ParseError, OSError, ValueError) as exc:
        return [f"{path}: invalid catalog: {exc}"]
    for context, source, comment in sorted(reference_messages.keys() - messages.keys()):
        errors.append(f"{path}: {context}: missing translation for {source!r}")
    for (context, source, comment), (message, translation) in messages.items():
        label = f"{path}: {context}: {source!r}"
        reference_entry = reference_messages.get((context, source, comment))
        if reference_entry is not None and (
            (message.get("numerus") == "yes") != (reference_entry[0].get("numerus") == "yes")
        ):
            errors.append(f"{label}: plural flag differs from extracted source")
        if translation is None or translation.get("type") == "unfinished":
            errors.append(f"{label}: missing or unfinished translation")
            continue
        forms = translation.findall("numerusform")
        if message.get("numerus") == "yes":
            required = 3 if language.startswith("uk") else 2 if language.startswith("en") else 1
            if len(forms) < required:
                errors.append(f"{label}: expected at least {required} plural forms")
            texts = ["".join(form.itertext()) for form in forms]
        else:
            if forms:
                errors.append(f"{label}: plural forms in a non-plural message")
            texts = ["".join(translation.itertext())]
        braces = bool(BRACE_FIELD.search(source))
        try:
            expected = placeholders(source, braces=braces)
            for index, value in enumerate(texts):
                if not value.strip():
                    errors.append(f"{label}: empty translation form {index + 1}")
                elif placeholders(value, braces=braces) != expected:
                    errors.append(f"{label}: placeholder mismatch in form {index + 1}")
        except ValueError as exc:
            errors.append(f"{label}: malformed format placeholders: {exc}")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--reference", type=Path, help="catalog freshly extracted from source")
    arguments = parser.parse_args(argv)
    errors = validate(arguments.catalog, arguments.reference)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"{len(errors)} translation problem(s)", file=sys.stderr)
        return 1
    print(f"{arguments.catalog}: translation validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
