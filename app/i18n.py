"""Qt translation loading and locale selection for the desktop interface."""

from pathlib import Path
import re

from PySide6.QtCore import QLocale, QTranslator

SUPPORTED_LANGUAGES = {"en", "uk"}
TRANSLATION_DIR = Path(__file__).resolve().parent / "resources" / "translations"
_QT_ARGUMENT = re.compile(r"%(\d+)")


def format_qt(template: str, *values: object) -> str:
    """Safely substitute Qt-style numbered placeholders in one pass."""
    return _QT_ARGUMENT.sub(
        lambda match: str(values[int(match.group(1)) - 1])
        if 1 <= int(match.group(1)) <= len(values)
        else match.group(0),
        template,
    )


def resolve_ui_language(selection: str, system_languages: list[str] | None = None) -> str:
    """Resolve a persisted language code to a supported Qt translation locale."""
    if not isinstance(selection, str):
        selection = "system"
    if selection in {"en", "uk"}:
        return selection
    if selection != "system":
        selection = "system"
    candidates = system_languages if system_languages is not None else QLocale.system().uiLanguages()
    for candidate in candidates:
        normalized = candidate.replace("-", "_").split("_", 1)[0].lower()
        if normalized in SUPPORTED_LANGUAGES:
            return normalized
    return "en"


def install_translation(application, selection: str) -> tuple[str, QTranslator | None]:
    """Install the selected compiled Qt catalog, retaining it for app lifetime."""
    language = resolve_ui_language(selection)
    translator = QTranslator(application)
    resource = TRANSLATION_DIR / f"utexteditor_{language}.qm"
    if not translator.load(str(resource)):
        if language != "en":
            return install_translation(application, "en")
        return "en", None
    application.installTranslator(translator)
    return language, translator
