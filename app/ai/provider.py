"""Provider abstraction used by services, independent of Qt."""

from typing import Protocol

from .models import Suggestion
from .prompts import DEFAULT_AI_ROLE, DEFAULT_COMPLETION_TEMPLATE


class AIProvider(Protocol):
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
    ) -> str:
        """Generate locally without retaining the prompt/response in diagnostics."""
        ...

    def check_spelling(self, text: str, language: str) -> list[Suggestion]:
        ...

    def check_connection(self) -> bool:
        ...
