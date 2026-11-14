"""Hybrid ranking/cache lifecycle, deterministic and offline."""

from dataclasses import replace

import pytest

from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.ai.embeddings import EmbeddingError, EmbeddingIdentity
from app.project import Project, ProjectError
from app.project.rag_context import ContextRequest, ProjectContextService, RetrievalPolicy
from app.project.rag_embeddings import SemanticRetriever, VectorCache, fuse_rankings
from app.project.rag_index import LexicalIndex, fts5_available
from app.project.rag_sources import BufferText, CaptureCancelled, CaptureLimits, capture_project_sources


class FakeEmbeddings:
    def __init__(self):
        self.identity = EmbeddingIdentity("http://embedding.local", "fake", "v1", 3)
        self.calls = []
        self.on_embed = None

    def embedding_identity(self):
        return self.identity

    def embed(self, texts, identity):
        self.calls.append(texts)
        if self.on_embed:
            return self.on_embed(texts, identity)
        return tuple((1.0,0.0,0.0) if ("medicine" in text or "poison" in text) else (0.0,1.0,0.0)
                     for text in texts)


@pytest.fixture
def corpus(tmp_path):
    if not fts5_available():
        pytest.skip("Runtime SQLite has no FTS5")
    project = Project.create(tmp_path / "project", "Novel")
    relevant = project.add_note("Remedy", content="A rare flower is the medicine that will save the captain.")
    distractor = project.add_note("Kitchen", content="The cook prepares potatoes for the voyage.")
    index = LexicalIndex(tmp_path / "cache", project.root, project.manifest.project_id)
    index.refresh(capture_project_sources(project))
    provider = FakeEmbeddings()
    return project, relevant, distractor, index, provider


def request():
    return ContextRequest(ContextPrompt("Author"), ContextBudget(32768,100), "poison",
                          author_request="poison", policy=RetrievalPolicy(maximum_passages=3))


def included(result):
    return [item.source_id for item in result.manifest.decisions if item.disposition in {"included","shortened"}]


def test_rrf_combines_ranks_and_deduplicates():
    scores = fuse_rankings(("b","a","b"),("a","c"))
    assert scores["a"] == pytest.approx(1/62+1/61)
    assert scores["b"] == pytest.approx(1/61)
    assert scores["c"] == pytest.approx(1/62)
    assert scores == fuse_rankings(("b","a"),("a","c"))


def test_automatic_cached_only_never_creates_source_vectors(corpus):
    project, relevant, distractor, index, provider = corpus
    automatic = ProjectContextService(index, semantic=SemanticRetriever(provider, index, cached_only=True))
    result = automatic.capture(project, request())
    assert result.manifest.retrieval_method == "lexical_fallback"
    assert provider.calls == []
    ProjectContextService(index, semantic=SemanticRetriever(provider, index)).capture(project, request())
    provider.calls.clear()
    result = automatic.capture(project, request())
    assert result.manifest.retrieval_method == "hybrid"
    assert len(provider.calls) == 1  # Query only; no project-vector generation.
    provider.calls.clear()
    automatic.capture(project, request(), open_buffers={relevant.id: BufferText("Unsaved medicine reference", 2)})
    assert provider.calls == []


def test_semantic_only_match_reuses_saved_vectors_and_excludes_before_embedding(corpus):
    project, relevant, distractor, index, provider = corpus
    service = ProjectContextService(index,semantic=SemanticRetriever(provider,index))
    result = service.capture(project,request())
    assert included(result) == [relevant.id]
    assert result.manifest.retrieval_method == "hybrid"
    assert result.manifest.embedding_identity.digest == "v1"
    assert len(provider.calls) == 2
    path = VectorCache(index).path
    original = path.read_bytes()
    provider.calls.clear()
    again = service.capture(project,request())
    assert included(again) == included(result)
    assert len(provider.calls) == 1  # Query only; no source vectors transmitted again.
    assert path.read_bytes() == original
    excluded = replace(request(),policy=RetrievalPolicy(excluded_source_ids=frozenset({relevant.id})))
    provider.calls.clear()
    result = service.capture(project,excluded)
    assert relevant.id not in included(result)
    assert all("medicine" not in text for batch in provider.calls for text in batch)


def test_model_digest_dimensions_and_host_changes_invalidate_cache(corpus):
    project, relevant, distractor, index, provider = corpus
    retriever = SemanticRetriever(provider,index)
    service = ProjectContextService(index,semantic=retriever)
    service.capture(project,request())
    for change in ({"digest":"v2"},{"model":"other"},{"host":"https://other.example"}):
        provider.identity = replace(provider.identity,**change)
        provider.calls.clear()
        service.capture(project,request())
        assert len(provider.calls) == 2
    provider.identity = replace(provider.identity,dimensions=2)
    provider.calls.clear()
    result = service.capture(project,request())
    assert result.manifest.retrieval_method == "lexical_fallback"
    assert any("dimensions" in notice for notice in result.manifest.notices)


def test_unsaved_vectors_are_request_local_and_current_text_is_authority(corpus):
    project, relevant, distractor, index, provider = corpus
    service = ProjectContextService(index,semantic=SemanticRetriever(provider,index))
    buffers = {relevant.id:BufferText("Different unsaved medicine text.",7)}
    result = service.capture(project,request(),open_buffers=buffers)
    assert included(result) == [relevant.id]
    assert "Different unsaved medicine" in result.prompt
    assert "rare flower" not in result.prompt
    path = VectorCache(index).path
    values = VectorCache(index).read(provider.identity)
    assert len(values) == 1  # Only the other saved note.
    assert b"Different unsaved" not in path.read_bytes()
    provider.calls.clear()
    service.capture(project,request(),open_buffers=buffers)
    assert any("Different unsaved medicine" in text for batch in provider.calls for text in batch)
    with pytest.raises(ProjectError,match="buffer changed"):
        result.verify_current({relevant.id:BufferText("edited",8)})


@pytest.mark.parametrize("failure", ["partial","dimensions","nan","zero","timeout","query","model"])
def test_failures_fall_back_visibly_without_partial_cache(corpus,failure):
    project, relevant, distractor, index, provider = corpus
    def fail(texts,identity):
        if failure == "partial": return ()
        if failure == "dimensions": return ((1.0,0.0),)*len(texts)
        if failure == "nan": return ((float("nan"),0.0,1.0),)*len(texts)
        if failure == "zero": return ((0.0,0.0,0.0),)*len(texts)
        if failure == "timeout": raise TimeoutError("test timeout")
        if failure == "query" and len(provider.calls) == 2: raise EmbeddingError("query failed")
        if failure == "model": provider.identity = replace(identity,digest="changed")
        return ((1.0,0.0,0.0),)*len(texts)
    provider.on_embed = fail
    result = ProjectContextService(index,semantic=SemanticRetriever(provider,index)).capture(project,request())
    assert result.manifest.retrieval_method == "lexical_fallback"
    assert not included(result)  # Baseline lexical query has no literal hit.
    assert any("lexical fallback" in text for text in result.manifest.notices)
    assert not VectorCache(index).path.exists()
    assert not list(index.path.parent.glob("*.building*"))


@pytest.mark.parametrize("change", ["disk","manifest","cancel"])
def test_sources_changed_during_embedding_never_publish_or_downgrade_cancellation(corpus,change):
    project, relevant, distractor, index, provider = corpus
    cancelled = [False]
    def mutate(texts,identity):
        if change == "disk": (project.root / relevant.path).write_text("changed",encoding="utf-8")
        elif change == "manifest": project.rename_note(relevant.id,"Changed title")
        else: cancelled[0] = True
        return ((1.0,0.0,0.0),)*len(texts)
    provider.on_embed = mutate
    with pytest.raises(ProjectError):
        ProjectContextService(index,semantic=SemanticRetriever(provider,index)).capture(project,request(),is_cancelled=lambda:cancelled[0])
    assert not VectorCache(index).path.exists()


def test_bounds_and_corrupt_cache_use_lexical_fallback(corpus,monkeypatch):
    project, relevant, distractor, index, provider = corpus
    service = ProjectContextService(index,semantic=SemanticRetriever(provider,index))
    monkeypatch.setattr("app.project.rag_embeddings.MAX_SEMANTIC_CHUNKS",1)
    result = service.capture(project,request())
    assert result.manifest.retrieval_method == "lexical_fallback"
    assert not provider.calls
    monkeypatch.undo()
    path = VectorCache(index).path
    path.write_bytes(b"invalid SQLite")
    result = service.capture(project,request())
    assert result.manifest.retrieval_method == "lexical_fallback"
    assert not provider.calls


def test_chunk_policy_and_changed_saved_text_regenerate_vectors(corpus):
    project, relevant, distractor, index, provider = corpus
    service = ProjectContextService(index,semantic=SemanticRetriever(provider,index))
    service.capture(project,request())
    (project.root / relevant.path).write_text("A new medicine from the desert.",encoding="utf-8")
    provider.calls.clear()
    result = service.capture(project,request())
    assert "new medicine" in result.prompt
    assert len(provider.calls[0]) == 1
    limits = CaptureLimits(chunk_characters=80,overlap_characters=10)
    index.refresh(capture_project_sources(project,limits=limits),force=True)
    provider.calls.clear()
    service.capture(project,request(),limits=limits)
    assert len(provider.calls[0]) == 2


def test_vector_cache_deleted_with_lexical_cache_and_symlinks_refused(corpus,tmp_path):
    project, relevant, distractor, index, provider = corpus
    ProjectContextService(index,semantic=SemanticRetriever(provider,index)).capture(project,request())
    path = VectorCache(index).path
    assert path.exists()
    index.delete()
    assert not path.exists()
    target = tmp_path / "unrelated"
    target.write_text("preserve")
    path.symlink_to(target)
    with pytest.raises(EmbeddingError,match="symbolic link"):
        VectorCache(index).read(provider.identity)
    assert target.read_text() == "preserve"


def test_partial_later_batch_preserves_previous_cache(corpus):
    project, relevant, distractor, index, provider = corpus
    service = ProjectContextService(index,semantic=SemanticRetriever(provider,index))
    service.capture(project,request())
    path = VectorCache(index).path
    original = path.read_bytes()
    for number in range(12):
        project.add_note(f"Other {number}",content="Medicine from another source.")
    count = [0]
    def second_batch_fails(texts,identity):
        count[0] += 1
        return ((1.0,0.0,0.0),)*len(texts) if count[0] == 1 else ()
    provider.on_embed = second_batch_fails
    result = service.capture(project,request())
    assert result.manifest.retrieval_method == "lexical_fallback"
    assert count[0] == 2
    assert path.read_bytes() == original


def test_changed_index_generation_during_embedding_refuses_cache_publication(corpus):
    project, relevant, distractor, index, provider = corpus
    def refresh(texts,identity):
        index.refresh(capture_project_sources(project),force=True)
        return ((1.0,0.0,0.0),)*len(texts)
    provider.on_embed = refresh
    result = ProjectContextService(index,semantic=SemanticRetriever(provider,index)).capture(project,request())
    assert result.manifest.retrieval_method == "lexical_fallback"
    assert not VectorCache(index).path.exists()


def test_vector_cache_write_cancel_is_atomic_and_cleans_staging(corpus,monkeypatch):
    project, relevant, distractor, index, provider = corpus
    service = ProjectContextService(index,semantic=SemanticRetriever(provider,index))
    service.capture(project,request())
    cache = VectorCache(index)
    original = cache.path.read_bytes()
    values = cache.read(provider.identity)
    checks = [0]
    def cancel_before_replace():
        checks[0] += 1
        if checks[0] == 2: raise CaptureCancelled("cancelled before replace")
    with pytest.raises(CaptureCancelled):
        cache.write(provider.identity,values,verify=cancel_before_replace,is_cancelled=lambda:False)
    assert cache.path.read_bytes() == original
    assert not list(index.path.parent.glob("*.building*"))


def test_missing_index_never_sends_embedding_text(corpus):
    project, relevant, distractor, index, provider = corpus
    index.delete()
    result = ProjectContextService(index,semantic=SemanticRetriever(provider,index)).capture(project,request())
    assert result.manifest.retrieval_method == "lexical_fallback"
    assert not provider.calls


def test_chronology_and_scene_associations_still_apply_before_semantic_ranking(corpus):
    from app.project import SceneCharacterAssociation
    project, relevant, distractor, index, provider = corpus
    chapter = project.add_chapter("Chapter")
    target = project.add_scene("Target",chapter_id=chapter.id,content="poison")
    later = project.add_scene("Later",chapter_id=chapter.id,content="medicine FUTURE_SECRET")
    character = project.add_character("Captain")
    project.associate_character(target.id,SceneCharacterAssociation(character.id))
    index.refresh(capture_project_sources(project))
    result = ProjectContextService(index,semantic=SemanticRetriever(provider,index)).capture(
        project,replace(request(),target_scene_id=target.id))
    assert "FUTURE_SECRET" not in result.prompt
    assert all("FUTURE_SECRET" not in text for batch in provider.calls for text in batch)
    assert character.id in result.prompt
    assert later.id not in included(result)


def test_foreign_or_tampered_semantic_candidates_refuse_before_network(corpus,tmp_path):
    project, relevant, distractor, index, provider = corpus
    capture = capture_project_sources(project)
    retriever = SemanticRetriever(provider,index)
    altered = replace(capture.chunks[0],start=1)
    with pytest.raises(EmbeddingError,match="captured project"):
        retriever.rank(capture,(altered,),"poison",())
    other_index = LexicalIndex(tmp_path / "other-cache",tmp_path / "other-project","foreign")
    with pytest.raises(EmbeddingError,match="captured project"):
        SemanticRetriever(provider,other_index).rank(capture,capture.chunks,"poison",())
    assert not provider.calls


def test_deleted_index_cannot_be_resurrected_by_semantic_capture(corpus):
    project, relevant, distractor, index, provider = corpus
    capture = capture_project_sources(project)
    index.delete()
    retriever = SemanticRetriever(provider,index)
    with pytest.raises(EmbeddingError,match="current lexical index"):
        retriever.rank(capture,capture.chunks,"poison",())
    assert not provider.calls
    assert not retriever.cache.path.exists()
