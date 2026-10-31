"""In-process coordination for fingerprinted manuscript writes."""

from threading import Lock

TEXT_WRITE_LOCK = Lock()
