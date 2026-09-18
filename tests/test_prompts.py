from app.ai.prompts import completion_prompt, spellcheck_prompt
import pytest


def test_completion_prompt_includes_language_and_context() -> None:
    prompt = completion_prompt("Start here", "Ukrainian")

    assert "Language: Ukrainian." in prompt
    assert "Start here" in prompt
    assert "Generate only a concise continuation" in prompt


def test_spellcheck_prompt_requires_machine_readable_offsets() -> None:
    prompt = spellcheck_prompt("Mistkae", "English")

    assert "JSON array" in prompt
    assert "Python string offsets" in prompt
    assert "Mistkae" in prompt


def test_completion_prompt_supports_context_template_placeholders() -> None:
    assert completion_prompt("draft", "English", "[{language}] {context}") == "[English] draft"


def test_completion_prompt_rejects_unknown_template_placeholders() -> None:
    with pytest.raises(ValueError, match="placeholders"):
        completion_prompt("draft", "English", "{unknown}")
