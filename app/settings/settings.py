"""Persistent application settings with safe MVP defaults."""

from dataclasses import dataclass

from app.ai.prompts import DEFAULT_AI_ROLE, DEFAULT_COMPLETION_TEMPLATE


@dataclass
class AppSettings:
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "gemma4:12b"
    ai_role: str = DEFAULT_AI_ROLE
    completion_template: str = DEFAULT_COMPLETION_TEMPLATE
    ai_enabled: bool = True
    completion_enabled: bool = True
    completion_debounce_ms: int = 500
    maximum_suggestion_length: int = 100
    temperature: float = 0.2
    context_size: int = 2048
    spellcheck_enabled: bool = True
    automatic_spellcheck: bool = True
    language: str = "Auto"
