"""Create a complete project revision from captured buffers and remaining disk text."""

from app.document.revisions import RevisionStore


def create_project_snapshot(project, name, manifest, scene_order, scene_titles, open_text):
    documents = dict(open_text)
    for scene in project.iter_scenes():
        if scene.id not in documents:
            documents[scene.id] = project.read_scene(scene.id)
    for note in project.manifest.notes:
        if note.id not in documents:
            documents[note.id] = project.read_note(note.id)
    store = RevisionStore(project.root / ".utexteditor" / "revisions")
    return store.create(
        name,
        structure=manifest,
        scene_order=scene_order,
        scene_titles=scene_titles,
        documents=documents,
    )
