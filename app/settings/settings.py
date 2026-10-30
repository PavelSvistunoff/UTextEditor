"""Persistent application settings with safe MVP defaults."""

from dataclasses import dataclass, asdict, field
import platform
import os
import math
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from app.ai.prompts import DEFAULT_AI_ROLE, DEFAULT_COMPLETION_TEMPLATE
from app.ai.prompts import completion_prompt


@dataclass
class AppSettings:
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "gemma4:12b"
    ai_role: str = DEFAULT_AI_ROLE
    completion_template: str = DEFAULT_COMPLETION_TEMPLATE
    ai_enabled: bool = True
    completion_enabled: bool = True
    automatic_project_context: bool = True
    completion_debounce_ms: int = 500
    maximum_suggestion_length: int = 100
    temperature: float = 0.2
    context_size: int = 2048
    spellcheck_enabled: bool = True
    automatic_spellcheck: bool = True
    language: str = "Auto"
    ui_language: str = "system"
    font_family: str = "Monospace"
    font_size: int = 12
    tab_width: int = 4
    word_wrap: bool = False
    line_numbers: bool = False
    autosave_enabled: bool = True
    autosave_idle_ms: int = 2000
    recent_projects: list[str] = field(default_factory=list)
    recent_files: list[str] = field(default_factory=list)
    # Empty in existing settings until the first disclosure is accepted.
    ai_context_consent_host: str = ""

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
        return base / "settings.yaml"

    def save(self, path: Path | str | None = None) -> None:
        self.validated()
        target = Path(path) if path is not None else self._default_settings_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        serialized = yaml.safe_dump(asdict(self), allow_unicode=True, sort_keys=False)
        temporary = target.with_name(f".{target.name}.tmp")
        try:
            temporary.write_text(serialized, encoding="utf-8")
            temporary.replace(target)
        except OSError:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    @classmethod
    def load(cls, path: Path | str | None = None) -> "AppSettings":
        target = Path(path) if path is not None else cls._default_settings_path()
        if not target.exists():
            if path is not None:
                return cls()
            legacy_target = target.with_name("settings.json")
            if not legacy_target.exists():
                return cls()
            target = legacy_target
        try:
            with target.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            if not isinstance(data, dict):
                return cls()
            known = {field for field in cls.__dataclass_fields__}
            settings = cls(**{key: value for key, value in data.items() if key in known})
            return settings.validated()
        except (OSError, UnicodeError, yaml.YAMLError, TypeError, ValueError):
            return cls()

    def validated(self) -> "AppSettings":
        defaults = type(self)()
        self.ollama_host = self._string(self.ollama_host, defaults.ollama_host, 2048).rstrip("/")
        if not self._valid_host(self.ollama_host):
            self.ollama_host = defaults.ollama_host
        if isinstance(self.ai_context_consent_host, str):
            self.ai_context_consent_host = self.ai_context_consent_host.strip().rstrip("/")
        if (
            not isinstance(self.ai_context_consent_host, str)
            or len(self.ai_context_consent_host) > 2048
            or not self._valid_host(self.ai_context_consent_host)
        ):
            self.ai_context_consent_host = ""
        self.ollama_model = self._string(self.ollama_model, defaults.ollama_model, 256)
        self.ai_role = self._string(self.ai_role, defaults.ai_role, 4000)
        self.completion_template = self._string(self.completion_template, defaults.completion_template, 8000)
        if "{context}" not in self.completion_template:
            self.completion_template = defaults.completion_template
        else:
            try:
                completion_prompt("", "Auto", self.completion_template)
            except ValueError:
                self.completion_template = defaults.completion_template
        candidate_language = self._string(self.language, defaults.language, 32)
        normalized_language = candidate_language.strip()
        self.language = {"auto": "Auto", "english": "English", "ukrainian": "Ukrainian"}.get(normalized_language.lower(), defaults.language)
        if self.language not in {"Auto", "English", "Ukrainian"}:
            self.language = defaults.language
        if not isinstance(self.ui_language, str) or self.ui_language not in {"system", "en", "uk"}:
            self.ui_language = defaults.ui_language
        self.font_family = self._string(self.font_family, defaults.font_family, 128) or defaults.font_family
        self.font_size = self._bounded_int(self.font_size, 8, 32, defaults.font_size)
        self.tab_width = self._bounded_int(self.tab_width, 2, 8, defaults.tab_width)
        self.word_wrap = self._bool(self.word_wrap, defaults.word_wrap)
        self.line_numbers = self._bool(self.line_numbers, defaults.line_numbers)
        self.autosave_enabled = self._bool(self.autosave_enabled, defaults.autosave_enabled)
        self.autosave_idle_ms = self._bounded_int(
            self.autosave_idle_ms, 250, 60000, defaults.autosave_idle_ms
        )
        recent_projects: list[str] = []
        seen_projects: set[str] = set()
        if isinstance(self.recent_projects, list):
            for project_path in self.recent_projects:
                if not isinstance(project_path, str) or not project_path.strip():
                    continue
                clean_path = project_path.strip()[:4096]
                if not Path(clean_path).is_absolute() or clean_path in seen_projects:
                    continue
                seen_projects.add(clean_path)
                recent_projects.append(clean_path)
                if len(recent_projects) == 10:
                    break
        self.recent_projects = recent_projects
        recent_files: list[str] = []
        seen_files: set[str] = set()
        if isinstance(self.recent_files, list):
            for file_path in self.recent_files:
                if (not isinstance(file_path, str) or not file_path.strip()
                        or len(file_path) > 4096 or "\x00" in file_path):
                    continue
                clean_path = file_path
                if not Path(clean_path).is_absolute() or clean_path in seen_files:
                    continue
                seen_files.add(clean_path)
                recent_files.append(clean_path)
                if len(recent_files) == 10:
                    break
        self.recent_files = recent_files
        self.ai_enabled = self._bool(self.ai_enabled, defaults.ai_enabled)
        self.completion_enabled = self._bool(self.completion_enabled, defaults.completion_enabled)
        self.automatic_project_context = self._bool(self.automatic_project_context, defaults.automatic_project_context)
        self.spellcheck_enabled = self._bool(self.spellcheck_enabled, defaults.spellcheck_enabled)
        self.automatic_spellcheck = self._bool(self.automatic_spellcheck, defaults.automatic_spellcheck)
        self.completion_debounce_ms = self._bounded_int(self.completion_debounce_ms, 100, 5000, defaults.completion_debounce_ms)
        self.maximum_suggestion_length = self._bounded_int(self.maximum_suggestion_length, 1, 10000, defaults.maximum_suggestion_length)
        self.context_size = self._bounded_int(self.context_size, 64, 65536, defaults.context_size)
        try:
            temperature = float(self.temperature) if not isinstance(self.temperature, bool) else math.nan
        except (TypeError, ValueError, OverflowError):
            temperature = math.nan
        self.temperature = temperature if math.isfinite(temperature) and 0 <= temperature <= 2 else defaults.temperature
        return self

    def has_ai_context_consent(self, destination: str) -> bool:
        """Consent applies only to the exact validated destination approved."""
        return bool(
            self.ai_context_consent_host
            and isinstance(destination, str)
            and destination.rstrip("/") == self.ai_context_consent_host
        )

    @staticmethod
    def _string(value, fallback: str, maximum: int) -> str:
        return value.strip()[:maximum] if isinstance(value, str) and value.strip() else fallback

    @staticmethod
    def _bool(value, fallback: bool) -> bool:
        return value if isinstance(value, bool) else fallback

    @staticmethod
    def _bounded_int(value, minimum: int, maximum: int, fallback: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            return fallback
        return value

    @staticmethod
    def _valid_host(value: str) -> bool:
        try:
            parsed = urlsplit(value)
            return (
                parsed.scheme in {"http", "https"}
                and bool(parsed.hostname)
                and parsed.username is None
                and parsed.password is None
                and parsed.path in {"", "/"}
                and not parsed.query
                and not parsed.fragment
                and (parsed.port is None or 1 <= parsed.port <= 65535)
            )
        except ValueError:
            return False
