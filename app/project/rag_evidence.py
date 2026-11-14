"""Validate optional passage evidence against the exact captured request."""

from dataclasses import dataclass
import json

from .model import ProjectError
from .rag_context import CapturedContext, ContextManifest


@dataclass(frozen=True)
class CapturedEvidence:
    source_id: str
    chunk_id: str
    title: str
    start: int
    end: int
    text: str
    content_digest: str
    metadata_digest: str
    buffer_revision: int | None


@dataclass(frozen=True)
class CapturedRequestEvidence:
    """Verified immutable review record; does not retain the entire project corpus."""
    role: str
    prompt: str
    manifest: ContextManifest
    passages: tuple[CapturedEvidence, ...]

    def estimated_bytes(self) -> int:
        return (len(self.role.encode("utf-8")) + len(self.prompt.encode("utf-8"))
                + len(self.manifest.to_json().encode("utf-8"))
                + sum(len(item.text.encode("utf-8")) for item in self.passages))


def capture_request_evidence(context: CapturedContext) -> CapturedRequestEvidence:
    return CapturedRequestEvidence(context.role, context.prompt, context.manifest, captured_passages(context))


def captured_passages(context: CapturedContext) -> tuple[CapturedEvidence, ...]:
    """Only actual sent optional spans qualify as source-backed evidence."""
    if context.source_capture is None or context.context not in context.prompt:
        raise ProjectError("Evidence is not bound to a captured project request.")
    try:
        payload = json.loads(context.context.split("<captured_context>\n", 1)[1].rsplit("\n</captured_context>", 1)[0])
        passages = payload["passages"]
        if not isinstance(passages, list):
            raise ValueError("Invalid passage list")
        sources = {source.id: source for source in context.source_capture.sources}
        chunks = {chunk.id: chunk for chunk in context.source_capture.chunks}
        decisions = {(item.source_id, item.chunk_id, item.start, item.end): item
                     for item in context.manifest.decisions if item.disposition in {"included", "shortened"}}
        evidence = []
        seen = set()
        for passage in passages:
            source_id, chunk_id = passage["source_id"], passage["chunk_id"]
            start, end = passage["range"]
            if type(start) is not int or type(end) is not int:
                raise ValueError("Invalid evidence offsets")
            key = (source_id, chunk_id, start, end)
            decision = decisions[key]
            source, chunk = sources[source_id], chunks[chunk_id]
            if (key in seen or chunk.source != source or not chunk.start <= start < end <= chunk.end
                    or source.text[start:end] != passage["text"]
                    or passage["title"] != source.title
                    or passage["content_digest"] != source.content_digest
                    or passage["metadata_digest"] != source.metadata_digest
                    or passage["buffer_revision"] != source.buffer_revision
                    or decision.content_digest != source.content_digest
                    or decision.metadata_digest != source.metadata_digest):
                raise ValueError("Captured evidence provenance does not match")
            seen.add(key)
            evidence.append(CapturedEvidence(source_id, chunk_id, source.title, start, end,
                                            passage["text"], source.content_digest,
                                            source.metadata_digest, source.buffer_revision))
        if seen != set(decisions):
            raise ValueError("Manifest and sent evidence differ")
        return tuple(evidence)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ProjectError("Retrieved evidence does not match the captured request.") from exc


def validate_quote(context: CapturedContext, source_id: str, start: int, end: int, quote: str) -> CapturedEvidence:
    """Validate a finding's exact quote inside an actually sent passage."""
    if type(start) is not int or type(end) is not int or not isinstance(quote, str) or not quote:
        raise ProjectError("Evidence requires nonempty text and exact source offsets.")
    for passage in captured_passages(context):
        if (passage.source_id == source_id and passage.start <= start < end <= passage.end
                and passage.text[start - passage.start:end - passage.start] == quote):
            return passage
    raise ProjectError("The quotation was not included in this captured request.")
