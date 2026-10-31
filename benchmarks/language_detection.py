"""Evaluate the regression corpus against an always-Auto baseline, offline.

This curated corpus measures regression behavior, not real-world accuracy.
Run: PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/language_detection.py
"""

from collections import Counter
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai.prompts import detect_language


def main() -> None:
    cases = runpy.run_path(str(ROOT / "tests" / "language_corpus.py"))["CASES"]
    expected_counts = Counter(expected for _, expected in cases)
    results = [(text, expected, detect_language(text)) for text, expected in cases]
    matched = sum(expected == actual for _, expected, actual in results)
    unsupported_guesses = sum(actual != "Auto" and actual != expected for _, expected, actual in results)
    print(f"Cases: {len(cases)}; expected labels: {dict(expected_counts)}")
    print(f"Always-Auto baseline: {expected_counts['Auto']}/{len(cases)} matching labels")
    print(f"Current detector: {matched}/{len(cases)} matching labels; "
          f"unsupported confident guesses: {unsupported_guesses}")
    for text, expected, actual in results:
        if actual != expected:
            print(f"Mismatch: {expected} -> {actual}: {text!r}")
    if matched != len(cases):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
