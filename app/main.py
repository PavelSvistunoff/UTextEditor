"""Application entry point."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

if __package__:
    from .ui.main_window import MainWindow
else:
    # Support ``python app/main.py`` during local development as well as
    # the package/module and installed-console-script entry points.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
