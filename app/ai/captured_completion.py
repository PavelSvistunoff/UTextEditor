"""Send the reviewed prompt unchanged, with source verification on both sides."""

from collections.abc import Callable, Mapping

from app.ai.provider import AIProvider
from app.project.rag_context import CapturedContext
from app.project.rag_sources import BufferText
from app.ai.completion_service import STALE_PROJECT_CONTEXT
from app.project import ProjectError


def generate_captured_completion(
    provider: AIProvider, captured: CapturedContext, buffers: Mapping[str, BufferText], *,
    temperature: float, is_cancelled: Callable[[], bool] = lambda: False,
    on_chunk: Callable[[str], None] | None = None,
) -> str | object:
    """Generate from one frozen request; streamed chunks remain provisional.

    Consumers must discard the preview on cancellation or a stale final result.
    Source verification surrounds generation rather than performing disk I/O for
    every token. Both modes send the same role, prompt and output reserve.
    """
    def current() -> bool:
        if is_cancelled():
            return False
        try:
            captured.verify_current(buffers)
        except (OSError, UnicodeError, ProjectError):
            return False
        return True

    if not current():
        return STALE_PROJECT_CONTEXT
    try:
        options = dict(role=captured.role, maximum_tokens=captured.budget.output_tokens,
                       temperature=temperature, require_full_context=True)
        if on_chunk is None:
            result = provider.generate_private(captured.prompt, **options)
        else:
            def provisional(chunk: str) -> None:
                if not isinstance(chunk, str):
                    raise ValueError("Completion stream chunks must be text.")
                if not is_cancelled():
                    on_chunk(chunk)

            result = provider.generate_stream(captured.prompt, on_chunk=provisional,
                                              is_cancelled=is_cancelled, **options)
    except Exception:
        # A late provider failure belongs to its original source snapshot.
        if not current():
            return STALE_PROJECT_CONTEXT
        raise
    if not current():
        return STALE_PROJECT_CONTEXT
    if not isinstance(result, str):
        raise ValueError("Completion response must be text.")
    return result
