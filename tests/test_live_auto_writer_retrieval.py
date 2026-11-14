"""Explicit live RAG Auto-writer generation smoke, synthetic project only."""

import os
from pathlib import Path
from time import perf_counter

import pytest

from app.ai.ollama_client import OllamaClient
from app.project import Project
from app.project.auto_writer import run_auto_writer
from app.project.auto_writer_context import AutoWriterRetrieval, ContextReviewDecision
from app.project.rag_index import LexicalIndex
from app.project.rag_sources import capture_project_sources
from app.settings.settings import AppSettings

pytestmark=[pytest.mark.live_ollama,pytest.mark.skipif(
    os.environ.get('UTEXTEDITOR_LIVE_RAG_AUTOWRITER')!='1',reason='Explicit live RAG Auto-writer opt-in required')]


def test_configured_generation_uses_reviewed_distant_evidence_and_snapshot(tmp_path):
    settings=AppSettings.load()
    window=settings.ollama_context_length or 8192
    events=[]
    provider=OllamaClient(settings.ollama_host,settings.ollama_model,context_length=window,timeout=300,
                          interaction_observer=lambda event,path,details:events.append((event,path,details)))
    project=Project.create(tmp_path/'project','Synthetic live RAG smoke')
    chapter=project.add_chapter('Chapter')
    fact=project.add_scene('Archive',chapter_id=chapter.id,content='The brass key is hidden inside the red lantern.')
    for i in range(3): project.add_scene(f'Walk {i}',chapter_id=chapter.id,content='The travellers walked quietly.')
    target=project.add_scene('Find the brass key',chapter_id=chapter.id)
    cache=tmp_path/'cache'
    LexicalIndex(cache,project.root,project.manifest.project_id).refresh(capture_project_sources(project))
    reviewed=[]
    def review(title,captured,excluded):
        assert project.read_scene(target.id)==''
        assert list((project.root/'.utexteditor/revisions').iterdir())
        assert any(item.source_id==fact.id and item.disposition in {'included','shortened'} for item in captured.manifest.decisions)
        reviewed.append(captured)
        return ContextReviewDecision('send',excluded)
    start=perf_counter()
    result=run_auto_writer(provider,project,'write_empty','Write only one short English sentence about finding the brass key; no title or explanation.',{},
        maximum_tokens=256,temperature=0.1,snapshot_name='Before live RAG smoke',is_cancelled=lambda:False,
        retrieval=AutoWriterRetrieval(cache,window,review))
    elapsed=perf_counter()-start
    requests=[data for event,path,data in events if event=='Request' and path=='/api/chat']
    assert len(requests)==1 and requests[0]['messages'][1]['content']==reviewed[0].prompt
    assert result.replacements[target.id].strip() and project.read_scene(target.id)==''
    assert Path(result.snapshot_path).exists()
    project.replace_scenes_transactionally(dict(result.replacements),expected_contents=dict(result.expected_disk_text),
                                           expected_contexts=dict(result.expected_context_text))
    assert project.read_scene(target.id)==result.replacements[target.id]
    assert project.read_scene(fact.id)=='The brass key is hidden inside the red lantern.'
    print({'host':settings.ollama_host,'model':settings.ollama_model,'requested_window':window,
           'elapsed_seconds':elapsed,'output_characters':len(result.replacements[target.id]),'retrieved_source_count':len(result.retrieval_contexts[target.id].passages)})
