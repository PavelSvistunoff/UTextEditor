"""Qt translation loading and locale selection for the desktop interface."""

from pathlib import Path
import logging
import re

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator

SUPPORTED_LANGUAGES = {"en", "uk"}
TRANSLATION_DIR = Path(__file__).resolve().parent / "resources" / "translations"
_QT_ARGUMENT = re.compile(r"%(\d+)")


class _InterfaceTranslator(QTranslator):
    """Keep app and Qt built-in translations in one removable installation."""

    def __init__(self, language: str, parent=None) -> None:
        super().__init__(parent)
        self._qt_base = QTranslator(self)
        directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        if not self._qt_base.load(f"qtbase_{language}", directory) and language != "en":
            logging.getLogger("utexteditor.i18n").warning("Qt base translations unavailable for %s", language)

    def translate(self, context: str, source_text: str, disambiguation: str | None = None, n: int = -1) -> str | None:
        translated = super().translate(context, source_text, disambiguation, n)
        # A null result lets Qt keep searching other translators/source fallback.
        return translated or self._qt_base.translate(context, source_text, disambiguation, n) or None


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
    translator = _InterfaceTranslator(language, application)
    resource = TRANSLATION_DIR / f"utexteditor_{language}.qm"
    if not translator.load(str(resource)):
        if language != "en":
            return install_translation(application, "en")
        return "en", None
    application.installTranslator(translator)
    return language, translator
