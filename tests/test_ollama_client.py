import json
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from app.ai.ollama_client import OllamaClient, OllamaError


def response_with(payload: object) -> MagicMock:
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode()
    response.__enter__.return_value = response
    return response


def test_complete_sends_a_non_streaming_request_and_returns_text() -> None:
    client = OllamaClient(model="test-model")
    with patch("app.ai.ollama_client.request.urlopen", return_value=response_with({"message": {"content": " done "}})) as urlopen:
        assert client.complete(
            "Hello",
            "English",
            role="Custom role",
            template="Complete: {context} ({language})",
            maximum_tokens=9,
            temperature=0.4,
        ) == " done "

    request = urlopen.call_args.args[0]
    payload = json.loads(request.data.decode())
    assert payload["model"] == "test-model"
    assert payload["stream"] is False
    assert payload["think"] is False
    assert payload["options"] == {"num_predict": 9, "temperature": 0.4}
    assert request.full_url.endswith("/api/chat")
    assert payload["messages"][0] == {"role": "system", "content": "Custom role"}
    assert payload["messages"][1]["role"] == "user"
    assert payload["messages"][1]["content"] == "Complete: Hello (English)"


@pytest.mark.parametrize("payload", [[], {"message": {"content": 12}}])
def test_invalid_ollama_response_is_reported_as_a_safe_error(payload: object) -> None:
    client = OllamaClient()
    with patch("app.ai.ollama_client.request.urlopen", return_value=response_with(payload)):
        with pytest.raises(OllamaError):
            client.complete("Hello", "English")


def test_connection_failure_is_false() -> None:
    client = OllamaClient()
    with patch("app.ai.ollama_client.request.urlopen", side_effect=OSError("offline")):
        assert not client.check_connection()


def test_missing_model_error_is_actionable() -> None:
    client = OllamaClient(model="missing-model")
    error = HTTPError("http://localhost", 404, "Not Found", {}, BytesIO(b"model missing-model not found"))
    with patch("app.ai.ollama_client.request.urlopen", side_effect=error):
        with pytest.raises(OllamaError, match="ollama pull missing-model"):
            client.complete("Hello", "English")


def test_spellcheck_uses_chat_json_mode_without_thinking() -> None:
    client = OllamaClient()
    with patch(
        "app.ai.ollama_client.request.urlopen",
        return_value=response_with({"message": {"content": "[]"}}),
    ) as urlopen:
        assert client.check_spelling("Привіт", "Ukrainian") == []

    payload = json.loads(urlopen.call_args.args[0].data.decode())
    assert urlopen.call_args.args[0].full_url.endswith("/api/chat")
    assert payload["format"] == "json"
    assert payload["think"] is False
    assert payload["options"] == {"temperature": 0.0, "num_predict": 256}
    assert any(item["role"] == "system" for item in payload["messages"])


def test_interaction_observer_receives_request_and_response() -> None:
    events: list[tuple[str, str, dict[str, object]]] = []
    client = OllamaClient(interaction_observer=lambda event, path, details: events.append((event, path, details)))

    with patch("app.ai.ollama_client.request.urlopen", return_value=response_with({"message": {"content": "done"}})):
        client.complete("Hello", "English")

    assert events[0][0:2] == ("Request", "/api/chat")
    assert "messages" in events[0][2]
    assert events[1] == ("Response", "/api/chat", {"message": {"content": "done"}})
