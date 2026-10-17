import logging

from app.logging_config import configure_logging


def test_configure_logging_sets_info_level_and_message_format(monkeypatch):
    configured = {}

    def capture_basic_config(**kwargs):
        configured.update(kwargs)

    monkeypatch.setattr(logging, "basicConfig", capture_basic_config)

    configure_logging()

    assert configured["level"] == logging.INFO
    assert "%(name)s" in configured["format"]
    assert "%(message)s" in configured["format"]
