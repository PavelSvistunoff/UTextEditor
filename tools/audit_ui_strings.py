"""Report likely unmarked UI literals for a human localization audit.

This deliberately covers selected Qt APIs only. Results are candidates, not a
proof of either untranslated text or complete localization coverage.
"""

import argparse
import ast
from pathlib import Path
import sys


WIDGET_CONSTRUCTORS = {"QAction", "QCheckBox", "QLabel", "QMenu", "QPushButton", "QRadioButton"}
TEXT_METHODS = {"addAction", "addButton", "setAccessibleDescription", "setAccessibleName", "setPlaceholderText",
                "setStatusTip", "setText", "setToolTip", "setWindowTitle", "showMessage"}
MESSAGE_METHODS = {"critical", "information", "question", "warning"}
INPUT_METHODS = {"getItem", "getMultiLineText", "getText"}
FILE_METHODS = {"getExistingDirectory", "getOpenFileName", "getSaveFileName"}


def _literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        value = node.value
    elif isinstance(node, ast.JoinedStr):
        value = ast.unparse(node)
    else:
        return None
    return value if any(character.isalpha() for character in value) else None


def audit_source(source: str, path: Path) -> list[str]:
    tree = ast.parse(source, filename=str(path))
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        positions = ()
        if isinstance(target, ast.Name) and target.id in WIDGET_CONSTRUCTORS:
            positions = (0,)
        elif isinstance(target, ast.Attribute):
            owner = target.value.id if isinstance(target.value, ast.Name) else None
            if owner == "QMessageBox" and target.attr in MESSAGE_METHODS:
                positions = (1, 2)
            elif owner == "QInputDialog" and target.attr in INPUT_METHODS:
                positions = (1, 2)
            elif owner == "QFileDialog" and target.attr in FILE_METHODS:
                positions = (1, 3) if target.attr != "getExistingDirectory" else (1,)
            elif target.attr in TEXT_METHODS:
                positions = (0,)
        for index in positions:
            if index < len(node.args) and (literal := _literal(node.args[index])) is not None:
                findings.append((node.lineno, f"{path}:{node.lineno}: {literal!r}"))
    return [message for _, message in sorted(findings)]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("app/ui")])
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args(argv)
    paths = sorted({file for path in args.paths for file in (path.rglob("*.py") if path.is_dir() else [path])})
    findings = []
    try:
        for path in paths:
            findings.extend(audit_source(path.read_text(encoding="utf-8"), path))
    except (OSError, SyntaxError, UnicodeError) as exc:
        print(f"UI string audit failed: {exc}", file=sys.stderr)
        return 2
    for finding in findings:
        print(finding)
    print(f"{len(findings)} candidate(s); review manually for translation scope.", file=sys.stderr)
    return int(args.fail_on_findings and bool(findings))


if __name__ == "__main__":
    raise SystemExit(main())
