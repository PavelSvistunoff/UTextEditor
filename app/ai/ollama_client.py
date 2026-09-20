"""Small Ollama HTTP client. It is deliberately free of Qt dependencies."""

import json
from collections.abc import Callable
from typing import Any
from urllib import request

from .models import Suggestion
from .prompts import DEFAULT_AI_ROLE, DEFAULT_COMPLETION_TEMPLATE, completion_prompt, spellcheck_prompt
from .validation import parse_suggestions


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "gemma4:12b",
        timeout: float = 30.0,
        interaction_observer: Callable[[str, str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.interaction_observer = interaction_observer

    def _observe(self, event: str, path: str, details: dict[str, Any]) -> None:
        if self.interaction_observer is None:
            return
        try:
            self.interaction_observer(event, path, details)
        except RuntimeError as exc:
            message = str(exc)
            if "Signal source has been deleted" in message:
                return
            raise

    def _post(self, path: str, payload: dict) -> dict:
        self._observe("Request", path, payload)
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(f"{self.host}{path}", data=body, headers={"Content-Type": "application/json"})
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (OSError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._observe("Error", path, {"message": str(exc)})
            raise OllamaError(str(exc)) from exc
        if not isinstance(result, dict):
            self._observe("Error", path, {"message": "Ollama returned an invalid response"})
            raise OllamaError("Ollama returned an invalid response")
        self._observe("Response", path, result)
        return result

    def check_connection(self) -> bool:
        try:
            self._post("/api/generate", {"model": self.model, "prompt": "", "stream": False, "options": {"num_predict": 1}})
            return True
        except OllamaError:
            return False

    def complete(
        self,
        context: str,
        language: str,
        *,
        role: str = DEFAULT_AI_ROLE,
        template: str = DEFAULT_COMPLETION_TEMPLATE,
        maximum_tokens: int = 100,
        temperature: float = 0.2,
    ) -> str:
        response = self._post(
            "/api/chat",
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": role},
                    {"role": "user", "content": completion_prompt(context, language, template)},
                ],
                "stream": False,
                "think": False,
                "options": {"num_predict": maximum_tokens, "temperature": temperature},
            },
        )
        message = response.get("message")
        result = message.get("content") if isinstance(message, dict) else None
        if not isinstance(result, str):
            raise OllamaError("Ollama returned no completion")
        # Leading whitespace is meaningful for inline completions: removing it
        # would join a word at the cursor to the first suggested word.
        return result

    def check_spelling(self, text: str, language: str) -> list[Suggestion]:
        response = self._post(
            "/api/chat",
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a strict spellcheck engine. Return only valid JSON that matches the user's requested schema. "
                            "Never return markdown fences or an empty JSON object."
                        ),
                    },
                    {"role": "user", "content": spellcheck_prompt(text, language)},
                ],
                "stream": False,
                "think": False,
                "format": "json",
                "options": {"temperature": 0.0, "num_predict": 256},
            },
        )
        message = response.get("message")
        raw = message.get("content", "[]") if isinstance(message, dict) else "[]"
        return parse_suggestions(raw, text, 0)
