"""Conflict-aware saving for a captured scene/note binding, without Qt state."""

from dataclasses import dataclass

from app.document.encoding import normalize_line_endings
from .service import Project
from .model import ProjectError


@dataclass
class ProjectDocumentBinding:
    project: Project
    kind: str
    item_id: str
    expected_text: str


def save_project_document(
    binding: ProjectDocumentBinding, text: str, line_ending: str
) -> tuple[str, Project]:
    persisted_text = normalize_line_endings(text, line_ending)
    fresh_project = Project.open(binding.project.root)
    if binding.kind == "scene":
        old_path = binding.project.get_scene(binding.item_id).path
        fresh_item = fresh_project.get_scene(binding.item_id)
    else:
        old_path = binding.project.get_note(binding.item_id).path
        fresh_item = fresh_project.get_note(binding.item_id)
    if fresh_item.path != old_path:
        raise ProjectError("Project item moved or was relinked externally; reopen or Save As before saving.")
    if binding.kind == "scene":
        fresh_project.write_scene(
            binding.item_id, persisted_text, expected_content=binding.expected_text
        )
    else:
        fresh_project.write_note(
            binding.item_id, persisted_text, expected_content=binding.expected_text
        )
    return persisted_text, fresh_project
