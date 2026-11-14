"""Frozen RAG-07 development/heldout comparison; synthetic projects only."""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys
import tempfile
from time import perf_counter
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.ai.ollama_client import OllamaClient
from app.project import Project, SceneCharacterAssociation
from app.project.rag_context import ContextRequest, ProjectContextService, RetrievalPolicy
from app.project.rag_embeddings import SemanticRetriever
from app.project.rag_evidence import captured_passages
from app.project.rag_index import LexicalIndex
from app.project.rag_sources import capture_project_sources
from app.settings.settings import AppSettings


def summarize(rows):
    metrics = {}
    for split in ('development','heldout'):
        metrics[split] = {}
        for language in ('en','uk'):
            subset = [r for r in rows if r['split']==split and r['language']==language]
            positives = [r for r in subset if r['expected']]
            negatives = [r for r in subset if not r['expected']]
            if not subset: continue
            warm = sorted(r['seconds'] for r in subset if not r['cold'])
            metrics[split][language] = {
                'positive_queries':len(positives),'negative_queries':len(negatives),
                'recall_at_1':statistics.mean(r['recall_at_1'] for r in positives),
                'recall_at_3':statistics.mean(r['recall_at_3'] for r in positives),
                'precision_at_3_fixed_slots':statistics.mean(r['precision_at_3'] for r in positives),
                'chronology_violations':sum(r['chronology_violations'] for r in subset),
                'absent_queries_with_candidates':sum(bool(r['found']) for r in negatives),
                'absent_warning_fraction':statistics.mean(r['partial_warning'] for r in negatives) if negatives else 1,
                'validated_passage_fraction':sum(r['validated'] for r in subset)/max(1,sum(r['passages'] for r in subset)),
                'warm_query_p95_seconds':warm[min(len(warm)-1,int(len(warm)*0.95))] if warm else 0,
                'max_request_bytes':max(r['request_bytes'] for r in subset),
            }
    return metrics


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['fixed','lexical','hybrid'],required=True)
    parser.add_argument('--split',choices=['development','heldout','all'],required=True)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    options=parser.parse_args()
    if options.mode=='hybrid' and not options.live: parser.error('Synthetic embedding calls require explicit --live')
    corpus_path=ROOT/'benchmarks/data/retrieval-evaluation-v1.json'
    corpus=json.loads(corpus_path.read_text())
    digest=hashlib.sha256(corpus_path.read_bytes()).hexdigest()
    protocol=json.loads((ROOT/'docs/evidence/rag07/protocol.json').read_text())
    if digest!=protocol['corpus_sha256']: parser.error('Frozen corpus hash changed; create a new protocol/holdout')
    settings=AppSettings.load()
    provider=OllamaClient(settings.embedding_host,settings.embedding_model,timeout=30) if options.mode=='hybrid' else None
    identity=provider.embedding_identity() if provider else None
    with tempfile.TemporaryDirectory(prefix='utexteditor-rag07-evaluation-') as directory:
        root=Path(directory)
        project=Project.create(root/'project','Synthetic RAG-07 evaluation')
        chapter=project.add_chapter('Manuscript')
        source_keys={}
        past=[]
        for source in corpus['sources']:
            scene=project.add_scene(source['title'],chapter_id=chapter.id,content=source['text'])
            scene.id=str(uuid5(NAMESPACE_URL,'utexteditor-rag07-v1/'+source['key']))
            source_keys[scene.id]=source['key'];past.append(scene)
        target=project.add_scene('Recall earlier facts',chapter_id=chapter.id,content='The travellers needed to recall earlier events.')
        forbidden=set()
        for source in corpus['future_sources']:
            scene=project.add_scene(source['title'],chapter_id=chapter.id,content=source['text'])
            scene.id=str(uuid5(NAMESPACE_URL,'utexteditor-rag07-v1/'+source['key']))
            source_keys[scene.id]=source['key'];forbidden.add(scene.id)
        source=corpus['unplaced']
        unplaced=project.add_scene(source['title'],content=source['text'])
        source_keys[unplaced.id]=source['key'];forbidden.add(unplaced.id)
        cast={}
        for item in corpus['characters']:
            character=project.add_character(item['name']);character.aliases=item['aliases']
            project.update_character(character.id,character);cast[item['key']]=character
        project._write_manifest()
        index=LexicalIndex(root/'cache',project.root,project.manifest.project_id)
        if options.mode!='fixed': index.refresh(capture_project_sources(project))
        semantic=SemanticRetriever(provider,index) if provider else None
        service=ProjectContextService(index,semantic=semantic)
        rows=[]
        for question in corpus['queries']:
            if options.split!='all' and question['split']!=options.split: continue
            target.character_associations=[]
            if question.get('character'):
                target.character_associations=[SceneCharacterAssociation(cast[question['character']].id)]
            project._write_manifest()
            start=perf_counter()
            if options.mode=='fixed':
                # Exact existing last-two/first-1000 manuscript-context policy; facts here live in scenes, not required notes.
                found=[source_keys[scene.id] for scene in past[-2:]]
                prompt='\n'.join(scene.title+'\n'+project.read_scene(scene.id)[:1000] for scene in past[-2:])
                validated=0;count=2;violations=0;partial_warning=False
                actual_method='fixed'
            else:
                request=ContextRequest(ContextPrompt('Author-controlled writing assistant'),ContextBudget(65536,100),
                    project.read_scene(target.id),author_request=question['text'],target_scene_id=target.id,
                    policy=RetrievalPolicy(allowed_kinds=frozenset({'scene'}),maximum_passages=3))
                context=service.capture(project,request)
                evidence=captured_passages(context)
                found=list(dict.fromkeys(source_keys[item.source_id] for item in evidence))
                prompt=context.prompt;validated=len(evidence);count=len(evidence)
                violations=sum(item.source_id in forbidden for item in evidence)
                partial_warning='Partial retrieval and no hits do not establish project-wide consistency.' in context.context
                actual_method=context.manifest.retrieval_method
            elapsed=perf_counter()-start
            expected=set(question['expected'])
            rows.append({'query':question['key'],'split':question['split'],'language':question['language'],
                'expected':sorted(expected),'found':found,'recall_at_1':int(bool(expected&set(found[:1]))),
                'recall_at_3':int(bool(expected&set(found[:3]))),'precision_at_3':len(expected&set(found[:3]))/3,
                'seconds':elapsed,'cold':len(rows)==0,'request_bytes':len(prompt.encode('utf-8')),
                'validated':validated,'passages':count,'chronology_violations':violations,'partial_warning':partial_warning,
                'actual_method':actual_method})
        report={'corpus_version':corpus['version'],'corpus_sha256':digest,'mode':options.mode,'split':options.split,
                'hardware':platform.platform(),'embedding_identity':identity.__dict__ if identity else None,
                'lexical_cache_bytes':index.path.stat().st_size if index.path.exists() else 0,
                'vector_cache_bytes':semantic.cache.path.stat().st_size if semantic and semantic.cache.path.exists() else 0,
                'metrics':summarize(rows),'queries':rows}
        options.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(report['metrics'],indent=2))


if __name__=='__main__': main()
