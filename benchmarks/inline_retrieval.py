"""Reproduce the predeclared RAG-08 workload; no Ollama or saved user settings."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import platform
import statistics
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.captured_completion import generate_captured_completion
from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.project import Project
from app.project.inline_context import InlineContextService
from app.project.rag_context import ContextRequest, RetrievalPolicy
from app.project.rag_index import LexicalIndex
from app.project.rag_sources import BufferText, capture_project_sources


class FakeGeneration:
    def generate_private(self, prompt, **kwargs):
        return " beyond"


def distribution(values):
    values = sorted(values)
    return {"median_ms": statistics.median(values) * 1000,
            "p95_ms": values[int((len(values)-1)*.95)] * 1000,
            "maximum_ms": max(values)*1000}


def run():
    with TemporaryDirectory(prefix="utexteditor-inline-") as temporary:
        root = Path(temporary)
        project = Project.create(root / "novel", "Synthetic inline workload")
        chapter = project.add_chapter("Chapter")
        sizes = []
        for number in range(100):
            text = (f"Scene {number}. The copper key unlocks the garden gate. "
                    "Марія пам'ятає сад і мідний ключ.\n\n") * 110
            project.add_scene(f"Scene {number}", chapter_id=chapter.id, content=text[:10240])
            sizes.append(len(text[:10240].encode("utf-8")))
        target = project.add_scene("Target", chapter_id=chapter.id, content="The copper key")
        index = LexicalIndex(root / "cache", project.root, project.manifest.project_id)
        index.refresh(capture_project_sources(project))
        service = InlineContextService()
        buffers = {target.id: BufferText("The copper key", 1)}
        base = ContextRequest(ContextPrompt("Continue"), ContextBudget(32768, 50),
                              "The copper key", current_passage="The copper key", target_scene_id=target.id,
                              policy=RetrievalPolicy(maximum_passages=4))
        result = {"environment": {"platform": platform.platform(), "python": platform.python_version()},
                  "workload": {"saved_scenes":101, "scene_bytes_min":min(sizes), "scene_bytes_max":max(sizes),
                               "total_earlier_scene_bytes":sum(sizes), "open_buffers":1,
                               "samples_per_mode":20, "p95_retrieval_target_ms":250}, "modes": {}}
        for mode in ("repeated", "distinct"):
            retrieval, generation, total, hits, states = [], [], [], [], []
            for number in range(21):
                query = "The copper key" if mode == "repeated" else f"The copper key query {number}"
                request = replace(base, current_passage=query)
                started = perf_counter()
                context = service.capture(project, index, request, buffers)
                generated_at = perf_counter()
                generated = generate_captured_completion(FakeGeneration(), context.captured, buffers, temperature=.2)
                finished = perf_counter()
                assert generated == " beyond"
                if number:
                    retrieval.append(context.retrieval_seconds)
                    generation.append(finished-generated_at)
                    total.append(finished-started)
                    hits.append(context.cache_hit)
                    states.append(context.captured.manifest.retrieval_state)
            result["modes"][mode] = {"retrieval": distribution(retrieval),
                "generation_with_source_verification_fake_provider": distribution(generation),
                "end_to_end_fake_provider": distribution(total), "cache_hits":sum(hits),
                "states":states, "target_met":distribution(retrieval)["p95_ms"] < 250}
        result["index_bytes"] = index.path.stat().st_size
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(run(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    print(report)
