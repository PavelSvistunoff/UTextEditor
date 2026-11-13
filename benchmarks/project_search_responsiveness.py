"""Measure project-search GUI latency offline with synthetic project files.

Run with QT_QPA_PLATFORM=offscreen .venv/bin/python benchmarks/project_search_responsiveness.py.
Results describe this machine and workload, not portable pass/fail thresholds.
"""

import argparse
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from app.project.search import MAX_DOCUMENT_BYTES, MAX_MATCHES
from app.settings.settings import AppSettings
from app.ui.main_window import MainWindow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenes", type=int, default=2000)
    parser.add_argument("--lines", type=int, default=40)
    parser.add_argument("--repetitions", type=int, default=1)
    args = parser.parse_args()
    if min(args.scenes, args.lines, args.repetitions) < 1:
        parser.error("scene, line and repetition counts must be positive")
    paragraphs = ("A quiet room and an old book.\n", "Тиха кімната, стара книга та мрія.\n",
                  "Une fenêtre ouverte — café et soleil. 🌿\n")
    if args.lines * max(len(text.encode("utf-8")) for text in paragraphs) > MAX_DOCUMENT_BYTES:
        parser.error("scene text must fit within the project search document size limit")
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        scenes = []
        for index in range(args.scenes):
            path = f"scene-{index}.txt"
            (root / path).write_text(paragraphs[index % len(paragraphs)] * args.lines, encoding="utf-8")
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
        print(f"scenes={args.scenes}, lines_per_scene={args.lines}, repetitions={args.repetitions}")
        for query in ("absent", "книга", "🌿") * args.repetitions:
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
            expected = (0 if query == "absent" else
                        min(MAX_MATCHES, sum(index % 3 == (1 if query == "книга" else 2)
                                      for index in range(args.scenes)) * args.lines))
            if window._project_search_panel.results.count() != expected:
                raise AssertionError(f"Unexpected result count for {query!r}")
            print(f"{query}: startup {startup:.1f} ms; total {elapsed:.1f} ms; "
                  f"maximum timer gap {max(gaps, default=0):.1f} ms; "
                  f"{window._project_search_panel.results.count()} displayed matches")
        for index in range(args.scenes):
            actual = (root / f"scene-{index}.txt").read_text(encoding="utf-8")
            if actual != paragraphs[index % len(paragraphs)] * args.lines:
                raise AssertionError(f"Benchmark search changed scene {index}")
        window.project = None
        window.close()
        app.processEvents()


if __name__ == "__main__":
    main()
