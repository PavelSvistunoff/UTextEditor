"""Centralized prompts for structured local AI operations."""

import re

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
        return template.format(context=context, language=_resolved_language(language, context))
    except (IndexError, KeyError, ValueError) as exc:
        raise ValueError("Completion template may only use {context} and {language} placeholders") from exc


def detect_language(text: str) -> str:
    """Detect clear English or Ukrainian signals and preserve ambiguity as Auto."""
    value = (text or "").strip()
    if not value:
        return "Auto"

    has_ukrainian = bool(re.search(r"[їієґЇІЄҐ]", value))
    has_cyrillic = bool(re.search(r"[а-яёіїєґА-ЯЁІЇЄҐ]", value))
    has_latin = bool(re.search(r"[A-Za-z]", value))
    # Other alphabets or Russian-specific letters do not provide reliable
    # evidence for either supported language, including mixed-script input.
    if re.search(r"[ыэёъЫЭЁЪ]", value) or re.search(
        r"[^\W\d_A-Za-zа-яёіїєґА-ЯЁІЇЄҐ]", value
    ):
        return "Auto"
    if len(value) < 8:
        return "Auto"

    if has_ukrainian and not has_latin:
        ukrainian_words = re.findall(r"\b[А-Яа-яЇїІіЄєҐґ']+\b", value)
        if len(ukrainian_words) >= 2:
            return "Ukrainian"
        return "Auto"

    if has_cyrillic and has_latin:
        return "Auto"

    english_words = re.findall(r"\b(?:the|and|is|are|you|that|this|with|for|to|of|in|it|was|have|has|from|on|at|as|be|by|not|we|they|their|there|here|which|would|should)\b", value.lower())
    ukrainian_words = re.findall(r"\b(?:це|цей|я|ти|ми|ви|що|як|де|але|тому|сво|коли|все|так|для|з|на|у|і|а)\b", value.lower())

    if has_latin and len(value) >= 8 and len(english_words) >= 2 and not ukrainian_words:
        return "English"
    if has_cyrillic and len(value) >= 8 and len(ukrainian_words) >= 2 and not english_words:
        return "Ukrainian"
    return "Auto"


def _resolved_language(language: str, text: str) -> str:
    if language and language != "Auto":
        return language
    return detect_language(text)


def spellcheck_prompt(text: str, language: str) -> str:
    resolved_language = _resolved_language(language, text)
    return (
        "You are a strict spellchecker and grammar fixer.\n"
        f"Language: {resolved_language}.\n"
        "Return only valid JSON, not markdown fences, not prose, and no explanation outside the JSON.\n"
        "Output a JSON array of objects with start, end, replacement, type, and explanation; original_text is optional.\n"
        "Use Python Unicode code-point offsets into the exact supplied text. Each object must look like: "
        "{\"start\": 0, \"end\": 4, \"replacement\": \"word\", \"type\": \"spelling\", \"explanation\": \"Possible spelling error.\", \"original_text\": \"wrng\"}.\n"
        "If the text is already correct, return [].\n"
        "Do not return an empty JSON object {}.\n\n"
        f"Text:\n{text}"
    )
