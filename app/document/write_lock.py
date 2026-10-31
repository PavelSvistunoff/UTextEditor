"""In-process coordination for fingerprinted document and manifest writes."""

from threading import RLock

TEXT_WRITE_LOCK = RLock()
