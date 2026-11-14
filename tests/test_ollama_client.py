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


def test_stream_generation_delivers_bounded_provisional_chunks():
    client = OllamaClient(model="test-model")
    response = MagicMock()
    response.__enter__.return_value = response
    response.readline.side_effect = [
        b'{"message":{"content":"Hello"},"done":false}\n',
        b'{"message":{"content":" world"},"done":true}\n',
    ]
    chunks = []
    with patch("app.ai.ollama_client.request.urlopen", return_value=response) as urlopen:
        assert client.generate_stream("prompt", on_chunk=chunks.append, is_cancelled=lambda: False) == "Hello world"
    assert chunks == ["Hello", " world"]
    assert json.loads(urlopen.call_args.args[0].data)["stream"] is True


def test_stream_generation_discards_cancelled_and_malformed_results():
    client = OllamaClient()
    response = MagicMock()
    response.__enter__.return_value = response
    response.readline.return_value = b'{"message":{"content":"partial"},"done":true}\n'
    cancelled = False
    chunks = []

    def receive(text):
        nonlocal cancelled
        chunks.append(text)
        cancelled = True

    with patch("app.ai.ollama_client.request.urlopen", return_value=response):
        assert client.generate_stream("prompt", on_chunk=receive, is_cancelled=lambda: cancelled) == ""
    assert chunks == ["partial"]
    response.readline.return_value = b'{"message":{}}\n'
    with patch("app.ai.ollama_client.request.urlopen", return_value=response):
        with pytest.raises(OllamaError, match="invalid streaming"):
            client.generate_stream("prompt", on_chunk=lambda _: None, is_cancelled=lambda: False)


def test_stream_generation_rejects_oversized_response(monkeypatch):
    monkeypatch.setattr("app.ai.ollama_client.MAX_RESPONSE_BYTES", 12)
    response = MagicMock()
    response.__enter__.return_value = response
    response.readline.return_value = b'x' * 13
    with patch("app.ai.ollama_client.request.urlopen", return_value=response):
        with pytest.raises(OllamaError, match="size limit"):
            OllamaClient().generate_stream("prompt", on_chunk=lambda _: None, is_cancelled=lambda: False)


def test_full_context_stream_disables_truncation_without_changing_request_text():
    response = MagicMock()
    response.__enter__.return_value = response
    response.readline.return_value = b'{"message":{"content":"Draft"},"done":true}\n'
    with patch("app.ai.ollama_client.request.urlopen", return_value=response) as urlopen:
        result = OllamaClient().generate_stream("Frozen context", role="Frozen role",
            maximum_tokens=80, temperature=.3, on_chunk=lambda text: None,
            is_cancelled=lambda: False, require_full_context=True)
    payload = json.loads(urlopen.call_args.args[0].data)
    assert result == "Draft"
    assert payload["truncate"] is payload["shift"] is False
    assert payload["messages"] == [{"role": "system", "content": "Frozen role"},
                                   {"role": "user", "content": "Frozen context"}]


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


def test_oversized_response_is_rejected_before_json_parsing(monkeypatch) -> None:
    import app.ai.ollama_client as ollama_client

    monkeypatch.setattr(ollama_client, "MAX_RESPONSE_BYTES", 32)
    response = response_with({})
    response.read.side_effect = lambda size: b"x" * size
    client = OllamaClient()

    with patch("app.ai.ollama_client.request.urlopen", return_value=response):
        with pytest.raises(OllamaError, match="size limit"):
            client.generate("prompt")

    response.read.assert_called_once_with(33)


def test_connection_failure_is_false() -> None:
    client = OllamaClient()
    with patch("app.ai.ollama_client.request.urlopen", side_effect=OSError("offline")):
        assert not client.check_connection()


def test_missing_model_error_is_actionable() -> None:
    client = OllamaClient(model="missing-model")
    error = HTTPError("http://localhost", 404, "Not Found", {}, BytesIO(b"model missing-model not found"))
    error.read = MagicMock(wraps=error.read)
    with patch("app.ai.ollama_client.request.urlopen", side_effect=error):
        with pytest.raises(OllamaError, match="ollama pull missing-model"):
            client.complete("Hello", "English")
    error.read.assert_called_once_with(64 * 1024)


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


def test_private_generation_still_records_its_interaction_in_diagnostics() -> None:
    events: list[tuple[str, str, dict[str, object]]] = []
    client = OllamaClient(
        interaction_observer=lambda event, path, details: events.append((event, path, details))
    )

    with patch(
        "app.ai.ollama_client.request.urlopen",
        return_value=response_with({"message": {"content": "private analysis"}}),
    ):
        assert client.generate_private("private manuscript text") == "private analysis"

    assert events[0][0:2] == ("Request", "/api/chat")
    assert "private manuscript text" in json.dumps(events[0][2])
    assert events[1] == ("Response", "/api/chat", {"message": {"content": "private analysis"}})


def test_private_generation_can_use_a_longer_operation_timeout() -> None:
    client = OllamaClient(timeout=30)
    with patch(
        "app.ai.ollama_client.request.urlopen",
        return_value=response_with({"message": {"content": "long result"}}),
    ) as urlopen:
        assert client.generate_private(
            "write this scene",
            maximum_tokens=900,
            timeout=300,
        ) == "long result"

    assert urlopen.call_args.kwargs["timeout"] == 300


def test_private_generation_can_request_json_mode() -> None:
    client = OllamaClient()
    with patch(
        "app.ai.ollama_client.request.urlopen",
        return_value=response_with({"message": {"content": '{"description":"Writer"}'}}),
    ) as urlopen:
        client.generate_private("suggest fields", json_mode=True)

    payload = json.loads(urlopen.call_args.args[0].data.decode())
    assert payload["format"] == "json"
    assert payload["think"] is False


def test_complete_reference_requests_disable_input_truncation_and_context_shifting():
    client = OllamaClient()
    with patch("app.ai.ollama_client.request.urlopen", return_value=response_with({"message": {"content": "Draft"}})) as urlopen:
        client.generate_private("All references", require_full_context=True)
    payload = json.loads(urlopen.call_args.args[0].data)
    assert payload["truncate"] is False
    assert payload["shift"] is False
    assert payload["messages"][1]["content"] == "All references"


def test_context_window_failure_does_not_expose_note_contents():
    client = OllamaClient()
    error = HTTPError("http://localhost:11434/api/chat", 400, "Bad Request", {}, BytesIO(b'context length exceeded: PRIVATE NOTE'))
    with patch("app.ai.ollama_client.request.urlopen", side_effect=error):
        with pytest.raises(OllamaError, match="context window") as caught:
            client.generate_private("All references", require_full_context=True)
    assert "PRIVATE NOTE" not in str(caught.value)


def model_metadata(capacity=8192):
    return {"model_info": {"general.architecture": "test", "test.context_length": capacity}}


@pytest.mark.parametrize("operation", ["generate", "generate_private", "complete", "check_spelling", "stream"])
def test_explicit_window_checks_model_capacity_and_budgets_every_chat_path(operation):
    client = OllamaClient(context_length=4096)
    stream = MagicMock()
    stream.__enter__.return_value = stream
    stream.readline.return_value = b'{"message":{"content":"done"},"done":true}\n'
    reply = stream if operation == "stream" else response_with({"message": {"content": "[]"}})
    with patch("app.ai.ollama_client.request.urlopen", side_effect=[response_with(model_metadata()), reply]) as urlopen:
        if operation == "complete":
            client.complete("text", "English")
        elif operation == "check_spelling":
            client.check_spelling("text", "English")
        elif operation == "stream":
            client.generate_stream("text", on_chunk=lambda _: None, is_cancelled=lambda: False)
        else:
            getattr(client, operation)("text")
    requests = [call.args[0] for call in urlopen.call_args_list]
    assert [req.full_url.rsplit("/", 1)[1] for req in requests] == ["show", "chat"]
    assert json.loads(requests[0].data) == {"model": client.model}
    payload = json.loads(requests[1].data)
    assert payload["options"]["num_ctx"] == 4096
    assert payload["truncate"] is False and payload["shift"] is False


@pytest.mark.parametrize("metadata", [
    {}, {"model_info": []}, model_metadata(True), model_metadata(0), model_metadata("8192"),
    {"model_info": {"general.architecture": "other", "test.context_length": 8192}},
])
def test_unknown_model_capacity_never_guesses_from_model_name(metadata):
    with patch("app.ai.ollama_client.request.urlopen", return_value=response_with(metadata)) as urlopen:
        with pytest.raises(OllamaError, match="did not report model context capacity"):
            OllamaClient(model="gemma4:12b", context_length=4096).generate("text")
    assert urlopen.call_count == 1


def test_window_above_model_capacity_is_not_silently_clamped():
    with patch("app.ai.ollama_client.request.urlopen", return_value=response_with(model_metadata(2048))) as urlopen:
        with pytest.raises(OllamaError, match="exceeds the model's reported capacity"):
            OllamaClient(context_length=4096).generate("text")
    assert urlopen.call_count == 1


@pytest.mark.parametrize("prompt,role,output", [
    ("x" * 4096, "role", 100), ("корисні дані " * 300, "role", 100),
    ("text", "role" * 1100, 100), ("text", "role", 4000),
])
def test_estimated_overflow_refuses_before_any_network_call(prompt, role, output):
    with patch("app.ai.ollama_client.request.urlopen") as urlopen:
        with pytest.raises(OllamaError, match="Estimated complete request"):
            OllamaClient(context_length=4096).generate(prompt, role=role, maximum_tokens=output)
    urlopen.assert_not_called()


@pytest.mark.parametrize("endpoint", ["show", "chat"])
def test_unsupported_context_request_is_reported_without_retry_or_raw_body(endpoint):
    error = HTTPError("http://localhost/api/" + endpoint, 400, "Bad Request", {},
                      BytesIO(b"unsupported num_ctx: PRIVATE MANUSCRIPT"))
    responses = [error] if endpoint == "show" else [response_with(model_metadata()), error]
    with patch("app.ai.ollama_client.request.urlopen", side_effect=responses) as urlopen:
        with pytest.raises(OllamaError) as caught:
            OllamaClient(context_length=4096).generate("text")
    assert "PRIVATE MANUSCRIPT" not in str(caught.value)
    assert urlopen.call_count == len(responses)
    if endpoint == "chat":
        assert "not retried" in str(caught.value)


def test_capacity_is_rechecked_when_server_replaces_a_model_tag():
    responses = [response_with(model_metadata()), response_with({"message": {"content": "first"}}),
                 response_with(model_metadata(1024))]
    with patch("app.ai.ollama_client.request.urlopen", side_effect=responses) as urlopen:
        client = OllamaClient(context_length=4096)
        assert client.generate("text") == "first"
        with pytest.raises(OllamaError, match="reported capacity"):
            client.generate("text")
    assert urlopen.call_count == 3


def test_explicit_connection_test_sends_window_without_manuscript():
    responses = [response_with(model_metadata()), response_with({"done": True})]
    with patch("app.ai.ollama_client.request.urlopen", side_effect=responses) as urlopen:
        assert OllamaClient(context_length=4096).check_connection() is True
    payload = json.loads(urlopen.call_args.args[0].data)
    assert payload["options"] == {"num_predict": 1, "num_ctx": 4096}
    assert payload["prompt"] == ""
    assert payload["truncate"] is False and payload["shift"] is False


def test_explicit_connection_test_reports_rejected_option_as_unavailable():
    error = HTTPError("http://localhost/api/generate", 400, "Bad Request", {}, BytesIO(b"unknown num_ctx"))
    with patch("app.ai.ollama_client.request.urlopen", side_effect=[response_with(model_metadata()), error]) as urlopen:
        assert OllamaClient(context_length=4096).check_connection() is False
    assert urlopen.call_count == 2


def test_cancelled_explicit_stream_does_not_query_model_or_send_prompt():
    with patch("app.ai.ollama_client.request.urlopen") as urlopen:
        assert OllamaClient(context_length=4096).generate_stream(
            "text", on_chunk=lambda _: pytest.fail("cancelled chunk"), is_cancelled=lambda: True,
        ) == ""
    urlopen.assert_not_called()


def test_stream_cancelled_during_capacity_check_does_not_send_chat():
    cancelled = iter([False, True])
    with patch("app.ai.ollama_client.request.urlopen", return_value=response_with(model_metadata())) as urlopen:
        result = OllamaClient(context_length=4096).generate_stream(
            "text", on_chunk=lambda _: pytest.fail("cancelled chunk"),
            is_cancelled=lambda: next(cancelled),
        )
    assert result == "" and urlopen.call_count == 1


def test_stream_unsupported_window_is_actionable_without_retry_or_body_leak():
    error = HTTPError("http://localhost/api/chat", 400, "Bad Request", {},
                      BytesIO(b"unsupported num_ctx: PRIVATE MANUSCRIPT"))
    with patch("app.ai.ollama_client.request.urlopen", side_effect=[response_with(model_metadata()), error]) as urlopen:
        with pytest.raises(OllamaError, match="not retried") as caught:
            OllamaClient(context_length=4096).generate_stream(
                "text", on_chunk=lambda _: None, is_cancelled=lambda: False,
            )
    assert "PRIVATE MANUSCRIPT" not in str(caught.value)
    assert urlopen.call_count == 2


@pytest.mark.parametrize("length", [-1, True, 1.5, 1048577])
def test_invalid_context_length_is_rejected(length):
    with pytest.raises(ValueError, match="Context length"):
        OllamaClient(context_length=length)
