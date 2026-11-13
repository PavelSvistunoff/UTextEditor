"""Unicode word boundaries shared by manuscript counts and writing goals."""

import re

WORD_PATTERN = re.compile(r"(?u)[^\W_]+(?:['’‐‑‒–—-][^\W_]+)*")


def count_words(text: str) -> int:
    """Count letter/digit runs with internal apostrophes and hyphens."""
    return len(WORD_PATTERN.findall(text))
