from threading import Event
from unittest.mock import patch

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from app.settings.settings import AppSettings
from app.ui.main_window import MainWindow
from app.ui.workers import FunctionWorker


@pytest.fixture
def window(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(AppSettings, "_default_settings_path", staticmethod(lambda: tmp_path / "settings.yaml"))
    AppSettings(ui_language="en").save(tmp_path / "settings.yaml")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    yield window
    window.close()
    app.processEvents()


def wait_until(predicate):
    if predicate():
        return
    loop = QEventLoop()
    poll = QTimer()
    poll.timeout.connect(lambda: loop.quit() if predicate() else None)
    deadline = QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(loop.quit)
    poll.start(5)
    deadline.start(3000)
    loop.exec()
    poll.stop()
    assert predicate()


def test_overlapping_tasks_report_completion_failure_and_discard(window):
    started, release = Event(), Event()

    def slow():
        started.set()
        assert release.wait(3)
        return "manuscript secret"

    first = FunctionWorker(slow)
    failed = FunctionWorker(lambda: (_ for _ in ()).throw(ValueError("private text")))
    stale = FunctionWorker(lambda: "ignored")
    a = window._track_ai_activity(first, "First")
    b = window._track_ai_activity(failed, "Second")
    c = window._track_ai_activity(stale, "Third", current=lambda: False)
    for worker in (first, failed, stale):
        window._track_worker(worker)
        window.thread_pool.start(worker)
    wait_until(started.is_set)
    wait_until(lambda: b.state == "failed" and c.state == "discarded")
    assert a.state == "running"
    release.set()
    wait_until(lambda: a.state == "completed")
    output = "\n".join(window.ai_activity.list.item(i).text() for i in range(window.ai_activity.list.count()))
    assert "manuscript secret" not in output
    assert "private text" not in output


def test_cancellation_remains_pending_until_worker_returns(window):
    started, release = Event(), Event()

    def slow():
        started.set()
        assert release.wait(3)

    worker = FunctionWorker(slow)
    item = window._track_ai_activity(worker, "Cancelable", cancel=worker.cancel)
    window._track_worker(worker)
    window.thread_pool.start(worker)
    wait_until(started.is_set)
    window.ai_activity.list.setCurrentRow(window.ai_activity.activities.index(item))
    window.ai_activity.cancel_button.click()
    wait_until(lambda: item.state == "cancelling")
    assert not window.ai_activity.cancel_button.isEnabled()
    release.set()
    wait_until(lambda: item.state == "cancelled")


def test_activity_history_is_bounded_without_discarding_running_tasks(window):
    panel = window.ai_activity
    running = panel.add("Running")
    panel.set_state(running, "running")
    for number in range(105):
        item = panel.add(f"Task {number}")
        panel.set_state(item, "completed")
    assert running in panel.activities
    assert len(panel.activities) == 100


def test_failed_task_can_retry_without_reusing_result(window):
    calls = []
    panel = window.ai_activity
    item = panel.add("Generation", retry=lambda: calls.append("fresh request"))
    panel.set_state(item, "failed")
    panel.list.setCurrentRow(panel.activities.index(item))
    assert panel.retry_button.isEnabled()
    panel.retry_button.click()
    assert calls == ["fresh request"]


def test_closing_window_cancels_inflight_activity(window):
    started, release = Event(), Event()

    def slow():
        started.set()
        assert release.wait(3)
        return "ignored"

    worker = FunctionWorker(slow)
    item = window._track_ai_activity(worker, "Closing task", cancel=worker.cancel)
    window._track_worker(worker)
    window.show()
    window.thread_pool.start(worker)
    wait_until(started.is_set)
    window.close()
    release.set()
    wait_until(lambda: item.state == "cancelled")
