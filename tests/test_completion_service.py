from app.ai.completion_service import CompletionService, build_context


class FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def complete(self, context: str, language: str, **kwargs: object) -> str:
        self.calls.append((context, language, kwargs))
        return " continuation"

    def check_spelling(self, text: str, language: str) -> list[object]:
        return []

    def check_connection(self) -> bool:
        return True


def test_context_clamps_cursor_and_honours_character_limit() -> None:
    assert build_context("abcdef", -5) == ""
    assert build_context("abcdef", 99) == "abcdef"
    assert build_context("abcdef", 3, maximum_characters=0) == ""
    assert build_context("abcdefgh", 8, maximum_characters=3) == "fgh"


def test_completion_service_delegates_options_to_provider() -> None:
    provider = FakeProvider()

    result = CompletionService(provider).complete(
        "draft",
        "English",
        role="Custom role",
        template="Context: {context}",
        maximum_tokens=12,
        temperature=0.5,
    )

    assert result == " continuation"
    assert provider.calls == [
        (
            "draft",
            "English",
            {"role": "Custom role", "template": "Context: {context}", "maximum_tokens": 12, "temperature": 0.5},
        )
    ]
