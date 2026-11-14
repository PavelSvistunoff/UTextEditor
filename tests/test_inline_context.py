"""Deterministic cache/deadline policy, without a server or timing assertions."""

from dataclasses import replace

import pytest

from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.project import Project
from app.project.inline_context import InlineContextService
from app.project.rag_context import ContextRequest, ProjectContextService, RetrievalPolicy
from app.project.rag_index import LexicalIndex
from app.project.rag_sources import BufferText, CaptureCancelled, capture_project_sources


@pytest.fixture
def captured_project(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter")
    earlier = project.add_scene("Clue", chapter_id=chapter.id,
                                content="The hidden door opens with a copper key from the garden.")
    target = project.add_scene("Door", chapter_id=chapter.id, content="The hidden door")
    note = project.add_note("Key", content="The hidden door opens only after midnight in winter.")
    index = LexicalIndex(tmp_path / "cache", project.root, project.manifest.project_id)
    index.refresh(capture_project_sources(project))
    request = ContextRequest(ContextPrompt("Continue the story"), ContextBudget(32768, 50),
                             "The hidden door", current_passage="The hidden door", target_scene_id=target.id,
                             policy=RetrievalPolicy(maximum_passages=4))
    return project, index, request, earlier, target, note


def test_repeated_capture_reuses_only_verified_context(captured_project, monkeypatch):
    project, index, request, earlier, target, note = captured_project
    service = InlineContextService()
    first = service.capture(project, index, request, {})
    assert not first.cache_hit
    monkeypatch.setattr(ProjectContextService, "capture", lambda *a, **kw: pytest.fail("cache should reuse capture"))
    second = service.capture(project, index, request, {})
    assert second.cache_hit and first.captured == second.captured


@pytest.mark.parametrize("change", ["query", "policy", "exclusion", "buffer", "disk", "index", "embedding"])
def test_cache_keys_and_byte_verification_invalidate(captured_project, change):
    project, index, request, earlier, target, note = captured_project
    service = InlineContextService()
    service.capture(project, index, request, {})
    buffers, embedding_key = {}, None
    if change == "query":
        request = replace(request, current_passage="The copper key")
    elif change == "policy":
        request = replace(request, policy=replace(request.policy, chronology="all"))
    elif change == "exclusion":
        request = replace(request, policy=replace(request.policy, excluded_source_ids=frozenset({note.id})))
    elif change == "buffer":
        buffers[note.id] = BufferText("The hidden door opens at noon; unsaved version wins.", 7)
    elif change == "disk":
        (project.root / note.path).write_text("The hidden door now opens at noon in summer.")
    elif change == "index":
        index.delete()
        index.refresh(capture_project_sources(project))
    else:
        embedding_key = ("http://remote.example", "another-model")
    result = service.capture(project, index, request, buffers, embedding_key=embedding_key)
    assert not result.cache_hit
    if change == "buffer":
        assert "unsaved version wins" in result.captured.prompt
        assert "after midnight" not in result.captured.prompt
    if change == "exclusion":
        assert "after midnight" not in result.captured.prompt


def test_fake_clock_timeout_recaptures_mandatory_only(captured_project, monkeypatch):
    project, index, request, *_ = captured_project
    now = [0.0]
    service = InlineContextService(clock=lambda: now[0])
    original = ProjectContextService.capture
    calls = []

    def expire_once(self, *args, **kwargs):
        calls.append(True)
        if len(calls) == 1:
            now[0] = 2.0
        return original(self, *args, **kwargs)

    monkeypatch.setattr(ProjectContextService, "capture", expire_once)
    result = service.capture(project, index, request, {})
    assert len(calls) == 2
    assert "copper key" not in result.captured.prompt
    assert any("timed out" in notice for notice in result.captured.manifest.notices)
    assert service._entry is None


def test_cancellation_never_downgrades_to_fallback(captured_project):
    project, index, request, *_ = captured_project
    with pytest.raises(CaptureCancelled):
        InlineContextService().capture(project, index, request, {}, is_cancelled=lambda: True)


def test_missing_index_and_empty_hits_are_explicit(captured_project):
    project, index, request, *_ = captured_project
    request = replace(request, current_passage="zyxwvunmatched", mandatory_text="zyxwvunmatched")
    result = InlineContextService().capture(project, index, request, {})
    assert result.captured.manifest.retrieval_state == "no_hits"
    index.delete()
    result = InlineContextService().capture(project, index, request, {})
    assert result.captured.manifest.index_state == "unavailable"
    assert "copper key" not in result.captured.prompt


def test_mandatory_timeout_skips_instead_of_reusing(captured_project, monkeypatch):
    project, index, request, *_ = captured_project
    now = [0.0]
    service = InlineContextService(clock=lambda: now[0])
    original = ProjectContextService.capture
    def expire(self, *args, **kwargs):
        now[0] += 2
        return original(self, *args, **kwargs)
    monkeypatch.setattr(ProjectContextService, "capture", expire)
    with pytest.raises(CaptureCancelled):
        service.capture(project, index, request, {})


def test_cached_hybrid_reuses_query_result_but_rechecks_installed_identity(captured_project):
    from test_rag_embeddings import FakeEmbeddings
    from app.project.rag_embeddings import SemanticRetriever
    project, index, request, *_ = captured_project
    provider = FakeEmbeddings()
    ProjectContextService(index, semantic=SemanticRetriever(provider, index)).capture(project, request)
    provider.calls.clear()
    service = InlineContextService()
    semantic = SemanticRetriever(provider, index, cached_only=True)
    first = service.capture(project, index, request, {}, semantic=semantic)
    assert first.captured.manifest.retrieval_method == "hybrid"
    assert len(provider.calls) == 1
    second = service.capture(project, index, request, {}, semantic=semantic)
    assert second.cache_hit and len(provider.calls) == 1
    provider.identity = replace(provider.identity, digest="changed-installed-model")
    third = service.capture(project, index, request, {}, semantic=semantic)
    assert not third.cache_hit
    assert third.captured.manifest.retrieval_method == "lexical_fallback"
    assert len(provider.calls) == 1  # No new source vectors on model replacement.


def test_incomplete_capture_is_not_cached(captured_project):
    project, index, request, earlier, target, note = captured_project
    (project.root / note.path).unlink()
    service = InlineContextService()
    result = service.capture(project, index, request, {})
    assert not result.captured.source_capture.complete
    assert service._entry is None


def test_fake_clock_expiration_also_verifies_cache_hits(captured_project, monkeypatch):
    from app.project.rag_sources import ProjectSourceCapture
    project, index, request, *_ = captured_project
    now = [0.0]
    service = InlineContextService(clock=lambda: now[0])
    service.capture(project, index, request, {})
    original = ProjectSourceCapture.verify_current
    checks = []
    def expire_first(self, *args, **kwargs):
        checks.append(True)
        if len(checks) == 1:
            now[0] = 2
        return original(self, *args, **kwargs)
    monkeypatch.setattr(ProjectSourceCapture, "verify_current", expire_first)
    result = service.capture(project, index, request, {})
    assert not result.cache_hit
    assert "copper key" not in result.captured.prompt
    assert any("timed out" in text for text in result.captured.manifest.notices)
