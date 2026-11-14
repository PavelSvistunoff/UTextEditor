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
from .context_budget import ContextBudget, ContextBudgetError, MAX_CONTEXT_TOKENS
from .embeddings import (EmbeddingError, EmbeddingIdentity, MAX_EMBEDDING_BATCH,
                         MAX_EMBEDDING_INPUT_BYTES, MAX_EMBEDDING_BATCH_BYTES, normalized_vector)

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
        *,
        context_length: int = 0,
    ) -> None:
        if type(context_length) is not int or not 0 <= context_length <= MAX_CONTEXT_TOKENS:
            raise ValueError(f"Context length must be 0 (server default) or up to {MAX_CONTEXT_TOKENS} tokens.")
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.interaction_observer = interaction_observer
        self.context_length = context_length

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
            message = self._http_error_message(exc, path, payload)
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

    def _http_error_message(self, error: HTTPError, path: str, payload: dict) -> str:
        """Classify failures without echoing a body that may contain manuscript text."""
        body = error.read(MAX_ERROR_BODY_BYTES).decode("utf-8", errors="replace").lower()
        if "model" in body and "not found" in body:
            return (f"Ollama model '{self.model}' was not found. Pull it with `ollama pull {self.model}` "
                    "or choose another model in AI Settings.")
        if error.code in {400, 413, 422} and payload.get("options", {}).get("num_ctx"):
            return ("Ollama rejected the explicitly configured context request. "
                    "Check server/model support for num_ctx and available memory; "
                    "the request was not retried with a smaller window.")
        if error.code in {400, 413} and payload.get("truncate") is False and "context" in body:
            return ("The complete request exceeds or cannot use the model context window. "
                    "Increase Ollama's context length or reduce project reference material; "
                    "no context was intentionally omitted.")
        return f"Ollama returned HTTP {error.code} while contacting {path}."

    def embedding_identity(self) -> EmbeddingIdentity:
        """Resolve a local model digest; do not pull models or trust mutable tags."""
        try:
            req = request.Request(f"{self.host}/api/tags")
            with request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise EmbeddingError("Embedding model metadata exceeds its size limit.")
            data = json.loads(raw)
            models = data.get("models") if isinstance(data, dict) else None
            if not isinstance(models, list):
                raise EmbeddingError("Embedding model inventory is malformed.")
            name = self.model if ":" in self.model else self.model + ":latest"
            model = next((item for item in models if isinstance(item, dict)
                          and item.get("name") in {self.model, name}), None)
            if model is None:
                raise EmbeddingError("The selected embedding model is not installed; no download was attempted.")
            metadata = self._post("/api/show", {"model": self.model})
            capabilities = metadata.get("capabilities")
            if not isinstance(capabilities, list) or "embedding" not in capabilities:
                raise EmbeddingError("The selected model does not declare embedding support.")
            info = metadata.get("model_info", {})
            architecture = info.get("general.architecture")
            return EmbeddingIdentity(self.host, model["name"], model.get("digest"),
                                     info.get(f"{architecture}.embedding_length"))
        except (OSError, ValueError, TypeError, AttributeError, OllamaError) as exc:
            raise EmbeddingError("Could not verify embedding model identity.") from exc

    def embed(self, texts: tuple[str, ...], identity: EmbeddingIdentity
              ) -> tuple[tuple[float, ...], ...]:
        if (not isinstance(texts, tuple) or not 1 <= len(texts) <= MAX_EMBEDDING_BATCH
                or any(not isinstance(text, str) or not text or len(text.encode("utf-8")) > MAX_EMBEDDING_INPUT_BYTES
                       for text in texts)
                or sum(len(text.encode("utf-8")) for text in texts) > MAX_EMBEDDING_BATCH_BYTES):
            raise EmbeddingError("Embedding batch exceeds its input limits.")
        if self.embedding_identity() != identity:
            raise EmbeddingError("Embedding model changed before the batch.")
        try:
            result = self._post("/api/embed", {"model": identity.model, "input": list(texts), "truncate": False})
        except OllamaError as exc:
            raise EmbeddingError("Embedding request failed; no model or destination was changed.") from exc
        values = result.get("embeddings")
        if (result.get("model") not in {self.model, identity.model}
                or not isinstance(values, list) or len(values) != len(texts)):
            raise EmbeddingError("Embedding response is incomplete or belongs to another model.")
        vectors = tuple(normalized_vector(value, identity.dimensions) for value in values)
        if self.embedding_identity() != identity:
            raise EmbeddingError("Embedding model changed during the batch.")
        return vectors

    def check_connection(self) -> bool:
        try:
            payload = {"model": self.model, "prompt": "", "stream": False, "options": {"num_predict": 1}}
            if self.context_length:
                self._check_context_capacity()
                payload["options"]["num_ctx"] = self.context_length
                payload["truncate"] = False
                payload["shift"] = False
            self._post("/api/generate", payload)
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
            self._chat_payload(
                completion_prompt(context, language, template),
                role=role, maximum_tokens=maximum_tokens, temperature=temperature,
            ),
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
        if is_cancelled():
            return ""
        path = "/api/chat"
        payload = self._chat_payload(
            prompt, role=role, maximum_tokens=maximum_tokens, temperature=temperature, stream=True,
        )
        if is_cancelled():
            return ""
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
        except HTTPError as exc:
            message = self._http_error_message(exc, path, payload)
            self._observe("Error", path, {"message": message, "duration": time.time() - start})
            raise OllamaError(message) from exc
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
        require_full_context: bool = False,
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
            require_full_context=require_full_context,
        )

    def _chat_payload(
        self, prompt: str, *, role: str, maximum_tokens: int, temperature: float,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Keep the shared generation protocol in the Ollama boundary."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": role},
                {"role": "user", "content": prompt},
            ],
            "stream": stream,
            "think": False,
            "options": {"num_predict": maximum_tokens, "temperature": temperature},
        }
        if self.context_length:
            try:
                ContextBudget(self.context_length, maximum_tokens).require_fit(role, prompt)
            except ContextBudgetError as exc:
                raise OllamaError(str(exc)) from exc
            self._check_context_capacity()
            payload["options"]["num_ctx"] = self.context_length
            payload["truncate"] = False
            payload["shift"] = False
        return payload

    def _check_context_capacity(self) -> None:
        """Check advertised architecture capacity, never infer it from a model tag.

        Recheck per configured request so a replaced model tag cannot reuse stale
        metadata. This does not prove the runtime allocated the requested window.
        Call only in workers, just like generation itself.
        """
        result = self._post("/api/show", {"model": self.model})
        info = result.get("model_info")
        architecture = info.get("general.architecture") if isinstance(info, dict) else None
        capacity = info.get(f"{architecture}.context_length") if isinstance(architecture, str) else None
        if type(capacity) is not int or capacity <= 0:
            raise OllamaError(
                "Ollama did not report model context capacity. The explicit context window "
                "cannot be checked; use a supported server/model or select server default."
            )
        if self.context_length > capacity:
            raise OllamaError(
                f"Requested context window ({self.context_length} tokens) exceeds the model's "
                f"reported capacity ({capacity} tokens). No generation was sent."
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
        require_full_context: bool = False,
    ) -> str:
        payload = self._chat_payload(
            prompt, role=role, maximum_tokens=maximum_tokens, temperature=temperature,
        )
        if require_full_context:
            payload["truncate"] = False
            payload["shift"] = False
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
        payload = self._chat_payload(
            spellcheck_prompt(text, language),
            role=("You are a strict spellcheck engine. Return only valid JSON that matches the user's requested schema. "
                  "Never return markdown fences or an empty JSON object."),
            maximum_tokens=256, temperature=0.0,
        )
        payload["format"] = "json"
        response = self._post(
            "/api/chat",
            payload,
        )
        message = response.get("message")
        raw = message.get("content", "[]") if isinstance(message, dict) else "[]"
        return parse_suggestions(raw, text, 0)
