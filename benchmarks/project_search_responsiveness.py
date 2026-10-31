"""Measure project-search GUI latency offline with synthetic project files.

Run with QT_QPA_PLATFORM=offscreen .venv/bin/python benchmarks/project_search_responsiveness.py.
Results describe this machine and workload, not portable pass/fail thresholds.
"""

import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from app.settings.settings import AppSettings
from app.ui.main_window import MainWindow


def main():
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        scenes = []
        for index in range(2000):
            path = f"scene-{index}.txt"
            (root / path).write_text("A quiet room and an old book.\n" * 40, encoding="utf-8")
            scenes.append(SimpleNamespace(id=str(index), title=f"Scene {index}", path=path))
        project = SimpleNamespace(root=root, manifest=SimpleNamespace(notes=[], project_id="benchmark"),
                                  iter_scenes=lambda: iter(scenes))
        with patch.object(AppSettings, "_default_settings_path", return_value=root / "settings.yaml"), \
                patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
            window = MainWindow()
        window.project = project
        window.show()
        window.show_project_search()
        app.processEvents()
        for query in ("absent", "book"):
            gaps = []
            last = [time.perf_counter()]
            timer = QTimer()
            timer.setInterval(5)

            def tick():
                now = time.perf_counter()
                gaps.append((now - last[0]) * 1000)
                last[0] = now

            timer.timeout.connect(tick)
            timer.start()
            start = time.perf_counter()
            window._start_project_text_search(query)
            startup = (time.perf_counter() - start) * 1000
            loop = QEventLoop()
            poll = QTimer()
            poll.setInterval(5)
            poll.timeout.connect(lambda: loop.quit() if window._project_search_cancel is None else None)
            poll.start()
            QTimer.singleShot(30000, loop.quit)
            loop.exec()
            elapsed = (time.perf_counter() - start) * 1000
            timer.stop()
            poll.stop()
            if window._project_search_cancel is not None:
                window._cancel_project_text_search()
                raise RuntimeError("Search did not finish within 30 seconds")
            print(f"{query}: startup {startup:.1f} ms; total {elapsed:.1f} ms; "
                  f"maximum timer gap {max(gaps, default=0):.1f} ms; "
                  f"{window._project_search_panel.results.count()} displayed matches")
        window.project = None
        window.close()
        app.processEvents()


if __name__ == "__main__":
    main()
