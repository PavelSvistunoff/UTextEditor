import json

import pytest

from app.ai.character_profile import suggest_character_fields


class Provider:
    def __init__(self, result):
        self.result = result
        self.prompt = ""
        self.options = {}

    def generate_private(self, prompt, **kwargs):
        self.prompt = prompt
        self.options = kwargs
        return self.result


def test_suggestions_include_profile_and_validate_structured_fields():
    provider = Provider(json.dumps({"description": "A watchmaker", "goals": "Find the key | active | 2", "knowledge": "knows: The gate is locked", "arc": "current_state: Afraid"}))
    result = suggest_character_fields(provider, {"full_name": "Mara", "description": "", "goals": "", "knowledge": "", "arc": ""}, "English", 0.2)
    assert result["description"] == "A watchmaker"
    assert "Mara" in provider.prompt
    assert provider.options["timeout"] == 300
    assert provider.options["json_mode"] is True
    assert provider.options["maximum_tokens"] == 8192


def test_suggestions_accept_fenced_json():
    assert suggest_character_fields(Provider('```json\n{"description":"A writer"}\n```'), {"description": ""}, "English", 0.2) == {"description": "A writer"}


@pytest.mark.parametrize("response", [
    "not json", '{}', '{"full_name":"Overwrite"}', '{"description":42}',
    '{"goals":"Find | invalid | 7"}', '{"knowledge":"unknown: secret"}',
    '{"arc":"invalid: state"}',
])
def test_suggestions_reject_invalid_or_populated_fields(response):
    with pytest.raises(ValueError):
        suggest_character_fields(Provider(response), {"full_name": "Mara", "description": "", "goals": "", "knowledge": "", "arc": ""}, "English", 0.2)


@pytest.mark.parametrize("field,text,expected", [
    ("primary_motivation", "Вона шукає свій дім і прагне знайти родину.", "Ukrainian"),
    ("primary_motivation", "The writer is looking for the key to her home.", "English"),
    ("knowledge", "knows: Вона знає, що її родина чекає вдома.", "Ukrainian"),
    ("goals", "Знайти свій дім і родину | active | 3 | Вона шукає підтримки.", "Ukrainian"),
])
def test_auto_profile_language_is_resolved_before_the_model_request(field, text, expected):
    provider = Provider('{"description":"An idea"}')
    suggest_character_fields(provider, {field: text, "description": ""}, "Auto", 0.2)
    assert f"Language: {expected}\n" in provider.prompt
    assert "Language: Auto" not in provider.prompt


@pytest.mark.parametrize("selection,fallback,profile,expected", [
    ("Auto", "Ukrainian", {"full_name": "Мара", "role": "supporting character"}, "Ukrainian"),
    ("Auto", "English", {"full_name": "Mara"}, "English"),
    ("Auto", "Ukrainian", {"primary_motivation": "The writer is looking for a key."}, "English"),
    ("Auto", "English", {"primary_motivation": "Вона шукає свій дім і родину."}, "Ukrainian"),
    ("English", "Ukrainian", {"primary_motivation": "Вона шукає свій дім і родину."}, "English"),
    ("Ukrainian", "English", {"primary_motivation": "The writer is looking for a key."}, "Ukrainian"),
    ("Auto", "Ukrainian", {"primary_motivation": "Он ищет свой дом и потерянную семью."}, "Ukrainian"),
    ("Auto", "Ukrainian", {"primary_motivation": "The writer is looking for a key.", "needs": "Вона шукає свій дім і родину."}, "Ukrainian"),
    ("Auto", "English", {"primary_motivation": "The writer is looking for a key.", "needs": "Вона шукає свій дім і родину."}, "English"),
    ("Auto", "English", {"arc": "current_state: Вона шукає свій дім і родину."}, "Ukrainian"),
])
def test_profile_suggestions_use_supported_language_with_explicit_precedence(selection, fallback, profile, expected):
    provider = Provider('{"description":"An idea"}')
    fields = {**profile, "description": ""}
    result = suggest_character_fields(provider, fields, selection, 0.2, fallback_language=fallback)
    assert result == {"description": "An idea"}
    assert f"Language: {expected}\n" in provider.prompt
    assert "Language: Auto" not in provider.prompt
    assert "Do not write Russian" in provider.prompt
    assert f"in {expected} only, never in Russian" in provider.options["role"]
    assert "goal status codes" in provider.prompt and "specified English form" in provider.prompt
    assert fields == {**profile, "description": ""}


@pytest.mark.parametrize("selection,fallback", [("Russian", "English"), ("French", "Ukrainian"), ("Auto", "Russian")])
def test_profile_suggestions_reject_unsupported_language_before_request(selection, fallback):
    provider = Provider('{"description":"An idea"}')
    with pytest.raises(ValueError, match="English or Ukrainian"):
        suggest_character_fields(provider, {"description": ""}, selection, 0.2, fallback_language=fallback)
    assert provider.prompt == ""
