"""Embedding contract and bounded, normalized vector validation."""

from collections.abc import Sequence
from dataclasses import dataclass
import math
from typing import Protocol

MAX_EMBEDDING_DIMENSIONS = 4096
MAX_EMBEDDING_BATCH = 8
MAX_EMBEDDING_INPUT_BYTES = 8192
MAX_EMBEDDING_BATCH_BYTES = 32768
EMBEDDING_FORMAT_VERSION = 1


class EmbeddingError(RuntimeError):
    """Embedding unavailable or invalid; callers may explicitly fall back."""


@dataclass(frozen=True)
class EmbeddingIdentity:
    host: str
    model: str
    digest: str
    dimensions: int

    def __post_init__(self) -> None:
        if any(not isinstance(value, str) or not value or len(value) > 2048
               for value in (self.host, self.model, self.digest)):
            raise EmbeddingError("Embedding model identity is incomplete.")
        if type(self.dimensions) is not int or not 1 <= self.dimensions <= MAX_EMBEDDING_DIMENSIONS:
            raise EmbeddingError("Embedding dimensions exceed the supported bound.")


class EmbeddingProvider(Protocol):
    def embedding_identity(self) -> EmbeddingIdentity: ...

    def embed(self, texts: tuple[str, ...], identity: EmbeddingIdentity
              ) -> tuple[tuple[float, ...], ...]: ...


def normalized_vector(value: Sequence[float], dimensions: int) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != dimensions:
        raise EmbeddingError("Embedding vector dimensions do not match the model.")
    try:
        valid = all(type(item) in (int, float) and math.isfinite(item) for item in value)
    except OverflowError:
        valid = False
    if not valid:
        raise EmbeddingError("Embedding vector contains invalid values.")
    norm = math.hypot(*value)
    if not math.isfinite(norm) or norm <= 0:
        raise EmbeddingError("Embedding vector has invalid magnitude.")
    return tuple(item / norm for item in value)


def embedding_input(model: str, text: str, *, query: bool) -> str:
    """Versioned retrieval-task formatting for the evaluated model families."""
    family = model.split(":", 1)[0]
    if family == "embeddinggemma":
        return ("task: search result | query: " if query else "title: none | text: ") + text
    if family == "qwen3-embedding":
        return ("Instruct: Retrieve relevant story passages for the query.\nQuery: " if query else "") + text
    # Other user-selected embedding models use raw text, never a generation prompt.
    return text
