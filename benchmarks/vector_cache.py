"""Offline resource probe for the bounded exact-scan vector store; no AI calls."""

from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import tempfile
from time import perf_counter
import tracemalloc

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.ai.embeddings import EmbeddingIdentity, normalized_vector
from app.project.rag_embeddings import MAX_SEMANTIC_CHUNKS, VectorCache, semantic_order
from app.project.rag_index import LexicalIndex


def main():
    identity = EmbeddingIdentity("offline","synthetic","probe-v1",768)
    tracemalloc.start()
    values = {hashlib.sha256(str(row).encode()).hexdigest():normalized_vector(
        tuple(math.sin(column + row * 0.11) for column in range(identity.dimensions)),identity.dimensions)
        for row in range(MAX_SEMANTIC_CHUNKS)}
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        cache = VectorCache(LexicalIndex(root / "cache",root / "project","resource-probe"))
        start = perf_counter()
        cache.write(identity,values,verify=lambda:None,is_cancelled=lambda:False)
        write_seconds = perf_counter() - start
        start = perf_counter()
        loaded = cache.read(identity)
        read_seconds = perf_counter() - start
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        query = next(iter(loaded.values()))
        samples = []
        for _ in range(10):
            start = perf_counter()
            semantic_order(loaded,query)
            samples.append(perf_counter()-start)
        print(json.dumps({"hardware":platform.platform(),"vectors":len(values),"dimensions":identity.dimensions,
                          "cache_bytes":cache.path.stat().st_size,"traced_python_peak_bytes":peak,
                          "write_seconds_with_tracing":write_seconds,"read_seconds_with_tracing":read_seconds,
                          "scan_median_seconds":statistics.median(samples),"scan_max_seconds":max(samples)},indent=2))


if __name__ == "__main__":
    main()
