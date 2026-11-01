from dataclasses import replace

import pytest

from app.ai.models import Suggestion
from app.ai.spellcheck_service import SpellcheckService


class FakeProvider:
    def __init__(self, result: object) -> None:
        self.result = result

    def check_spelling(self, text: str, language: str) -> object:
        return self.result


def test_service_revisions_and_validates_provider_suggestions() -> None:
    source = "A sentense."
    provider = FakeProvider([Suggestion(2, 10, "sentence", original_text="sentense", revision=2)])

    result = SpellcheckService(provider).check(source, "English", revision=7)

    assert result == [Suggestion(2, 10, "sentence", original_text="sentense", revision=7)]


def test_service_rejects_malformed_or_unverifiable_provider_results() -> None:
    source = "A sentense."
    invalid = Suggestion(2, 10, "sentence", original_text="different")

    assert SpellcheckService(FakeProvider([invalid, object()])).check(source, "English", 1) == []
    assert SpellcheckService(FakeProvider({"not": "a list"})).check(source, "English", 1) == []


def test_service_can_parse_legacy_json_provider_result() -> None:
    provider = FakeProvider('[{"start": 2, "end": 10, "replacement": "sentence"}]')

    result = SpellcheckService(provider).check("A sentense.", "English", revision=3)

    assert result[0].original_text == "sentense"
    assert result[0].revision == 3


@pytest.mark.parametrize("fields", [
    {"start": "0"}, {"start": True}, {"start": -1}, {"end": None},
    {"end": False}, {"end": 20}, {"end": 0}, {"replacement": None},
    {"replacement": "x" * 2001}, {"explanation": "x" * 1001},
    {"explanation": []}, {"type": 2}, {"original_text": []}, {"source_text": []},
])
def test_typed_provider_suggestions_are_validated_before_sorting(fields) -> None:
    valid = Suggestion(0, 3, "the", original_text="teh")
    malformed = replace(valid, **fields)
    result = SpellcheckService(FakeProvider([malformed, valid])).check("teh cat", "English", 7)
    assert result == [replace(valid, revision=7)]


def test_typed_provider_limits_and_nonoverlap_match_json_review_contract() -> None:
    source = "teh " * 205
    provider = FakeProvider([
        Suggestion(index, index + 3, "the", explanation="x" * 1000)
        for index in reversed(range(0, len(source), 4))
    ])
    result = SpellcheckService(provider).check(source, "English", 7)
    assert len(result) == 200
    assert [item.start for item in result] == list(range(0, 800, 4))
    assert all(item.revision == 7 for item in result)
    provider.result = [Suggestion(0, 3, "x" * 2000), Suggestion(0, 3, "the")]
    assert SpellcheckService(provider).check("teh", "English", 7) == [
        Suggestion(0, 3, "x" * 2000, revision=7)
    ]
