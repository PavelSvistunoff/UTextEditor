"""Explicit live hybrid inline and multi-step smoke, synthetic manuscript only."""

import os
from time import perf_counter

import pytest

from app.ai.captured_completion import generate_captured_completion
from app.ai.ollama_client import OllamaClient
from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.project import Project
from app.project.auto_writer import run_auto_writer
from app.project.auto_writer_context import AutoWriterRetrieval, ContextReviewDecision
from app.project.inline_context import InlineContextService
from app.project.rag_context import ContextRequest, ProjectContextService, RetrievalPolicy
from app.project.rag_embeddings import SemanticRetriever
from app.project.rag_index import LexicalIndex
from app.project.rag_sources import capture_project_sources
from app.settings.settings import AppSettings

pytestmark = [pytest.mark.live_ollama, pytest.mark.skipif(
    os.environ.get("UTEXTEDITOR_LIVE_RAG_WORKFLOWS") != "1", reason="Explicit live hybrid workflow opt-in required")]


def test_live_hybrid_inline_and_two_scene_writer(tmp_path):
    settings = AppSettings.load()
    events = []
    window = settings.ollama_context_length or 8192
    provider = OllamaClient(settings.ollama_host, settings.ollama_model, context_length=window,
        timeout=300, interaction_observer=lambda event, path, details: events.append((event, path, details)))
    embeddings = OllamaClient(settings.embedding_host, settings.embedding_model, timeout=30)
    identity = embeddings.embedding_identity()
    project = Project.create(tmp_path / "synthetic", "Hybrid workflow smoke")
    chapter = project.add_chapter("Chapter")
    fact = project.add_scene("Archive", chapter_id=chapter.id,
        content="Mara hid the brass key inside the red lantern by the garden gate.")
    first = project.add_scene("Find the brass key", chapter_id=chapter.id)
    second = project.add_scene("Use the brass key", chapter_id=chapter.id)
    cache = tmp_path / "cache"
    index = LexicalIndex(cache, project.root, project.manifest.project_id)
    index.refresh(capture_project_sources(project))
    request = ContextRequest(ContextPrompt("Continue the mandatory_text with one short English sentence only."),
        ContextBudget(window, 96), "Mara searched for the brass key", author_request="Find the brass key",
        target_scene_id=first.id, policy=RetrievalPolicy(allowed_kinds=frozenset({"scene"})))
    warm = ProjectContextService(index, semantic=SemanticRetriever(embeddings, index)).capture(project, request)
    assert warm.manifest.retrieval_method == "hybrid", warm.manifest.notices
    start = perf_counter()
    inline = InlineContextService().capture(project, index, request, {},
        semantic=SemanticRetriever(embeddings, index, cached_only=True), embedding_key=identity)
    assert inline.captured.manifest.retrieval_method == "hybrid", inline.captured.manifest.notices
    continuation = generate_captured_completion(provider, inline.captured, {}, temperature=.1)
    assert isinstance(continuation, str) and continuation.strip()
    assert project.read_scene(first.id) == ""
    print({"live_workflow": "inline", "generation_model": settings.ollama_model,
        "embedding_model": identity.model, "embedding_digest": identity.digest, "dimensions": identity.dimensions,
        "retrieval_seconds": inline.retrieval_seconds, "total_seconds": perf_counter() - start,
        "output_characters": len(continuation)}, flush=True)
    reviewed = []
    def review(title, captured, excluded):
        assert captured.manifest.retrieval_method == "hybrid", captured.manifest.notices
        assert any(item.source_id == fact.id and item.disposition in {"included", "shortened"}
                   for item in captured.manifest.decisions)
        reviewed.append(captured)
        return ContextReviewDecision("send", excluded)
    start = perf_counter()
    result = run_auto_writer(provider, project, "write_empty",
        "Write just one short English sentence about the brass key; no title or explanation.", {},
        maximum_tokens=96, temperature=.1, snapshot_name="Before synthetic hybrid smoke",
        is_cancelled=lambda: False, retrieval=AutoWriterRetrieval(cache, window, review, embeddings))
    assert set(result.replacements) == {first.id, second.id} and len(reviewed) == 2
    assert all(value.strip() for value in result.replacements.values())
    assert project.read_scene(first.id) == project.read_scene(second.id) == ""
    assert any("Provisional earlier drafts" in item.prompt for item in reviewed[1:])
    requests = [details for event, path, details in events if event == "Request" and path == "/api/chat"]
    assert [item["messages"][1]["content"] for item in requests] == [inline.captured.prompt, *[item.prompt for item in reviewed]]
    print({"live_workflow": "two-step-auto-writer", "requests": len(reviewed),
        "elapsed_seconds": perf_counter() - start, "requested_window": window,
        "generation_host": settings.ollama_host, "embedding_host": settings.embedding_host,
        "draft_characters": [len(text) for text in result.replacements.values()],
        "project_unchanged": True}, flush=True)
