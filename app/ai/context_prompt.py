"""Frozen, predictable prompt layout for budgeted captured context."""

from dataclasses import dataclass
from string import Formatter


@dataclass(frozen=True)
class ContextPrompt:
    role: str
    template: str = "{context}"
    language: str = "Auto"

    def __post_init__(self) -> None:
        if any(not isinstance(value, str) for value in (self.role, self.template, self.language)):
            raise ValueError("Prompt role, template and language must be strings.")
        context_count = 0
        for _literal, field, spec, conversion in Formatter().parse(self.template):
            if field is None:
                continue
            if field not in {"context", "language"} or spec or conversion:
                raise ValueError("Captured prompts support only plain {context} and {language} placeholders.")
            context_count += field == "context"
        if not context_count:
            raise ValueError("Captured prompt template must include {context}.")

    def render(self, context: str) -> str:
        # Resolve Auto from author input before capture, never from retrieved data.
        return self.template.format(context=context, language=self.language)
