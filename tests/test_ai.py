from app.ai.completion_service import build_context
from app.ai.models import Suggestion
from app.ai.validation import parse_suggestions, valid_suggestion


def test_context_prefers_current_paragraph_and_is_bounded() -> None:
    text = "old paragraph\n\n" + "x" * 5000
    context = build_context(text, len(text))
    assert "old paragraph" not in context
    assert len(context) <= 4000


def test_structured_suggestions_are_validated() -> None:
    source = "This sentense is wrong."
    payload = '[{"start": 5, "end": 13, "replacement": "sentence", "type": "spelling"}, {"start": 99, "end": 100, "replacement": "x"}]'
    suggestions = parse_suggestions(payload, source, 4)
    assert len(suggestions) == 1
    assert suggestions[0].original_text == "sentense"
    assert valid_suggestion(suggestions[0], source, 4)
    assert not valid_suggestion(suggestions[0], source + "!", 4)


def test_invalid_json_is_safe() -> None:
    assert parse_suggestions("not json", "text", 0) == []


def test_suggestion_range_must_be_inside_snapshot() -> None:
    suggestion = Suggestion(0, 5, "x", original_text="other", revision=1)
    assert not valid_suggestion(suggestion, "text", 1)


def test_parser_rejects_wrong_field_types_and_invalid_ranges() -> None:
    payload = [
        {"start": -1, "end": 1, "replacement": "x"},
        {"start": 0, "end": 8, "replacement": "x"},
        {"start": 0, "end": 1, "replacement": 10},
        {"start": 0, "end": 1, "replacement": "x", "type": 2},
    ]

    assert parse_suggestions(payload, "text", 0) == []


def test_parser_accepts_wrapped_suggestions_payload() -> None:
    suggestions = parse_suggestions(
        {"suggestions": [{"start": 0, "end": 4, "replacement": "word", "explanation": None}]},
        "text",
        2,
    )

    assert suggestions == [Suggestion(0, 4, "word", explanation="None", original_text="text", revision=2, source_text="text")]
