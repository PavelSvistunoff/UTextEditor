import sys
import types
from pathlib import Path

import app.main as app_main


def test_main_logs_and_continues_when_optional_setup_fails(monkeypatch) -> None:
    class DummyApp:
        def __init__(self, *args, **kwargs):
            pass

        def setFont(self, *_args, **_kwargs):
            pass

        def setWindowIcon(self, *_args, **_kwargs):
            raise RuntimeError("icon failed")

        def exec(self):
            return 0

    class DummyWindow:
        def __init__(self, **_kwargs):
            pass

        def show(self):
            pass

    bad_logging = types.ModuleType("app.logging_config")

    def boom() -> None:
        raise RuntimeError("logging failed")

    bad_logging.configure_logging = boom
    monkeypatch.setitem(sys.modules, "app.logging_config", bad_logging)
    monkeypatch.setattr(app_main, "configure_application_font", lambda _app: None)
    monkeypatch.setattr(app_main, "QApplication", DummyApp)
    monkeypatch.setattr(app_main, "QIcon", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(app_main, "MainWindow", DummyWindow)
    monkeypatch.setattr(app_main, "RecoveryStore", lambda: object())
    monkeypatch.setattr(app_main, "WritingGoalStore", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(
        app_main.AppSettings,
        "_default_settings_path",
        staticmethod(lambda: Path("/tmp/settings.yaml")),
    )

    assert app_main.main() == 0
