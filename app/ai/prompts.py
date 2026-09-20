"""Centralized prompts for structured local AI operations."""

import re

DEFAULT_AI_ROLE = "You are a medium. Predict what I will say next."
DEFAULT_COMPLETION_TEMPLATE = (
    "You are an inline text completion engine.\n"
    "Language: {language}.\n"
    "Generate only a concise continuation of the text. Do not repeat existing text, explain, or add unrelated content.\n\n"
    "Text:\n{context}\nContinuation:"
)


def resolve_language(language: str, text: str) -> str:
    """Resolve Auto mode using a simple content-language heuristic."""
    if language and language != "Auto":
        return language
    if re.search(r"[а-яёїієґА-ЯЁЇІЄҐ]", text):
        return "Ukrainian"
    return "English"


def detect_language(language: str, text: str) -> str:
    return resolve_language(language, text)


def _resolved_language(language: str, text: str) -> str:
    return resolve_language(language, text)


def completion_prompt(
    context: str,
    language: str,
    template: str = DEFAULT_COMPLETION_TEMPLATE,
) -> str:
    """Render a user-configured template without evaluating arbitrary code."""
    resolved_language = resolve_language(language, context)
    try:
        return template.format(context=context, language=resolved_language)
    except (IndexError, KeyError, ValueError) as exc:
        raise ValueError("Completion template may only use {context} and {language} placeholders") from exc


def spellcheck_prompt(text: str, language: str) -> str:
    resolved_language = resolve_language(language, text)
    return (
        "You are a strict spellchecker and grammar fixer.\n"
        f"Language: {resolved_language}.\n"
        "Return only valid JSON, not markdown fences, not prose, and no explanation outside the JSON.\n"
        "Output a JSON array of objects with exactly these keys: start, end, replacement, type, explanation.\n"
        "Use Python string offsets from the supplied text. Each object must look like: "
        "{\"start\": 0, \"end\": 4, \"replacement\": \"word\", \"type\": \"spelling\", \"explanation\": \"Possible spelling error.\"}.\n"
        "If the text is already correct, return [].\n"
        "Do not return an empty JSON object {}.\n\n"
        f"Text:\n{text}"
    )
