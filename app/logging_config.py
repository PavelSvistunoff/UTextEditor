"""Configure application logging to logs/utexteditor.log.

Creates logs/ directory in the repository root and a rotating file handler.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(level: int = logging.WARNING) -> None:
    """Keep application logging minimal and failure-focused.

    Only warnings and errors are written to disk by default; noisy informational
    payloads such as successful Ollama requests stay at debug level and are not
    emitted unless the application is intentionally run with a lower threshold.
    """
    repo_root = Path(__file__).resolve().parents[1].parent
    logs_dir = repo_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "utexteditor.log"

    logger = logging.getLogger()
    logger.setLevel(level)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    # Keep terminal output quiet; store the important events in the log file.
    fh = RotatingFileHandler(str(log_file), maxBytes=10 * 1024 * 1024, backupCount=1, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("utexteditor.ai").setLevel(level)
    logging.getLogger("utexteditor.ai").propagate = True
