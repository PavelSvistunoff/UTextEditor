"""Captured, bounded scene analysis and evidence validation for worker calls."""

from app.project.service import Project
from app.project.character_context import scene_character_context
from .provider import AIProvider
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
    scene = project.get_scene(scene_id)
    scene_text = open_text[scene_id] if scene_id in open_text else project.read_scene(scene_id)
    sections = [(scene_id, f"Selected scene ({scene_id}): {scene.title}\n", scene_text)]
    if task == "continuity":
        for note_id in note_ids:
            note = project.get_note(note_id)
            text = open_text[note_id] if note_id in open_text else project.read_note(note_id)
            sections.append((note_id, f"Selected reference note ({note_id}, {note.type}): {note.title}\n", text))
        character_context = scene_character_context(project, scene_id)
        if character_context:
            sections.append((None, "Characters explicitly associated with this scene:\n", character_context))
    parts = []
    source_texts = {}
    offset = 0
    for source_id, header, text in sections:
        if parts:
            offset += 2
        visible = max(0, maximum_context - offset - len(header))
        if source_id is not None:
            source_texts[source_id] = text[:visible]
        parts.append(header + text)
        offset += len(header) + len(text)
    context = "\n\n".join(parts)
    if len(context) > maximum_context:
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
