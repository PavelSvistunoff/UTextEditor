"""Persistent application settings with safe MVP defaults."""

from dataclasses import dataclass, asdict
import json
import platform
import os
from pathlib import Path

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

    @staticmethod
    def _default_settings_path() -> Path:
        home = Path.home()
        system = platform.system()
        if system == "Windows":
            base = Path(os.environ.get("APPDATA", home)) / "UTextEditor"
        elif system == "Darwin":
            base = home / "Library" / "Application Support" / "UTextEditor"
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")) / "utexteditor"
        base.mkdir(parents=True, exist_ok=True)
        return base / "settings.json"

    def save(self, path: Path | str | None = None) -> None:
        target = Path(path) if path is not None else self._default_settings_path()
        try:
            with target.open("w", encoding="utf-8") as fh:
                json.dump(asdict(self), fh, ensure_ascii=False, indent=2)
        except OSError:
            # Do not raise on disk errors; settings persistence is best-effort.
            pass

    @classmethod
    def load(cls, path: Path | str | None = None) -> "AppSettings":
        target = Path(path) if path is not None else cls._default_settings_path()
        if not target.exists():
            return cls()
        try:
            with target.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return cls(**data)
        except Exception:
            return cls()
