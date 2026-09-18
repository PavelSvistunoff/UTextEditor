"""Data models shared by AI services and the UI."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Suggestion:
    start: int
    end: int
    replacement: str
    type: str = "spelling"
    explanation: str = ""
    original_text: str = ""
    revision: int = 0
    source_text: str = ""


@dataclass(frozen=True)
class CompletionRequest:
    request_id: int
    document_id: str
    revision: int
    cursor_position: int
    selection: tuple[int, int]
    context: str
    language: str
