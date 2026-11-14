"""Captured, bounded scene analysis and evidence validation for worker calls."""

from app.project.service import Project
from app.project.character_context import capture_scene_character_context
from .provider import AIProvider
from .context_budget import ContextBudgetError
from .continuity import parse_continuity_findings, format_continuity_findings


def run_project_analysis(
    provider: AIProvider,
    project: Project,
    task: str,
    scene_id: str,
    note_ids: tuple[str, ...],
    open_text: dict[str, str],
    maximum_context: int,
    role: str,
    maximum_tokens: int,
    temperature: float,
) -> str:
    if task not in {"summary", "continuity"}:
        raise ValueError("Unknown project analysis task.")
    if type(maximum_context) is not int or maximum_context <= 0:
        raise ValueError("Analysis context character limit must be positive.")
    scene = project.get_scene(scene_id)
    scene_text = open_text[scene_id] if scene_id in open_text else project.read_scene(scene_id)
    sections = [(scene_id, f"Selected scene ({scene_id}): {scene.title}\n", scene_text)]
    if task == "continuity":
        for note_id in note_ids:
            note = project.get_note(note_id)
            text = open_text[note_id] if note_id in open_text else project.read_note(note_id)
            sections.append((note_id, f"Selected reference note ({note_id}, {note.type}): {note.title}\n", text))
        character_context, limited = capture_scene_character_context(project, scene_id)
        if limited:
            raise ContextBudgetError(
                "Required character evidence exceeds the scene profile limits. "
                "No continuity request was sent; reduce associated profile details before retrying."
            )
        if character_context:
            sections.append((None, "Characters explicitly associated with this scene:\n", character_context))
    context = "\n\n".join(header + text for _source_id, header, text in sections)
    source_texts = {source_id: text for source_id, _header, text in sections if source_id is not None}
    if len(context) > maximum_context:
        if task == "continuity":
            raise ContextBudgetError(
                "Required scene, note and character evidence exceeds the analysis character limit "
                f"({len(context)} > {maximum_context}). Increase Context size or select fewer notes; "
                "no continuity request was sent and no source was truncated."
            )
        context = context[:maximum_context] + "\n[Selected context truncated to the configured limit.]"
    if task == "summary":
        instruction = "Summarize the selected scene. Keep the response concise and cite source details when useful."
    else:
        instruction = (
            "Review the selected scene against the selected reference notes and explicitly associated character profiles. "
            "Return only JSON: {\"findings\":[{\"confidence\":\"definite|probable|possible\", "
            "\"scene_id\":\"scene ID\", \"character_ids\":[\"associated character ID\"], "
            "\"concern\":\"explanation\", \"evidence\":{\"source_id\":\"scene or selected note ID\", "
            "\"quote\":\"exact excerpt from that source\"}, \"suggestion\":\"author review question\"}]}. "
            "Use an empty findings list if none. Do not invent evidence or treat every personality deviation as an error. "
            f"Scene ID: {scene_id}. Associated characters: "
            + ", ".join(f"{project.get_character(a.character_id).full_name} ({a.character_id})" for a in scene.character_associations)
        )
    result = provider.generate_private(
        f"{instruction}\n\nOnly analyze this captured context:\n{context}",
        role=role,
        maximum_tokens=maximum_tokens,
        temperature=temperature,
        require_full_context=task == "continuity",
    )
    if not isinstance(result, str):
        raise ValueError("The provider returned a malformed analysis response.")
    if task == "continuity":
        # Only accept quotations actually present in the bounded request.
        findings = parse_continuity_findings(
            result, scene_id=scene_id,
            character_ids={item.character_id for item in scene.character_associations},
            sources=source_texts,
        )
        if any(finding.quote not in context for finding in findings):
            raise ValueError("The model cited text outside the context sent for review.")
        return format_continuity_findings(findings)
    return result
