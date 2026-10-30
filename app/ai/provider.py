"""Provider abstraction used by services, independent of Qt."""

from collections.abc import Callable
from typing import Protocol

from .models import Suggestion
from .prompts import DEFAULT_AI_ROLE, DEFAULT_COMPLETION_TEMPLATE


class AIProvider(Protocol):
    def generate_stream(self, prompt: str, *, on_chunk: Callable[[str], None],
                        is_cancelled: Callable[[], bool], role: str = DEFAULT_AI_ROLE,
                        maximum_tokens: int = 300, temperature: float = 0.2) -> str:
        ...

    def complete(
        self,
        context: str,
        language: str,
        *,
        role: str = DEFAULT_AI_ROLE,
        template: str = DEFAULT_COMPLETION_TEMPLATE,
        maximum_tokens: int = 100,
        temperature: float = 0.2,
    ) -> str:
        ...

    def generate(
        self,
        prompt: str,
        *,
        role: str = DEFAULT_AI_ROLE,
        maximum_tokens: int = 300,
        temperature: float = 0.2,
        timeout: float | None = None,
    ) -> str:
        ...

    def generate_private(
        self,
        prompt: str,
        *,
        role: str = DEFAULT_AI_ROLE,
        maximum_tokens: int = 300,
        temperature: float = 0.2,
        timeout: float | None = None,
        json_mode: bool = False,
    ) -> str:
        """Generate locally while keeping the request/response visible to diagnostics."""
        ...

    def check_spelling(self, text: str, language: str) -> list[Suggestion]:
        ...

    def check_connection(self) -> bool:
        ...
