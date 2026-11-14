"""Explicitly invoked embedding smoke; synthetic sources and configured destination only."""

import os
import platform
from time import perf_counter

import pytest

from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.ai.ollama_client import OllamaClient
from app.project import Project
from app.project.rag_context import ContextRequest, ProjectContextService
from app.project.rag_embeddings import SemanticRetriever
from app.project.rag_index import LexicalIndex
from app.project.rag_sources import capture_project_sources
from app.settings.settings import AppSettings

pytestmark = [pytest.mark.live_ollama, pytest.mark.skipif(
    os.environ.get("UTEXTEDITOR_LIVE_EMBEDDINGS") != "1", reason="Explicit live embedding opt-in required")]


def test_configured_embeddings_roundtrip_and_warm_cache(tmp_path):
    settings = AppSettings.load()
    provider = OllamaClient(settings.embedding_host,settings.embedding_model,timeout=30)
    identity = provider.embedding_identity()
    start = perf_counter()
    project = Project.create(tmp_path / "project","Synthetic embedding smoke")
    remedy = project.add_note("Зілля",content="Відвар із білої верби лікує гарячку, від якої занедужав князь Данило.")
    project.add_note("Kitchen",content="The cook stores dried apples below deck.")
    index = LexicalIndex(tmp_path / "cache",project.root,project.manifest.project_id)
    index.refresh(capture_project_sources(project))
    retriever = SemanticRetriever(provider,index)
    service = ProjectContextService(index,semantic=retriever)
    request = ContextRequest(ContextPrompt("Story assistant"),ContextBudget(32768,100),
                             "Чим можна вилікувати хворого князя?",author_request="Чим можна вилікувати хворого князя?")
    captured = service.capture(project,request)
    assert captured.manifest.retrieval_method == "hybrid",captured.manifest.notices
    assert captured.manifest.embedding_identity == identity
    assert any(item.source_id == remedy.id and item.disposition in {"included","shortened"}
               for item in captured.manifest.decisions)
    cold_seconds = perf_counter() - start
    original = retriever.cache.path.read_bytes()
    start = perf_counter()
    again = service.capture(project,request)
    warm_seconds = perf_counter() - start
    assert again.manifest.retrieval_method == "hybrid"
    assert retriever.cache.path.read_bytes() == original
    assert any("2 cached, 0 newly" in notice for notice in again.manifest.notices)
    print({"model":identity.model,"digest":identity.digest,"dimensions":identity.dimensions,
           "host":identity.host,"hardware":platform.platform(),"cold_seconds":cold_seconds,
           "warm_seconds":warm_seconds,"cache_bytes":len(original)})
