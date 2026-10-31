"""Bounded character context for scene-focused local AI requests."""

from app.project.model import Character, SceneCharacterAssociation

MAX_CHARACTER_CONTEXT = 5000


def project_planning_context(project, *, limit: int = MAX_CHARACTER_CONTEXT) -> str:
    """Compact, relevant profiles for outline planning; bounds breadth and depth."""
    lines = []
    relevant = [
        character for character in project.manifest.characters
        if character.primary_motivation
        or any(goal.status == "active" for goal in character.goals)
        or character.internal_conflicts
    ]
    selected = relevant[:24]
    selected_ids = {character.id for character in selected}
    for character in selected:
        name = character.display_name or character.full_name
        details = [f"{name} ({character.role})"]
        if character.primary_motivation:
            details.append(f"motivation: {character.primary_motivation}")
        active = [goal.description for goal in character.goals if goal.status == "active"]
        if active:
            details.append("goals: " + "; ".join(active[:3]))
        if character.internal_conflicts:
            details.append("internal conflict: " + "; ".join(character.internal_conflicts[:2]))
        lines.append(" — ".join(details))
    characters = {character.id: character for character in selected}
    for relationship in project.manifest.character_relationships:
        if relationship.source_id not in selected_ids or relationship.target_id not in selected_ids:
            continue
        source = characters[relationship.source_id]
        target = characters[relationship.target_id]
        description = f" — {relationship.description}" if relationship.description else ""
        attitude = f"; attitude: {relationship.attitude}" if relationship.attitude else ""
        trust = f"; trust: {relationship.trust}" if relationship.trust is not None else ""
        lines.append(
            f"Directed relationship: {source.display_name or source.full_name} → "
            f"{target.display_name or target.full_name}: "
            f"{relationship.relationship_type}{description}{attitude}{trust}"
        )
    if len(relevant) > len(selected):
        lines.append(f"[{len(relevant) - len(selected)} additional relevant profiles omitted by the planning context limit.]")
    return "\n".join(lines)[:max(0, limit)]


def scene_character_context(project, scene_id: str, *, limit: int = MAX_CHARACTER_CONTEXT) -> str:
    """Render profiles explicitly associated with a scene and adjacent relationships only."""
    return capture_scene_character_context(project, scene_id, limit=limit)[0]


def capture_scene_character_context(project, scene_id: str, *, limit: int = MAX_CHARACTER_CONTEXT) -> tuple[str, bool]:
    """Return the rendered context and whether its character details were limited."""
    scene = project.get_scene(scene_id)
    associations = scene.character_associations
    if not associations:
        return "", False
    selected = {item.character_id for item in associations}
    characters = {character.id: character for character in project.manifest.characters}
    lines: list[str] = []
    omitted = False
    for association in associations:
        character = characters.get(association.character_id)
        if character is None:
            continue
        profile, limited = _profile(character, association)
        lines.append(profile)
        omitted |= limited
        for relationship in project.manifest.character_relationships:
            if relationship.source_id == character.id and relationship.target_id in selected:
                other = characters[relationship.target_id]
                lines.append(f"Relationship: {character.full_name} → {other.full_name}: {relationship.relationship_type}; {relationship.description}; attitude={relationship.attitude}; trust={relationship.trust}")
    rendered = "\n".join(lines)
    return rendered[:max(0, limit)], omitted or len(rendered) > max(0, limit)


def _profile(character: Character, association: SceneCharacterAssociation) -> tuple[str, bool]:
    lines = [f"Character: {character.display_name or character.full_name} ({character.role})"]
    omitted = False

    def bounded(items, maximum):
        nonlocal omitted
        omitted |= len(items) > maximum
        return items[:maximum]
    if association.presence == "mentioned":
        lines.append("Scene status: mentioned, not physically present.")
    if association.purpose:
        lines.append(f"Scene purpose: {association.purpose}")
    if character.primary_motivation:
        lines.append(f"Primary motivation: {character.primary_motivation}")
    goals = [goal.description for goal in character.goals if goal.status == "active"]
    if goals:
        lines.append("Active goals: " + "; ".join(bounded(goals, 5)))
    traits = character.personality.get("traits", [])
    if traits:
        lines.append("Traits: " + "; ".join(bounded(traits, 8)))
    for kind in ("knows", "believes", "suspects", "does_not_know", "conceals"):
        statements = [item.statement for item in character.knowledge if item.kind == kind]
        if statements:
            lines.append(f"{kind.replace('_', ' ').title()}: " + "; ".join(bounded(statements, 5)))
    if character.arc.get("current_state"):
        lines.append(f"Current arc state: {character.arc['current_state']}")
    if association.relevant_goals:
        lines.append("Scene-relevant goals: " + "; ".join(bounded(association.relevant_goals, 5)))
    if association.development_notes:
        lines.append("Development notes: " + "; ".join(bounded(association.development_notes, 5)))
    for change in bounded(association.state_changes, 8):
        previous = f" (previously: {change.previous_value})" if change.previous_value else ""
        evidence = f"; evidence: {change.evidence}" if change.evidence else ""
        lines.append(f"Scene state change: {change.field} → {change.value}{previous}{evidence}")
    return "\n".join(lines), omitted
