"""Reviewed manuscript retrieval for one sequential Auto-writer run."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
import json

from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.ai.embeddings import EmbeddingProvider
from .model import ProjectError
from .rag_context import CapturedContext, ContextRequest, ProjectContextService, RetrievalPolicy
from .rag_embeddings import SemanticRetriever
from .rag_evidence import captured_passages
from .rag_index import LexicalIndex
from .rag_sources import BufferText
from .service import Project


@dataclass(frozen=True)
class ContextReviewDecision:
    action: str
    excluded_source_ids: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if self.action not in {"send", "rebuild", "cancel"}:
            raise ValueError("Unknown captured-context review decision.")
        if not isinstance(self.excluded_source_ids, frozenset) or any(
            not isinstance(item, str) for item in self.excluded_source_ids
        ):
            raise ValueError("Excluded sources must be an immutable set of IDs.")


@dataclass(frozen=True)
class AutoWriterRetrieval:
    cache_root: Path
    context_tokens: int
    review: Callable[[str, CapturedContext, frozenset[str]], ContextReviewDecision]
    embedding_provider: EmbeddingProvider | None = None

    def prepare(self, project: Project, scene_id: str, title: str, mandatory_prompt: str,
                role: str, instructions: str, current_text: str,
                open_text: Mapping[str, str | None], generated: Mapping[str, str], *,
                expected_disk: Mapping[str, str], output_tokens: int,
                is_cancelled: Callable[[], bool]) -> CapturedContext:
        # These overlays are internal working drafts, never accepted text or disk/cache writes.
        buffers = {item_id: BufferText(text, 0) for item_id, text in open_text.items() if text is not None}
        buffers.update({item_id: BufferText(text, 1) for item_id, text in generated.items()})
        draft_ids = tuple(sorted(generated))
        if draft_ids:
            mandatory_prompt += ("\nProvisional earlier drafts generated in this run (not saved or accepted): "
                                 + json.dumps(draft_ids) + ". Retrieved spans bearing these IDs may depend on drafts later rejected.")
        index = LexicalIndex(self.cache_root, project.root, project.manifest.project_id)
        semantic = SemanticRetriever(self.embedding_provider, index) if self.embedding_provider is not None else None
        service = ProjectContextService(index, semantic=semantic)
        request_role = (
            role + "\nDraft the complete target scene from the captured project input. "
            "For a nonempty current scene, preserve its core events, point of view and established facts. "
            "Only explicit scene associations establish target presence; retrieved passages are background. "
            "Follow these author writing instructions: " + (instructions or "No additional instructions.")
        )
        excluded = frozenset()
        while True:
            if is_cancelled():
                raise ProjectError("Auto-writer context review was cancelled.")
            request = ContextRequest(
                ContextPrompt(request_role), ContextBudget(self.context_tokens, output_tokens), mandatory_prompt,
                author_request=title + "\n" + instructions, current_passage=current_text,
                target_scene_id=scene_id,
                policy=RetrievalPolicy(allowed_kinds=frozenset({"scene"}), excluded_source_ids=excluded),
            )
            captured = service.capture(project, request, open_buffers=buffers, is_cancelled=is_cancelled)
            actual_disk = {source.id: source.text for source in captured.source_capture.disk_sources
                           if source.relative_path is not None}
            if any(actual_disk.get(item_id) != text for item_id, text in expected_disk.items()):
                raise ProjectError("Auto-writer disk context changed or could not be captured completely; no scenes were changed.")
            passages = captured_passages(captured)
            generated_evidence = sorted({item.source_id for item in passages} & set(draft_ids))
            if generated_evidence:
                captured = replace(captured, manifest=replace(captured.manifest, notices=(
                    *captured.manifest.notices,
                    "Provisional generated-draft evidence (not saved or accepted): " + ", ".join(generated_evidence),
                )))
            decision = self.review(title, captured, excluded)
            if not isinstance(decision, ContextReviewDecision):
                raise ProjectError("Invalid Auto-writer source review response.")
            self.verify(captured, is_cancelled=is_cancelled)
            if decision.action == "cancel":
                raise ProjectError("Auto-writer context review was cancelled; no scenes were changed.")
            if decision.action == "send":
                if decision.excluded_source_ids != excluded:
                    raise ProjectError("Rebuild the captured request after changing excluded sources.")
                return captured
            if not decision.excluded_source_ids <= {scene.id for scene in project.iter_scenes()}:
                raise ProjectError("Only optional manuscript scenes can be excluded; complete reference material is required.")
            excluded = decision.excluded_source_ids

    @staticmethod
    def verify(captured: CapturedContext, *, is_cancelled: Callable[[], bool]) -> None:
        if captured.source_capture is None:
            raise ProjectError("Auto-writer retrieval requires project sources.")
        buffers = {source.id: BufferText(source.text, source.buffer_revision)
                   for source in captured.source_capture.sources if source.buffer_revision is not None}
        captured.source_capture.verify_current(buffers, is_cancelled=is_cancelled)
        captured_passages(captured)
