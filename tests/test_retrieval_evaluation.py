"""Frozen heldout evaluation gates stay reproducible and reject regressions."""

import json
from pathlib import Path
import runpy
import shutil


def test_frozen_heldout_reports_pass_and_a_recall_regression_fails(tmp_path):
    root=Path(__file__).resolve().parents[1]
    check=runpy.run_path(str(root/'benchmarks/check_retrieval_evaluation.py'))['check_reports']
    reports=root/'docs/evidence/rag07'
    assert all(check(reports).values())
    for path in reports.glob('*.json'): shutil.copyfile(path,tmp_path/path.name)
    path=tmp_path/'hybrid-heldout.json'
    data=json.loads(path.read_text())
    data['metrics']['heldout']['uk']['recall_at_3']=0.5
    path.write_text(json.dumps(data))
    assert not check(tmp_path)['uk_recall']
