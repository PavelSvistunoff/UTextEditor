"""Project word counts and availability from captured open text and disk."""

from .service import Project, WordCount, count_words
from .model import ProjectError


def build_project_summary(project: Project, open_text: dict[str, str]):
    scene_counts: dict[str, WordCount] = {}
    unavailable: set[str] = set()
    for scene in project.iter_scenes():
        if scene.id in open_text:
            scene_counts[scene.id] = WordCount(count_words(open_text[scene.id]), True)
        else:
            result = project.scene_word_count(scene.id)
            scene_counts[scene.id] = result
            if not result.complete:
                unavailable.add(scene.id)
    chapter_counts: dict[str, WordCount] = {}
    for chapter in project.manifest.chapters:
        chapter_counts[chapter.id] = WordCount(
            sum(scene_counts[scene.id].count for scene in chapter.scenes),
            all(scene_counts[scene.id].complete for scene in chapter.scenes),
        )
    project_count = WordCount(
        sum(result.count for result in scene_counts.values()),
        all(result.complete for result in scene_counts.values()),
    )
    for note in project.manifest.notes:
        try:
            project.read_note(note.id)
        except (OSError, UnicodeError, ProjectError):
            unavailable.add(note.id)
    return scene_counts, chapter_counts, project_count, unavailable
