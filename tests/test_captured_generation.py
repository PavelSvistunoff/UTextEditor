"""Frozen source context has identical streaming/non-streaming contracts."""

import pytest

from app.ai.captured_completion import generate_captured_completion
from app.ai.completion_service import STALE_PROJECT_CONTEXT
from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.project import Project
from app.project.rag_context import ContextRequest, ProjectContextService


@pytest.fixture
def snapshot(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    note = project.add_note("Clue", content="The copper key opens the hidden door.")
    request = ContextRequest(ContextPrompt("Write for author review"), ContextBudget(8192, 80),
                             "Write about the copper key", author_request="copper key")
    captured = ProjectContextService().capture(project, request)
    return project, note, captured


class Provider:
    def __init__(self, effect=lambda: None):
        self.calls = []
        self.effect = effect

    def generate_private(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        self.effect()
        return "Draft"

    def generate_stream(self, prompt, *, on_chunk, is_cancelled, **kwargs):
        self.calls.append((prompt, kwargs))
        on_chunk("Dr")
        self.effect()
        on_chunk("aft")
        return "Draft"


def test_modes_send_identical_frozen_request(snapshot):
    _, _, captured = snapshot
    provider = Provider()
    chunks = []
    assert generate_captured_completion(provider, captured, {}, temperature=.3) == "Draft"
    assert generate_captured_completion(provider, captured, {}, temperature=.3, on_chunk=chunks.append) == "Draft"
    assert provider.calls[0] == provider.calls[1] == (captured.prompt, {
        "role": captured.role, "maximum_tokens": 80, "temperature": .3, "require_full_context": True})
    assert chunks == ["Dr", "aft"]


@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("when", ["before", "during", "error"])
def test_source_changes_drop_result_and_late_failure(snapshot, stream, when):
    project, note, captured = snapshot

    def change():
        (project.root / note.path).write_text("Changed source", encoding="utf-8")
        if when == "error":
            raise RuntimeError("Late provider failure")

    if when == "before":
        change()
    provider = Provider(change if when != "before" else lambda: None)
    result = generate_captured_completion(provider, captured, {}, temperature=.2,
                                         on_chunk=(lambda chunk: None) if stream else None)
    assert result is STALE_PROJECT_CONTEXT
    assert len(provider.calls) == (0 if when == "before" else 1)


def test_cancellation_suppresses_late_chunks_and_final_result(snapshot):
    _, _, captured = snapshot
    cancelled = [False]
    provider = Provider(lambda: cancelled.__setitem__(0, True))
    chunks = []
    assert generate_captured_completion(provider, captured, {}, temperature=.2,
        on_chunk=chunks.append, is_cancelled=lambda: cancelled[0]) is STALE_PROJECT_CONTEXT
    assert chunks == ["Dr"]


def test_current_provider_failure_is_reported(snapshot):
    _, _, captured = snapshot

    def fail():
        raise RuntimeError("Provider unavailable")

    with pytest.raises(RuntimeError, match="Provider unavailable"):
        generate_captured_completion(Provider(fail), captured, {}, temperature=.2, on_chunk=lambda text: None)


def test_malformed_chunk_is_rejected(snapshot):
    _, _, captured = snapshot
    provider = Provider()

    def malformed(prompt, *, on_chunk, **kwargs):
        on_chunk(None)
        return "Draft"

    provider.generate_stream = malformed
    with pytest.raises(ValueError, match="chunks must be text"):
        generate_captured_completion(provider, captured, {}, temperature=.2, on_chunk=lambda text: None)
