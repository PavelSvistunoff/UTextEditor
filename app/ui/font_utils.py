"""Font helpers for choosing an installed editor font."""

from functools import lru_cache
import platform

from PySide6.QtGui import QFont, QFontDatabase, QFontInfo


@lru_cache(maxsize=1)
def _installed_families() -> dict[str, str]:
    return {
        installed.casefold(): installed for installed in QFontDatabase.families()
    }


@lru_cache(maxsize=1)
def _fixed_width_family() -> str | None:
    for family in _installed_families().values():
        if QFontInfo(QFont(family)).fixedPitch():
            return family
    return None


def editor_font(family: str | None, point_size: int) -> QFont:
    installed_family = _installed_families().get((family or "").casefold())
    if installed_family is None:
        fixed_width_family = _fixed_width_family()
        font = QFont(fixed_width_family) if fixed_width_family else QFont()
    else:
        font = QFont(installed_family)
    font.setPointSize(point_size)
    return font


def configure_application_font(application) -> None:
    preferences = {
        "Darwin": (".AppleSystemUIFont", "Helvetica Neue", "Arial"),
        "Windows": ("Segoe UI", "Arial"),
        "Linux": ("Noto Sans", "DejaVu Sans", "Liberation Sans"),
    }
    families = _installed_families()
    family = next(
        (
            families[candidate.casefold()]
            for candidate in preferences.get(platform.system(), ())
            if candidate.casefold() in families
        ),
        None,
    )
    if family is None:
        family = next(
            (
                installed
                for installed in families.values()
                if not QFontInfo(QFont(installed)).fixedPitch()
            ),
            None,
        )
    if family is None:
        return
    font = QFont(family)
    font.setPointSize(application.font().pointSize())
    application.setFont(font)
