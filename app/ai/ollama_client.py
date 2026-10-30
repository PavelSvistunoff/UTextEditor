"""Small Ollama HTTP client. It is deliberately free of Qt dependencies."""

import json
import logging
import time
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError
from urllib import request

from .models import Suggestion
from .prompts import DEFAULT_AI_ROLE, DEFAULT_COMPLETION_TEMPLATE, completion_prompt, spellcheck_prompt
from .validation import parse_suggestions

logger = logging.getLogger("utexteditor.ai")
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_ERROR_BODY_BYTES = 64 * 1024


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

    def _post(
        self,
        path: str,
        payload: dict,
        *,
        observe: bool = True,
        timeout: float | None = None,
    ) -> dict:
        if observe:
            self._observe("Request", path, payload)
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(f"{self.host}{path}", data=body, headers={"Content-Type": "application/json"})
        start = time.time()
        try:
            with request.urlopen(req, timeout=self.timeout if timeout is None else timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ValueError("Ollama response exceeded the 16 MiB size limit")
                result = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            body = exc.read(MAX_ERROR_BODY_BYTES).decode("utf-8", errors="replace")
            if "model" in body.lower() and "not found" in body.lower():
                message = f"Ollama model '{self.model}' was not found. Pull it with `ollama pull {self.model}` or choose another model in AI Settings."
            else:
                message = f"Ollama returned HTTP {exc.code} while contacting {path}."
            duration = time.time() - start
            if observe:
                self._observe("Error", path, {"message": message, "duration": duration})
            logger.error("Ollama request failed %s %s (%.3fs): HTTP %s", path, self.model, duration, exc.code)
            raise OllamaError(message) from exc
        except (OSError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            duration = time.time() - start
            if observe:
                self._observe("Error", path, {"message": str(exc), "duration": duration})
            logger.error("Ollama request failed %s %s (%.3fs): %s", path, self.model, duration, exc)
            raise OllamaError(str(exc)) from exc
        duration = time.time() - start
        if not isinstance(result, dict):
            if observe:
                self._observe("Error", path, {"message": "Ollama returned an invalid response", "duration": duration})
            logger.error("Ollama returned invalid response for %s %s (%.3fs)", path, self.model, duration)
            raise OllamaError("Ollama returned an invalid response")
        if observe:
            self._observe("Response", path, result)
        logger.info("Ollama %s %s completed in %.3fs", path, self.model, duration)
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

    def generate(
        self,
        prompt: str,
        *,
        role: str = DEFAULT_AI_ROLE,
        maximum_tokens: int = 300,
        temperature: float = 0.2,
        timeout: float | None = None,
    ) -> str:
        return self._generate(
            prompt,
            role=role,
            maximum_tokens=maximum_tokens,
            temperature=temperature,
            observe=True,
            timeout=timeout,
            json_mode=False,
        )

    def generate_stream(self, prompt: str, *, on_chunk: Callable[[str], None],
                        is_cancelled: Callable[[], bool], role: str = DEFAULT_AI_ROLE,
                        maximum_tokens: int = 300, temperature: float = 0.2) -> str:
        """Read bounded NDJSON generation output, emitting provisional text in the caller's thread."""
        path = "/api/chat"
        payload = {"model": self.model, "messages": [{"role": "system", "content": role},
                   {"role": "user", "content": prompt}], "stream": True, "think": False,
                   "options": {"num_predict": maximum_tokens, "temperature": temperature}}
        self._observe("Request", path, payload)
        req = request.Request(f"{self.host}{path}", data=json.dumps(payload).encode("utf-8"),
                              headers={"Content-Type": "application/json"})
        parts: list[str] = []
        total = 0
        start = time.time()
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                while not is_cancelled():
                    line = response.readline(MAX_RESPONSE_BYTES + 1)
                    if is_cancelled():
                        break
                    if not line:
                        raise ValueError("Ollama stream ended before completion")
                    total += len(line)
                    if total > MAX_RESPONSE_BYTES:
                        raise ValueError("Ollama response exceeded the 16 MiB size limit")
                    value = json.loads(line.decode("utf-8"))
                    if not isinstance(value, dict) or not isinstance(value.get("done"), bool):
                        raise ValueError("Ollama returned an invalid streaming response")
                    message = value.get("message", {})
                    content = message.get("content", "") if isinstance(message, dict) else None
                    if not isinstance(content, str) or value.get("error"):
                        raise ValueError("Ollama returned an invalid streaming response")
                    if content:
                        parts.append(content)
                        on_chunk(content)
                    if is_cancelled():
                        break
                    if value["done"]:
                        result = "".join(parts)
                        self._observe("Response", path, {"message": {"content": result}, "done": True})
                        return result
        except (OSError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._observe("Error", path, {"message": str(exc), "duration": time.time() - start})
            raise OllamaError(str(exc)) from exc
        self._observe("Cancelled", path, {"duration": time.time() - start})
        return ""

    def generate_private(
        self,
        prompt: str,
        *,
        role: str = DEFAULT_AI_ROLE,
        maximum_tokens: int = 300,
        temperature: float = 0.2,
        timeout: float | None = None,
        json_mode: bool = False,
    ) -> str:
        """Generate a local AI response while keeping the interaction visible in diagnostics."""
        # Private here means the request is internal to the app workflow, not that it
        # should be hidden from the debug UI. The debug dialog is intentionally a full
        # trace of Ollama traffic for troubleshooting.
        return self._generate(
            prompt,
            role=role,
            maximum_tokens=maximum_tokens,
            temperature=temperature,
            observe=True,
            timeout=timeout,
            json_mode=json_mode,
        )

    def _generate(
        self,
        prompt: str,
        *,
        role: str,
        maximum_tokens: int,
        temperature: float,
        observe: bool,
        timeout: float | None,
        json_mode: bool,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": role},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": False,
            "options": {"num_predict": maximum_tokens, "temperature": temperature},
        }
        if json_mode:
            payload["format"] = "json"
        response = self._post(
            "/api/chat",
            payload,
            observe=observe,
            timeout=timeout,
        )
        message = response.get("message")
        result = message.get("content") if isinstance(message, dict) else None
        if not isinstance(result, str):
            raise OllamaError("Ollama returned no generated text")
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
