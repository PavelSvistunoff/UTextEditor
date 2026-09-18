"""Centralized prompts for structured local AI operations."""

DEFAULT_AI_ROLE = "You are a medium. Predict what I will say next."
DEFAULT_COMPLETION_TEMPLATE = (
    "You are an inline text completion engine.\n"
    "Language: {language}.\n"
    "Generate only a concise continuation of the text. Do not repeat existing text, explain, or add unrelated content.\n\n"
    "Text:\n{context}\nContinuation:"
)


def completion_prompt(
    context: str,
    language: str,
    template: str = DEFAULT_COMPLETION_TEMPLATE,
) -> str:
    """Render a user-configured template without evaluating arbitrary code."""
    try:
        return template.format(context=context, language=language)
    except (IndexError, KeyError, ValueError) as exc:
        raise ValueError("Completion template may only use {context} and {language} placeholders") from exc


def spellcheck_prompt(text: str, language: str) -> str:
    return (
        "Check the text for spelling and basic grammar errors.\n"
        f"Language: {language}.\n"
        "Return only a JSON array of objects with start, end, replacement, type, and explanation. "
        "Offsets are Python string offsets in the supplied text. Return [] when there are no errors.\n\n"
        f"Text:\n{text}"
    )
