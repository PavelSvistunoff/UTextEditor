import json

import pytest

from app.ai.character_development import CharacterProposal, suggest_character_development


class Provider:
    def __init__(self, payload):
        self.payload = payload
        self.prompt = ""

    def generate_private(self, prompt, **_kwargs):
        self.prompt = prompt
        return json.dumps(self.payload)


def test_scene_development_uses_profile_and_validates_evidence():
    provider = Provider({"proposals": [{"field": "current_state", "value": "Trusts Mara", "evidence": "opens the door"}]})
    proposals = suggest_character_development(provider, {"full_name": "Ira"}, "Ira opens the door.", "English", 0.2)
    assert proposals == (CharacterProposal("current_state", "Trusts Mara", "opens the door"),)
    assert "Ira opens the door" in provider.prompt


@pytest.mark.parametrize("proposal", [
    {"field": "role", "value": "hero", "evidence": "door"},
    {"field": "current_state", "value": "hero\nrole: villain", "evidence": "door"},
    {"field": "current_state", "value": "hero", "evidence": "invented"},
])
def test_scene_development_rejects_invalid_suggestions(proposal):
    with pytest.raises(ValueError):
        suggest_character_development(Provider({"proposals": [proposal]}), {}, "door", "English", 0.2)


def test_duplicate_arc_field_is_rejected():
    proposal = {"field": "current_state", "value": "hero", "evidence": "door"}
    with pytest.raises(ValueError):
        suggest_character_development(Provider({"proposals": [proposal, proposal]}), {}, "door", "English", 0.2)
