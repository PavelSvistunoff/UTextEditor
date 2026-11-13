"""Check the standalone history probe on a short, deterministic workload."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("workload,expected", [("append", 9), ("mixed", 3)])
def test_history_benchmark_checks_undo_redo_and_branch(workload, expected):
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, str(root / "benchmarks/writing_goal_history.py"),
         "--commands", "9", "--undo", "4", "--workload", workload],
        cwd=root, env=env, capture_output=True, text=True, timeout=30, check=True,
    )
    assert f"New-word counts: before undo {expected}" in result.stdout
    assert "After undo and branch:" in result.stdout
