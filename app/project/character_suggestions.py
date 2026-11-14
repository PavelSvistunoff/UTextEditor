"""Generate character suggestions with complete, verified project-note context."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from app.ai.character_profile import suggest_character_fields
from app.ai.provider import AIProvider
from .analysis_context import AnalysisRetrieval
from .reference_context import ProjectNotes, capture_project_notes
from .service import Project
from .model import ProjectError


@dataclass(frozen=True)
class CharacterSuggestions:
    values: dict[str, str]
    references: ProjectNotes
    retrieval: AnalysisRetrieval | None = None

    def verify_current(self) -> None:
        self.references.verify_current()
        if self.retrieval is not None:
            self.retrieval.verify_current()


def suggest_project_character_fields(
    provider: AIProvider, project: Project, fields: dict[str, str], language: str,
    temperature: float, open_notes: Mapping[str, str | None], *, fallback_language: str,
    is_cancelled: Callable[[], bool] | None = None,
    retrieval: AnalysisRetrieval | None = None,
) -> CharacterSuggestions:
    def check_cancelled() -> None:
        if is_cancelled is not None and is_cancelled():
            raise ProjectError("Character suggestions were cancelled.")

    check_cancelled()
    references = capture_project_notes(project, open_notes)
    if retrieval is not None:
        retrieval.mandatory_source_ids |= frozenset(note.id for note in references.notes)
        retrieval.required_texts = {note.id: note.text for note in references.notes}
    check_cancelled()
    values = suggest_character_fields(
        provider, fields, language, temperature, fallback_language=fallback_language,
        reference_notes=references.text, retrieval=retrieval,
    )
    check_cancelled()
    references.verify_current()
    return CharacterSuggestions(values, references, retrieval)
