"""Validate structured, evidence-linked continuity findings from untrusted AI."""

from dataclasses import dataclass
import json
import re


@dataclass(frozen=True)
class ContinuityFinding:
    confidence: str
    scene_id: str
    character_ids: tuple[str, ...]
    concern: str
    source_id: str
    quote: str
    suggestion: str


def parse_continuity_findings(response: object, *, scene_id: str,
                              character_ids: set[str], sources: dict[str, str]) -> tuple[ContinuityFinding, ...]:
    if not isinstance(response, str) or len(response) > 60_000:
        raise ValueError("The model returned an invalid or oversized continuity response.")
    response = response.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", response, re.IGNORECASE | re.DOTALL)
    if fenced:
        response = fenced.group(1)
    try:
        payload = json.loads(response)
    except (ValueError, TypeError) as exc:
        raise ValueError("The model did not return valid continuity JSON.") from exc
    if not isinstance(payload, dict) or set(payload) != {"findings"} or not isinstance(payload["findings"], list) or len(payload["findings"]) > 50:
        raise ValueError("The model returned an invalid continuity findings list.")
    findings = []
    for row in payload["findings"]:
        required = {"confidence", "scene_id", "character_ids", "concern", "evidence", "suggestion"}
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError("The model returned an invalid continuity finding.")
        confidence, characters, evidence = row["confidence"], row["character_ids"], row["evidence"]
        if confidence not in ("definite", "probable", "possible") or row["scene_id"] != scene_id:
            raise ValueError("The model returned an invalid confidence or scene ID.")
        if not isinstance(characters, list) or len(characters) > len(character_ids) or any(not isinstance(item, str) or item not in character_ids for item in characters) or len(set(characters)) != len(characters):
            raise ValueError("The model referenced an unassociated character.")
        if not isinstance(evidence, dict) or set(evidence) != {"source_id", "quote"}:
            raise ValueError("The model returned invalid evidence.")
        source_id, quote = evidence["source_id"], evidence["quote"]
        if not isinstance(source_id, str) or source_id not in sources or not isinstance(quote, str) or not quote.strip() or len(quote) > 1000 or quote not in sources[source_id]:
            raise ValueError("The model cited evidence outside the captured source text.")
        for key in ("concern", "suggestion"):
            value = row[key]
            if not isinstance(value, str) or not value.strip() or len(value) > 2000 or "\x00" in value:
                raise ValueError("The model returned invalid finding text.")
        findings.append(ContinuityFinding(confidence, scene_id, tuple(characters), row["concern"].strip(), source_id, quote, row["suggestion"].strip()))
    return tuple(findings)


def format_continuity_findings(findings: tuple[ContinuityFinding, ...]) -> str:
    if not findings:
        return "No continuity findings were returned. This does not establish that the scene is consistent."
    return "\n\n".join(
        f"{index}. {finding.confidence.upper()} — {finding.concern}\n"
        f"Scene: {finding.scene_id}\nCharacters: {', '.join(finding.character_ids) or 'none'}\n"
        f"Evidence ({finding.source_id}): {finding.quote}\nSuggested review: {finding.suggestion}"
        for index, finding in enumerate(findings, 1)
    )
