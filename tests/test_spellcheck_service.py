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
