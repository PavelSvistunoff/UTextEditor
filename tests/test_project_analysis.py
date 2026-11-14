import pytest

from app.ai.context_budget import ContextBudgetError
from app.ai.project_analysis import run_project_analysis
from app.project import Project, SceneCharacterAssociation


class AnalysisProvider:
    def __init__(self):
        self.calls = []

    def generate_private(self, prompt, **options):
        self.calls.append((prompt, options))
        return '{"findings": []}'


def analyze(provider, project, scene, notes=(), limit=2048, task="continuity", buffers=None):
    return run_project_analysis(provider, project, task, scene.id, notes,
                                buffers or {}, limit, "Review only", 100, 0.2)


def test_long_scene_cannot_starve_selected_note_or_character(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    scene = project.add_scene("Сцена", content="Довгий текст. " * 300)
    note = project.add_note("Факт", content="Обов'язкове свідчення")
    character = project.add_character("Марія")
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    provider = AnalysisProvider()
    with pytest.raises(ContextBudgetError, match="Required scene, note and character evidence"):
        analyze(provider, project, scene, (note.id,))
    assert provider.calls == []
    analyze(provider, project, scene, (note.id,), limit=10000)
    prompt = provider.calls[0][0]
    assert scene.title in prompt and "Обов'язкове свідчення" in prompt and "Марія" in prompt


def test_exact_character_boundary_and_unsaved_note_text(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    scene = project.add_scene("Scene", content="disk scene")
    note = project.add_note("Note", content="disk note")
    buffers = {scene.id: "unsaved scene", note.id: "незбережена нотатка"}
    context = (f"Selected scene ({scene.id}): Scene\nunsaved scene\n\n"
               f"Selected reference note ({note.id}, {note.type}): Note\nнезбережена нотатка")
    provider = AnalysisProvider()
    analyze(provider, project, scene, (note.id,), len(context), buffers=buffers)
    assert provider.calls[0][0].endswith(context)
    with pytest.raises(ContextBudgetError):
        analyze(provider, project, scene, (note.id,), len(context) - 1, buffers=buffers)
    assert len(provider.calls) == 1


def test_limited_character_details_refuse_partial_continuity_request(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    scene = project.add_scene("Scene", content="Scene prose")
    character = project.add_character("Mara")
    character.personality = {"traits": [f"trait {index}" for index in range(9)]}
    project.update_character(character.id, character)
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    provider = AnalysisProvider()
    with pytest.raises(ContextBudgetError, match="Required character evidence"):
        analyze(provider, project, scene, limit=20000)
    assert not provider.calls


def test_summary_still_sends_only_a_labeled_scene_excerpt(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    scene = project.add_scene("Scene", content="start " + "x" * 400 + " hidden ending")
    note = project.add_note("Secret", content="unselected secret")
    provider = AnalysisProvider()
    analyze(provider, project, scene, (note.id,), limit=120, task="summary")
    prompt = provider.calls[0][0]
    assert "[Selected context truncated" in prompt
    assert "hidden ending" not in prompt and "unselected secret" not in prompt


@pytest.mark.parametrize("task,limit", [("invalid", 2048), ("continuity", 0)])
def test_invalid_analysis_request_never_calls_provider(tmp_path, task, limit):
    project = Project.create(tmp_path / "project", "Novel")
    scene = project.add_scene("Scene", content="text")
    provider = AnalysisProvider()
    with pytest.raises(ValueError):
        analyze(provider, project, scene, limit=limit, task=task)
    assert not provider.calls
