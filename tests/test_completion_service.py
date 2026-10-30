from app.ai.completion_service import CompletionService, build_context, complete_project_scene


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


def test_context_honours_paragraph_boundaries_at_and_across_window_edge() -> None:
    assert build_context("old\n\nnew text", 13, maximum_characters=9) == "new text"
    assert build_context("old\n\nnew text", 13, maximum_characters=8) == "new text"
    assert build_context("old\n\nnew text", 13, maximum_characters=4) == "text"
    assert build_context("old\n\nnew\n\nlast", 14, maximum_characters=12) == "last"


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


def test_project_completion_uses_open_notes_and_bounds_disk_notes():
    class Project:
        def read_note(self, note_id):
            assert note_id == "disk"
            return "x" * 20000

    provider = FakeProvider()
    result = complete_project_scene(
        CompletionService(provider), Project(),
        (("open", "People", "character"), ("disk", "World", "general")),
        {"open": "Unsaved detail"}, "Character: Mara", "The story", "English",
    )
    context = provider.calls[0][0]
    assert result == " continuation"
    assert "Character: Mara" in context and "Unsaved detail" in context
    assert context.endswith("Text to continue:\nThe story")
    assert "x" * (10000 - len("character: People\nUnsaved detail") - len("general: World\n")) in context
