"""Application entry point."""

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

logger = logging.getLogger("utexteditor.app")


if __package__:
    from .ui.main_window import MainWindow
else:
    # Support ``python app/main.py`` during local development as well as
    # the package/module and installed-console-script entry points.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.ui.main_window import MainWindow

from app.document.recovery import RecoveryStore
from app.document.writing_goals import WritingGoalStore
from app.settings.settings import AppSettings


def main() -> int:
    # Configure logging early so modules can emit diagnostics
    try:
        from app.logging_config import configure_logging

        configure_logging()
    except Exception:
        logger.exception("Failed to configure application logging; continuing with defaults.")

    app = QApplication(sys.argv)
    # Set application icon from bundled resources so the window and dock show it
    icon_path = Path(__file__).resolve().parents[1] / "app" / "resources" / "icon.svg"
    if not icon_path.exists():
        # Fallback to package-relative resources for installed package layout
        icon_path = Path(__file__).resolve().parents[1] / "resources" / "icon.svg"
    try:
        app.setWindowIcon(QIcon(str(icon_path)))
    except Exception:
        logger.exception("Failed to load application icon %s; continuing without a custom window icon.", icon_path)
    window = MainWindow(
        recovery_store=RecoveryStore(),
        writing_goal_store=WritingGoalStore(
            AppSettings._default_settings_path().with_name("writing-goals.json")
        ),
    )
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
