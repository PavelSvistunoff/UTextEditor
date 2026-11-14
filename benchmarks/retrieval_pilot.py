"""Versioned model-selection pilot using production capture/ranking, synthetic data only."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import statistics
import sys
import tempfile
from time import perf_counter
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.ai.ollama_client import OllamaClient
from app.project import Project
from app.project.rag_context import ContextRequest, ProjectContextService, RetrievalPolicy
from app.project.rag_embeddings import SemanticRetriever
from app.project.rag_index import LexicalIndex
from app.project.rag_sources import capture_project_sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model")
    parser.add_argument("--host", default="http://localhost:11434")
    parser.add_argument("--live", action="store_true", help="Explicitly allow synthetic text to this embedding destination")
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if options.model and not options.live:
        parser.error("Embedding evaluation requires explicit --live consent")
    corpus = json.loads((ROOT / "benchmarks/data/retrieval-pilot-v1.json").read_text())
    with tempfile.TemporaryDirectory(prefix="utexteditor-retrieval-pilot-") as directory:
        root = Path(directory)
        project = Project.create(root / "project", "Synthetic pilot")
        mapping = {}
        for source in corpus["sources"]:
            note = project.add_note(source["title"], content=source["text"])
            note.id = str(uuid5(NAMESPACE_URL, "utexteditor-pilot-v1/" + source["id"]))
            mapping[note.id] = source["id"]
        project._write_manifest()
        index = LexicalIndex(root / "cache", project.root, project.manifest.project_id)
        start = perf_counter()
        index.refresh(capture_project_sources(project))
        index_seconds = perf_counter() - start
        provider = OllamaClient(options.host, options.model, timeout=30) if options.model else None
        identity = provider.embedding_identity() if provider else None
        semantic = SemanticRetriever(provider, index) if provider else None
        service = ProjectContextService(index, semantic=semantic)
        rows = []
        for query in corpus["queries"]:
            request = ContextRequest(ContextPrompt("Story assistant"), ContextBudget(65536, 100),
                                     mandatory_text=query["text"], author_request=query["text"],
                                     policy=RetrievalPolicy(maximum_passages=3))
            start = perf_counter()
            result = service.capture(project, request)
            elapsed = perf_counter() - start
            found = list(dict.fromkeys(mapping[item.source_id] for item in result.manifest.decisions
                                       if item.disposition in {"included", "shortened"}))
            expected = set(query["relevant"])
            rows.append({"query": query["id"], "language": query["language"], "expected": sorted(expected),
                         "found": found, "recall_at_1": int(bool(expected & set(found[:1]))),
                         "recall_at_3": int(bool(expected & set(found[:3]))),
                         "precision_at_3": len(expected & set(found[:3])) / max(1, len(found[:3])),
                         "seconds": elapsed, "prompt_bytes": len(result.prompt.encode()),
                         "method": result.manifest.retrieval_method, "notices": result.manifest.notices})
        metrics = {}
        for language in ("en", "uk"):
            positives = [row for row in rows if row["language"] == language and row["expected"]]
            negatives = [row for row in rows if row["language"] == language and not row["expected"]]
            metrics[language] = {key: statistics.mean(row[key] for row in positives)
                                 for key in ("recall_at_1", "recall_at_3", "precision_at_3")}
            metrics[language]["absent_queries_with_candidates"] = sum(bool(row["found"]) for row in negatives)
        warm = sorted(row["seconds"] for row in rows[1:])
        result = {"corpus_version": corpus["version"], "predeclared": corpus["predeclared"],
                  "hardware": platform.platform(), "identity": asdict(identity) if identity else None,
                  "index_seconds": index_seconds, "lexical_cache_bytes": index.path.stat().st_size,
                  "vector_cache_bytes": semantic.cache.path.stat().st_size if semantic and semantic.cache.path.exists() else 0,
                  "cold_first_query_seconds": rows[0]["seconds"],
                  "warm_query_p95_seconds": warm[min(len(warm)-1, int(len(warm)*0.95))],
                  "metrics": metrics, "queries": rows}
        options.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({key: result[key] for key in ("identity", "metrics", "cold_first_query_seconds", "warm_query_p95_seconds", "vector_cache_bytes")}, indent=2))


if __name__ == "__main__":
    main()
