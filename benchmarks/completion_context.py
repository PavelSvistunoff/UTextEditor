"""Compare bounded completion context construction with the previous approach.

Run from the repository root: .venv/bin/python benchmarks/completion_context.py
"""

import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.completion_service import build_context


def previous_context(text: str, cursor: int, limit: int = 4000) -> str:
    before = text[:cursor]
    separator = before.rfind("\n\n")
    return before[max(separator + 2 if separator >= 0 else 0, len(before) - limit):]


def measure(function, text: str, cursor: int, iterations: int = 100) -> tuple[float, int]:
    tracemalloc.start()
    start = time.perf_counter()
    for _ in range(iterations):
        function(text, cursor)
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return elapsed, peak


def main() -> None:
    text = "word " * 1_000_000
    cursor = len(text) // 2
    assert previous_context(text, cursor) == build_context(text, cursor)
    for name, function in (("previous", previous_context), ("current", build_context)):
        elapsed, peak = measure(function, text, cursor)
        print(f"{name}: {elapsed:.4f} s / 100 calls; peak Python allocation {peak:,} bytes")


if __name__ == "__main__":
    main()
