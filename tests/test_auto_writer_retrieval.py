"""Auto-writer RAG preserves full context, review identity and transactional safety."""

from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.ai.context_budget import ContextBudgetError
from app.document.revisions import RevisionStore
from app.project import Project, ProjectError, SceneCharacterAssociation
from app.project.auto_writer import run_auto_writer
from app.project.auto_writer_context import AutoWriterRetrieval, ContextReviewDecision
from app.project.rag_evidence import captured_passages, capture_request_evidence, validate_quote
from app.project.rag_index import LexicalIndex, fts5_available
from app.project.rag_sources import capture_project_sources


class Provider:
    def __init__(self):
        self.prompts=[]
        self.on_generate=None

    def generate_private(self,prompt,**options):
        self.prompts.append((prompt,options))
        return self.on_generate(prompt) if self.on_generate else 'A complete draft about the silver compass.'


@pytest.fixture
def story(tmp_path):
    if not fts5_available(): pytest.skip('SQLite FTS5 unavailable')
    project=Project.create(tmp_path/'project','Novel')
    chapter=project.add_chapter('Chapter')
    far=project.add_scene('Archive',chapter_id=chapter.id,content='The silver compass is hidden in a hollow tree. Distant evidence.')
    for i in range(3): project.add_scene(f'Interlude {i}',chapter_id=chapter.id,content='They walked through the meadow.')
    target=project.add_scene('Find the silver compass',chapter_id=chapter.id)
    future=project.add_scene('Future',chapter_id=chapter.id,content='FUTURE_TRAP silver compass revealed tomorrow.')
    note=project.add_note('World',content='REFERENCE_START '+ 'a'*11000+' REFERENCE_END')
    character=project.add_character('Mara');character.background['history']='FULL_CHARACTER_END'
    project.update_character(character.id,character)
    other=project.add_character('Distant person');other.arc['current_state']='FULL_UNASSOCIATED_END'
    project.update_character(other.id,other)
    project.associate_character(target.id,SceneCharacterAssociation(character.id,presence='mentioned'))
    cache=tmp_path/'cache'
    index=LexicalIndex(cache,project.root,project.manifest.project_id)
    index.refresh(capture_project_sources(project))
    return project,far,target,future,note,character,other,cache


def run(story,provider,review,**changes):
    project,*_,cache=story
    options=dict(maximum_tokens=300,temperature=0.2,snapshot_name='Before RAG',is_cancelled=lambda:False,
                 retrieval=AutoWriterRetrieval(cache,65536,review))
    options.update(changes)
    return run_auto_writer(provider,project,'write_empty','Keep established silver compass facts.',{},**options)


def test_distant_scene_full_notes_profiles_associations_and_exact_reviewed_prompt(story):
    project,far,target,future,note,character,other,cache=story
    provider=Provider();reviewed=[]
    def review(title,captured,excluded):
        reviewed.append(captured)
        assert project.read_scene(target.id)==''
        evidence=captured_passages(captured)
        assert far.id in {item.source_id for item in evidence}
        assert future.id not in {item.source_id for item in evidence}
        assert 'FUTURE_TRAP' not in captured.prompt
        assert 'REFERENCE_START' in captured.prompt and 'REFERENCE_END' in captured.prompt
        assert 'FULL_CHARACTER_END' in captured.prompt and 'FULL_UNASSOCIATED_END' in captured.prompt
        assert character.id in captured.prompt and 'mentioned' in captured.prompt
        quote=next(item for item in evidence if item.source_id==far.id)
        assert validate_quote(captured,far.id,quote.start,quote.end,quote.text)==quote
        return ContextReviewDecision('send',excluded)
    result=run(story,provider,review)
    assert provider.prompts[0][0]==reviewed[0].prompt
    assert provider.prompts[0][1]['role']==reviewed[0].role
    assert provider.prompts[0][1]['require_full_context'] is True
    record=result.retrieval_contexts[target.id]
    assert record.prompt==reviewed[0].prompt and record.passages==captured_passages(reviewed[0])
    assert not hasattr(record,'source_capture')  # Whole-corpus snapshots are not retained per draft.
    assert project.read_scene(target.id)=='' and Path(result.snapshot_path).exists()


def test_exclusions_rebuild_before_send_and_missing_evidence_is_explicit(story):
    project,far,target,future,note,character,other,cache=story
    provider=Provider();visits=[]
    def review(title,captured,excluded):
        visits.append(captured)
        if len(visits)==1: return ContextReviewDecision('rebuild',frozenset({far.id}))
        assert not captured_passages(captured)
        assert captured.manifest.retrieval_state=='no_hits'
        assert any(item.source_id==far.id and item.reason=='excluded' for item in captured.manifest.decisions)
        return ContextReviewDecision('send',excluded)
    result=run(story,provider,review)
    assert len(visits)==2 and len(provider.prompts)==1
    assert provider.prompts[0][0]==visits[1].prompt


def test_generated_prior_drafts_are_full_provisional_overlays_and_never_persisted(story):
    project,far,target,future,note,character,other,cache=story
    second=project.add_scene('Follow the new amber beacon',chapter_id=project.manifest.chapters[0].id)
    provider=Provider();reviews=[]
    provider.on_generate=lambda prompt: ('x'*1300+'\nThe new amber beacon is inside a hollow tower.' if len(provider.prompts)==1 else 'Second draft.')
    def review(title,captured,excluded):
        reviews.append(captured)
        if len(reviews)==2:
            evidence=captured_passages(captured)
            assert any(item.source_id==target.id and 'amber beacon' in item.text for item in evidence)
            assert 'Provisional earlier drafts generated in this run' in captured.prompt
            assert any('Provisional generated-draft evidence' in notice for notice in captured.manifest.notices)
            assert project.read_scene(target.id)==''
        return ContextReviewDecision('send',excluded)
    result=run(story,provider,review)
    assert len(result.replacements)==2
    assert project.read_scene(target.id)=='' and project.read_scene(second.id)==''
    assert b'amber beacon' not in LexicalIndex(cache,project.root,project.manifest.project_id).path.read_bytes()


@pytest.mark.parametrize('stage',['review','generation','failure'])
def test_disk_changes_discard_results_and_preserve_pre_run_snapshot(story,stage):
    project,far,target,future,note,character,other,cache=story
    provider=Provider()
    def change(): (project.root/far.path).write_text('Changed evidence',encoding='utf-8')
    def review(title,captured,excluded):
        if stage=='review': change()
        return ContextReviewDecision('send',excluded)
    def generate(prompt):
        change()
        if stage=='failure': raise RuntimeError('obsolete provider error')
        return 'Generated text'
    if stage!='review': provider.on_generate=generate
    with pytest.raises(ProjectError,match='changed'):
        run(story,provider,review)
    assert project.read_scene(target.id)==''
    assert RevisionStore(project.root/'.utexteditor/revisions').list_snapshots()
    assert len(provider.prompts)==(stage!='review')


@pytest.mark.parametrize('limit',['tokens','reviews','references'])
def test_budget_refusal_never_drops_mandatory_context_or_sends_a_request(story,monkeypatch,limit):
    project,far,target,future,note,character,other,cache=story
    provider=Provider();review=lambda title,captured,excluded:ContextReviewDecision('send',excluded)
    options={}
    if limit=='tokens': options['retrieval']=AutoWriterRetrieval(cache,512,review)
    elif limit=='reviews': monkeypatch.setattr('app.project.auto_writer.MAX_AUTOWRITER_REVIEW_BYTES',100)
    else: (project.root/note.path).write_text('я'*40000,encoding='utf-8')
    with pytest.raises((ProjectError,ContextBudgetError)):
        run(story,provider,review,**options)
    assert not provider.prompts and project.read_scene(target.id)==''


def test_generation_failure_after_first_draft_leaves_every_scene_unchanged(story):
    project,far,target,future,note,character,other,cache=story
    second=project.add_scene('Another empty scene',chapter_id=project.manifest.chapters[0].id)
    provider=Provider()
    def fail_second(prompt):
        if len(provider.prompts)==2: raise RuntimeError('generation failed')
        return 'First staged draft'
    provider.on_generate=fail_second
    with pytest.raises(RuntimeError,match='generation failed'):
        run(story,provider,lambda t,c,e:ContextReviewDecision('send',e))
    assert project.read_scene(target.id)=='' and project.read_scene(second.id)==''


def test_evidence_rejects_changed_quotes_offsets_manifest_and_unsent_sources(story):
    provider=Provider();contexts=[]
    run(story,provider,lambda t,c,e:(contexts.append(c) or ContextReviewDecision('send',e)))
    context=contexts[0];evidence=captured_passages(context)[0]
    with pytest.raises(ProjectError): validate_quote(context,evidence.source_id,evidence.start,evidence.end,'invented')
    with pytest.raises(ProjectError): validate_quote(context,'unknown',0,3,'abc')
    with pytest.raises(ProjectError): captured_passages(replace(context,prompt='Another request'))
    with pytest.raises(ProjectError): captured_passages(replace(context,manifest=replace(context.manifest,decisions=())))
    altered=context.context.replace('Distant evidence.','Invented evidence.')
    with pytest.raises(ProjectError): captured_passages(replace(context,context=altered,prompt=altered))


def test_retrieved_batch_still_rolls_back_transaction_and_preserves_source_review(story,monkeypatch):
    project,far,target,future,note,character,other,cache=story
    second=project.add_scene('Second silver compass scene',chapter_id=project.manifest.chapters[0].id)
    result=run(story,Provider(),lambda t,c,e:ContextReviewDecision('send',e))
    original_rename=Path.rename;failed=[False]
    second_path=project.root/second.path
    def fail_install(path,destination):
        if not failed[0] and path.name.endswith('.tmp') and Path(destination)==second_path:
            failed[0]=True;raise OSError('simulated install failure')
        return original_rename(path,destination)
    monkeypatch.setattr(Path,'rename',fail_install)
    with pytest.raises(ProjectError,match='could not replace'):
        project.replace_scenes_transactionally(dict(result.replacements),expected_contents=dict(result.expected_disk_text),
                                               expected_contexts=dict(result.expected_context_text))
    assert project.read_scene(target.id)=='' and project.read_scene(second.id)==''
    assert Path(result.snapshot_path).exists() and result.retrieval_contexts[target.id].passages
    assert not list(project.root.rglob('*.bak')) and not list(project.root.rglob('*.tmp'))


def test_quote_validation_survives_unicode_crlf_and_rejects_unselected_offsets(story):
    project,far,target,future,note,character,other,cache=story
    (project.root/far.path).write_bytes('The silver compass — срібний компас.\r\nТочна цитата.\r\n'.encode())
    contexts=[]
    run(story,Provider(),lambda t,c,e:(contexts.append(c) or ContextReviewDecision('send',e)))
    context=contexts[0];evidence=captured_passages(context)[0]
    assert '\r\n' in evidence.text
    start=evidence.start+evidence.text.index('срібний компас')
    assert validate_quote(context,far.id,start,start+len('срібний компас'),'срібний компас')==evidence
    with pytest.raises(ProjectError): validate_quote(context,far.id,-1,start,'wrong')


def test_cancelled_review_never_calls_generation(story):
    provider=Provider()
    with pytest.raises(ProjectError,match='cancelled'):
        run(story,provider,lambda t,c,e:ContextReviewDecision('cancel'))
    assert not provider.prompts


def test_scene_title_remains_query_authority_with_long_generic_style_instructions(story):
    project,far,target,future,note,character,other,cache=story
    seen=[]
    retrieval=AutoWriterRetrieval(cache,65536,lambda t,c,e:(seen.append(c) or ContextReviewDecision('send',e)))
    run_auto_writer(Provider(),project,'write_empty','Write only one short English sentence about finding the object; no title or explanation.',{},
                   maximum_tokens=300,temperature=0.2,snapshot_name='Title query',is_cancelled=lambda:False,retrieval=retrieval)
    assert any(item.source_id==far.id for item in captured_passages(seen[0]))


def test_disk_race_after_snapshot_and_before_capture_refuses_stale_mandatory_input(story,monkeypatch):
    project,far,target,future,note,character,other,cache=story
    original=RevisionStore.create
    def raced(store,*args,**kwargs):
        snapshot=original(store,*args,**kwargs)
        (project.root/far.path).write_text('Changed after snapshot',encoding='utf-8')
        return snapshot
    monkeypatch.setattr(RevisionStore,'create',raced)
    provider=Provider()
    with pytest.raises(ProjectError,match='disk context changed'):
        run(story,provider,lambda t,c,e:ContextReviewDecision('send',e))
    assert not provider.prompts and project.read_scene(target.id)==''


def test_hybrid_auto_writer_uses_shared_semantic_ranking_and_validated_evidence(story):
    from test_rag_embeddings import FakeEmbeddings
    project,far,target,future,note,character,other,cache=story
    contexts=[]
    retrieval=AutoWriterRetrieval(cache,65536,
        lambda t,c,e:(contexts.append(c) or ContextReviewDecision('send',e)),FakeEmbeddings())
    result=run(story,Provider(),lambda t,c,e:ContextReviewDecision('send',e),retrieval=retrieval)
    assert contexts[0].manifest.retrieval_method=='hybrid'
    assert result.retrieval_contexts[target.id].passages
    assert any(item.source_id==far.id for item in result.retrieval_contexts[target.id].passages)


def test_rebuild_cannot_exclude_required_reference_material(story):
    project,far,target,future,note,character,other,cache=story
    provider=Provider()
    with pytest.raises(ProjectError,match='complete reference material is required'):
        run(story,provider,lambda t,c,e:ContextReviewDecision('rebuild',frozenset({note.id})))
    assert not provider.prompts
