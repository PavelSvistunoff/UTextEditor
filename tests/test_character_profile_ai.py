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


@pytest.mark.parametrize("knowledge,goals", [
    ("knows: Факт;conceals: Таємниця;believes: Припущення", "Знайти дім | active | 3 | Пошук підтримки"),
    ("knows: Факт\nconceals: Таємниця", "Знайти дім | active | 3 | Перша мета | Допомогти друзям | blocked | 2 | Друга мета"),
])
def test_model_arc_typo_and_joined_records_are_normalized_before_review(knowledge, goals):
    provider = Provider(json.dumps({
        "description": "Ідея персонажа",
        "arc": "initial_state: Самотній\nturnings_points: Зустріч із друзями; важливе рішення",
        "knowledge": knowledge,
        "goals": goals,
    }))
    result = suggest_character_fields(provider, {"description": "", "arc": "", "knowledge": "", "goals": ""}, "Ukrainian", 0.2)
    assert result["description"] == "Ідея персонажа"
    assert result["arc"] == "initial_state: Самотній\nturning_points: Зустріч із друзями; важливе рішення"
    assert ";conceals:" not in result["knowledge"]
    assert result["knowledge"].splitlines()[0] == "knows: Факт"
    if "blocked" in goals:
        assert result["goals"].splitlines() == [
            "Знайти дім | active | 3 | Перша мета", "Допомогти друзям | blocked | 2 | Друга мета",
        ]
    else:
        assert result["knowledge"].splitlines() == ["knows: Факт", "conceals: Таємниця", "believes: Припущення"]


@pytest.mark.parametrize("arc", [
    "turning_point: Подія", "unknown: Подія", "розвиток: Подія",
    "turning_points: Перша подія\nturnings_points: Інша подія",
])
def test_arc_normalization_does_not_guess_unknown_or_duplicate_fields(arc):
    with pytest.raises(ValueError):
        suggest_character_fields(Provider(json.dumps({"arc": arc})), {"arc": ""}, "Ukrainian", 0.2)


def test_structured_normalization_retains_semicolons_and_pipes_in_prose():
    knowledge = "knows: Уміє слухати; зберігає спокій\nconceals: Таємниця; згадка про друзів"
    goals = "Знайти дім | active | 3 | Варіант A | Варіант B"
    result = suggest_character_fields(
        Provider(json.dumps({"knowledge": knowledge, "goals": goals})),
        {"knowledge": "", "goals": ""}, "Ukrainian", 0.2,
    )
    assert result == {"knowledge": knowledge, "goals": goals}


def test_normalized_goal_text_still_obeys_field_size_limit():
    # Adding canonical record spacing must not bypass the validated output cap.
    goals = "|".join(["x", "active", "3", "n"] * 150)
    assert len(goals) <= 2000
    with pytest.raises(ValueError, match="Invalid suggestion for goals"):
        suggest_character_fields(Provider(json.dumps({"goals": goals})), {"goals": ""}, "English", 0.2)
