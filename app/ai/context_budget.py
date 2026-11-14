"""Explicit request budgets; UTF-8 byte estimates are not tokenizer counts."""

from dataclasses import dataclass

MAX_CONTEXT_TOKENS = 1_048_576


class ContextBudgetError(ValueError):
    """The captured request cannot fit the configured budget without omissions."""


@dataclass(frozen=True)
class ContextBudget:
    context_tokens: int
    output_tokens: int
    safety_tokens: int = 256
    message_overhead_tokens: int = 32

    def __post_init__(self) -> None:
        for value in (self.context_tokens, self.output_tokens):
            if type(value) is not int or value <= 0:
                raise ValueError("Context and output token budgets must be positive integers.")
        for value in (self.safety_tokens, self.message_overhead_tokens):
            if type(value) is not int or value < 0:
                raise ValueError("Budget overheads must be nonnegative integers.")

    def remaining_tokens(self, role: str, prompt: str) -> int:
        """Reserve response and framing space before adding optional passages.

        One token per UTF-8 byte deliberately overestimates ordinary prose.
        It is not a universal tokenizer bound: model-specific chat templates
        and special tokens can differ. Server capacity checks remain necessary.
        Count the fully rendered prompt, including instructions and wrappers.
        """
        estimated_input = len(role.encode("utf-8")) + len(prompt.encode("utf-8"))
        return (self.context_tokens - self.output_tokens - self.safety_tokens
                - self.message_overhead_tokens - estimated_input)

    def require_fit(self, role: str, prompt: str) -> None:
        if self.remaining_tokens(role, prompt) < 0:
            raise ContextBudgetError(
                "Estimated complete request exceeds the configured context token budget "
                "including response reserve and safety margin. Increase the context window "
                "or reduce the source material; no content was truncated. "
                "This UTF-8 byte-based estimate is not an exact token count."
            )
