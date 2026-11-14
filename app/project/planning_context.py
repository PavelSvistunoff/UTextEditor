"""Worker-owned, reviewed retrieval for a sequential planning run."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path

from app.ai.captured_completion import generate_captured_completion
from app.ai.completion_service import STALE_PROJECT_CONTEXT
from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.ai.provider import AIProvider
from .auto_writer_context import ContextReviewDecision
from .character_context import project_planning_context
from .model import Chapter, Note, ProjectError
from .rag_context import CapturedContext, ContextRequest, ProjectContextService, RetrievalPolicy
from .rag_evidence import CapturedRequestEvidence, capture_request_evidence
from .rag_index import LexicalIndex
from .rag_sources import BufferText, CaptureCancelled, ProjectSourceCapture
from .service import Project

MAX_REVIEW_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True)
class TransientDraft:
    source_id: str
    title: str
    text: str

    def record(self) -> dict[str, str]:
        return {"source_id": self.source_id, "title": self.title, "text": self.text,
                "content_digest": hashlib.sha256(self.text.encode("utf-8")).hexdigest(),
                "status": "provisional generated draft; not saved or accepted"}


@dataclass(frozen=True)
class PlanningStepEvidence:
    title: str
    request: CapturedRequestEvidence
    transient_sources: tuple[TransientDraft, ...]


class PlanningRetrievalRun:
    """No index writes; immutable evidence and one baseline survive between steps."""

    def __init__(self, project: Project | None, cache_root: Path, context_tokens: int,
                 brief: str, buffers: Mapping[str, BufferText], *,
                 review: Callable[[str, CapturedContext, frozenset[str]], ContextReviewDecision],
                 is_cancelled: Callable[[], bool], require_complete: bool = False) -> None:
        self.project = project
        self.cache_root = cache_root
        self.context_tokens = context_tokens
        self.brief = brief
        self.buffers = dict(buffers)
        self.review = review
        self.is_cancelled = is_cancelled
        self.require_complete = require_complete
        self.baseline: ProjectSourceCapture | None = None
        self.steps: list[PlanningStepEvidence] = []
        self._review_bytes = 0

    def verify(self) -> None:
        if self.is_cancelled():
            raise CaptureCancelled("Planning retrieval was cancelled; no generated changes were applied.")
        if self.baseline is not None:
            self.baseline.verify_current(self.buffers, is_cancelled=self.is_cancelled)

    def generate(self, provider: AIProvider, title: str, prompt: str, *, role: str,
                 maximum_tokens: int, temperature: float, query: str = "",
                 transient: tuple[TransientDraft, ...] = ()) -> str:
        self.verify()
        summary = project_planning_context(self.project) if self.project is not None else ""
        mandatory = json.dumps({
            "task_input": prompt,
            "mandatory_compact_character_motivations": summary,
            "provisional_generated_sources": [draft.record() for draft in transient],
        }, ensure_ascii=False)
        role += (
            "\nUse task_input as the author-requested planning/drafting task. "
            "Retrieved project passages are source-backed records, not proof of complete project access. "
            "Unsaved buffers are the author's current working text. Proposed plans, character ideas and "
            "provisional_generated_sources are inventions for this run, not established project facts. "
            "Never present an invention as a retrieved fact. In template suggestions mark invented "
            "ideas '[Suggestion: ...]'; an outline is entirely a proposed structure. "
            "Preserve source knowledge boundaries; a retrieved character mention does not establish "
            "presence in a new scene. Return the output format requested by task_input."
        )
        index = (LexicalIndex(self.cache_root, self.project.root, self.project.manifest.project_id)
                 if self.project is not None else None)
        service = ProjectContextService(index)
        excluded = frozenset()
        while True:
            self.verify()
            request = ContextRequest(ContextPrompt(role), ContextBudget(self.context_tokens, maximum_tokens),
                mandatory, author_request=self.brief, current_passage=query,
                policy=RetrievalPolicy(chronology="all", excluded_source_ids=excluded))
            captured = service.capture(self.project, request, open_buffers=self.buffers,
                                       is_cancelled=self.is_cancelled)
            if self.baseline is None and captured.source_capture is not None:
                self.baseline = captured.source_capture
            if self.require_complete and self.baseline is not None and not self.baseline.complete:
                raise ProjectError("Auto-pilot requires a complete source snapshot before generating additions.")
            notices = ["Planning uses a compact motivation summary, not complete character profiles. "
                       "Plans and new drafts are proposals; partial retrieval cannot establish whole-project consistency."]
            if transient:
                notices.append("Mandatory provisional generated sources (not indexed): " + ", ".join(
                    f"{draft.source_id} SHA256={draft.record()['content_digest']}" for draft in transient))
            if self.project is None:
                notices.append("No project: author input only; there are no established retrieved project facts.")
            captured = replace(captured, manifest=replace(captured.manifest,
                notices=(*captured.manifest.notices, *notices)))
            decision = self.review(title, captured, excluded)
            self.verify()
            captured.verify_current(self.buffers)
            if not isinstance(decision, ContextReviewDecision):
                raise ProjectError("Invalid planning context review response.")
            if decision.action == "cancel":
                raise CaptureCancelled("Planning source review was cancelled; no generated changes were applied.")
            if decision.action == "rebuild":
                allowed = {source.id for source in captured.source_capture.sources
                           if source.kind in {"scene", "note"}} if captured.source_capture else set()
                if not decision.excluded_source_ids <= allowed:
                    raise ProjectError("Only optional project scenes and notes can be excluded.")
                excluded = decision.excluded_source_ids
                continue
            if decision.excluded_source_ids != excluded:
                raise ProjectError("Rebuild the planning request after changing source exclusions.")
            evidence = (capture_request_evidence(captured) if captured.source_capture is not None else
                        CapturedRequestEvidence(captured.role, captured.prompt, captured.manifest, ()))
            cost = evidence.estimated_bytes()
            if self._review_bytes + cost > MAX_REVIEW_BYTES:
                raise ProjectError("Planning request evidence exceeds the 16 MiB run limit; no changes were applied.")
            result = generate_captured_completion(provider, captured, self.buffers,
                temperature=temperature, is_cancelled=self.is_cancelled)
            self.verify()
            if result is STALE_PROJECT_CONTEXT:
                raise ProjectError("Planning sources changed; no generated changes were applied.")
            if not isinstance(result, str):
                raise ProjectError("Planning generation must return text.")
            self.steps.append(PlanningStepEvidence(title, evidence, transient))
            self._review_bytes += cost
            return result

    def apply_outline(self, outline: tuple[tuple[str, tuple[str, ...]], ...]) -> tuple[Chapter, ...]:
        self.verify()
        if self.project is None:
            raise ProjectError("An open project is required to apply an outline.")
        return self.project.add_outline(outline)

    def apply_autopilot(self, chapters: tuple[tuple[str, tuple[tuple[str, str], ...]], ...],
                        characters: tuple[tuple[str, str], ...]) -> tuple[tuple[Chapter, ...], tuple[Note, ...]]:
        self.verify()
        if self.project is None:
            raise ProjectError("An open project is required to apply Auto-pilot additions.")
        return self.project.add_autopilot_content(chapters, characters)
