import json

import pytest

from app.ai.continuity import format_continuity_findings, parse_continuity_findings


def finding():
    return {"confidence": "probable", "scene_id": "scene", "character_ids": ["mara"],
            "concern": "The timeline may conflict.",
            "evidence": {"source_id": "note", "quote": "arrived Tuesday"},
            "suggestion": "Check the arrival date."}


def parse(row):
    return parse_continuity_findings(json.dumps({"findings": [row]}), scene_id="scene",
                                     character_ids={"mara"}, sources={"scene": "Scene", "note": "Mara arrived Tuesday."})


def test_continuity_validates_and_renders_evidence():
    findings = parse(finding())
    assert findings[0].character_ids == ("mara",)
    assert "arrived Tuesday" in format_continuity_findings(findings)


@pytest.mark.parametrize("field,value", [
    ("scene_id", "other"), ("character_ids", ["other"]), ("confidence", "certain"),
    ("evidence", {"source_id": "note", "quote": "invented"}),
    ("evidence", {"source_id": "other", "quote": "Scene"}),
    ("concern", ""),
])
def test_continuity_rejects_untrusted_or_out_of_scope_findings(field, value):
    row = finding()
    row[field] = value
    with pytest.raises(ValueError):
        parse(row)


def test_continuity_rejects_malformed_response():
    with pytest.raises(ValueError):
        parse_continuity_findings("not json", scene_id="scene", character_ids=set(), sources={})
