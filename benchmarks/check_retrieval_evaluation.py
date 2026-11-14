"""Check frozen RAG-07 numerical gates from committed, reproducible raw reports."""

import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def check_reports(directory: Path) -> dict[str,bool]:
    corpus_path=ROOT/'benchmarks/data/retrieval-evaluation-v1.json'
    corpus=json.loads(corpus_path.read_text())
    protocol=json.loads((directory/'protocol.json').read_text())
    reports={name:json.loads((directory/(name+'.json')).read_text())
             for name in ('fixed','lexical','hybrid-development','hybrid-heldout')}
    digest=hashlib.sha256(corpus_path.read_bytes()).hexdigest()
    criteria=protocol['protocol']['gates']
    checks={'frozen_corpus_hash':digest==protocol['corpus_sha256'] and all(r['corpus_sha256']==digest for r in reports.values())}
    heldout=reports['hybrid-heldout']
    expected={q['key']:q for q in corpus['queries'] if q['split']=='heldout'}
    checks['heldout_cases_complete']=({r['query'] for r in heldout['queries']}==set(expected)
                                    and len(heldout['queries'])==len(expected))
    checks['heldout_labels_match']=all(r['expected']==expected[r['query']]['expected'] for r in heldout['queries'])
    checks['hybrid_really_used']=all(r['actual_method']=='hybrid' for r in heldout['queries'])
    checks['vector_cache_bound']=heldout['vector_cache_bytes']<=criteria['vector_cache_bytes_max']
    for language in ('en','uk'):
        metrics=heldout['metrics']['heldout'][language]
        lexical=reports['lexical']['metrics']['heldout'][language]
        checks[language+'_recall']=metrics['recall_at_3']>=criteria['heldout_hybrid_recall_at_3_per_language_min']
        checks[language+'_precision']=metrics['precision_at_3_fixed_slots']>=criteria['heldout_hybrid_precision_at_3_per_language_min']
        checks[language+'_no_lexical_regression']=metrics['recall_at_3']>=lexical['recall_at_3']
        checks[language+'_chronology']=metrics['chronology_violations']<=criteria['chronology_violations_max']
        checks[language+'_validated_evidence']=metrics['validated_passage_fraction']>=criteria['validated_passage_fraction_min']
        checks[language+'_absence_warning']=metrics['absent_warning_fraction']>=criteria['absent_warning_fraction_min']
        checks[language+'_latency']=metrics['warm_query_p95_seconds']<=criteria['warm_query_p95_seconds_max']
    return checks


if __name__=='__main__':
    result=check_reports(ROOT/'docs/evidence/rag07')
    print(json.dumps(result,indent=2))
    if not all(result.values()): raise SystemExit(1)
