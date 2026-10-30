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
