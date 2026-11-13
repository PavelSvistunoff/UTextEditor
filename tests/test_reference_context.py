import pytest

from app.project import Project, ProjectError
from app.project.character_suggestions import suggest_project_character_fields
from app.project.reference_context import capture_project_notes


class Provider:
    def __init__(self, during=None):
        self.requests = []
        self.during = during

    def generate_private(self, prompt, **options):
        self.requests.append((prompt, options))
        if self.during:
            self.during()
        return '{"description":"A proposed description"}'


def test_character_generation_sends_every_note_and_open_buffer_in_full(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    first = project.add_note("First", "research", content="OLD_DISK_TEXT")
    second = project.add_note("Last", "timeline", content="x" * 11000 + "CLOSED_NOTE_END")
    provider = Provider()
    result = suggest_project_character_fields(provider, project, {"description": ""}, "Ukrainian", 0.2,
                                             {first.id: "UNSAVED_NOTE_END"}, fallback_language="Ukrainian")
    prompt, options = provider.requests[0]
    assert "UNSAVED_NOTE_END" in prompt and "CLOSED_NOTE_END" in prompt
    assert "OLD_DISK_TEXT" not in prompt
    assert first.id in prompt and second.id in prompt
    assert options["require_full_context"] is True
    assert result.values == {"description": "A proposed description"}
    assert project.read_note(first.id) == "OLD_DISK_TEXT"


@pytest.mark.parametrize("failure", ["missing", "invalid_utf8", "too_large", "open_too_large", "omitted"])
def test_incomplete_note_context_fails_before_any_model_request(tmp_path, monkeypatch, failure):
    import app.project.reference_context as context

    project = Project.create(tmp_path / "novel", "Novel")
    note = project.add_note("Reference", content="Original")
    path = project.root / note.path
    buffers = {}
    if failure == "missing":
        path.unlink()
    elif failure == "invalid_utf8":
        path.write_bytes(b"\xff")
    elif failure == "too_large":
        monkeypatch.setattr(context, "MAX_PROJECT_REFERENCE_BYTES", 20)
        path.write_text("x" * 21)
    elif failure == "open_too_large":
        monkeypatch.setattr(context, "MAX_PROJECT_REFERENCE_BYTES", 20)
        buffers[note.id] = "x" * 21
    else:
        buffers[note.id] = None
    provider = Provider()
    with pytest.raises((ProjectError, OSError, UnicodeError)):
        suggest_project_character_fields(provider, project, {"description": ""}, "English", 0.2,
                                         buffers, fallback_language="English")
    assert not provider.requests


@pytest.mark.parametrize("change", ["note", "manifest"])
def test_character_suggestions_discard_changed_reference_context(tmp_path, change):
    project = Project.create(tmp_path / "novel", "Novel")
    note = project.add_note("Reference", content="Original")

    def mutate():
        if change == "note":
            (project.root / note.path).write_text("External edit", encoding="utf-8")
        else:
            project.add_note("Added during generation", content="New")

    provider = Provider(mutate)
    with pytest.raises(ProjectError, match="changed"):
        suggest_project_character_fields(provider, project, {"description": ""}, "English", 0.2,
                                         {}, fallback_language="English")
    assert len(provider.requests) == 1


def test_reference_capture_verifies_changes_after_review(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    note = project.add_note("Reference", content="Original")
    captured = capture_project_notes(project, {})
    (project.root / note.path).write_text("Edited during review", encoding="utf-8")
    with pytest.raises(ProjectError, match="changed"):
        captured.verify_current()


def test_cancelled_character_context_capture_never_dispatches_model(tmp_path, monkeypatch):
    import app.project.character_suggestions as service

    project = Project.create(tmp_path / "novel", "Novel")
    original = service.capture_project_notes
    cancelled = False

    def capture(*args):
        nonlocal cancelled
        result = original(*args)
        cancelled = True
        return result

    monkeypatch.setattr(service, "capture_project_notes", capture)
    provider = Provider()
    with pytest.raises(ProjectError, match="cancelled"):
        service.suggest_project_character_fields(provider, project, {"description": ""}, "English", 0.2, {},
                                                 fallback_language="English", is_cancelled=lambda: cancelled)
    assert not provider.requests


def test_complete_cast_context_keeps_every_text_field_relationship_and_scene_change(tmp_path):
    import base64
    import json
    from uuid import uuid4
    from app.project.model import (
        CHARACTER_ARC_FIELDS, CHARACTER_BACKGROUND_FIELDS, CHARACTER_PERSONALITY_FIELDS,
        CHARACTER_KNOWLEDGE_KINDS, CharacterGoal, CharacterKnowledge,
        CharacterRelationship, CharacterStateChange, SceneCharacterAssociation,
    )
    from app.project.character_context import complete_project_character_context

    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening")
    character = project.add_character("Mara")
    character.background = {key: f"Complete {key}" for key in CHARACTER_BACKGROUND_FIELDS}
    character.personality = {key: [f"Trait {number}" for number in range(10)] for key in CHARACTER_PERSONALITY_FIELDS}
    character.arc = {key: f"Complete {key}" for key in CHARACTER_ARC_FIELDS}
    character.goals = [CharacterGoal(f"Goal {number}", "blocked", 4, "Goal notes") for number in range(7)]
    character.knowledge = [CharacterKnowledge(kind, f"Fact {number}") for kind in CHARACTER_KNOWLEDGE_KINDS for number in range(7)]
    character.portrait = base64.b64encode(b"\xff\xd8\xffportrait data").decode()
    project.update_character(character.id, character)
    others = [project.add_character(f"Other {number}") for number in range(25)]
    project.add_character_relationship(CharacterRelationship(str(uuid4()), character.id, others[-1].id,
                                                            history="Full history", shared_secrets="Full secret"))
    project.associate_character(scene.id, SceneCharacterAssociation(
        character.id, state_changes=[CharacterStateChange("current_state", f"Change {number}", evidence="Quoted text") for number in range(10)],
    ))
    original = project.manifest.to_mapping()
    text = complete_project_character_context(project)
    captured = json.loads(text)
    expected = [{key: value for key, value in profile.items() if key != "portrait"} for profile in original["characters"]]
    assert captured["characters"] == expected
    assert captured["relationships"] == original["character_relationships"]
    assert len(captured["characters"]) == 26
    assert len(captured["scene_development"][0]["character_associations"][0]["state_changes"]) == 10
    assert character.portrait not in text
    assert project.manifest.to_mapping() == original


def test_auto_writer_http_payload_contains_complete_references_and_no_truncation(tmp_path):
    import json
    from unittest.mock import MagicMock, patch
    from app.ai.ollama_client import OllamaClient
    from app.project.auto_writer import run_auto_writer

    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("Empty")
    note = project.add_note("Reference", content="x" * 11000 + "NOTE_TAIL")
    character = project.add_character("Unassociated")
    character.description = "PROFILE_TAIL"
    project.update_character(character.id, character)
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = b'{"message":{"content":"Draft"}}'
    with patch("app.ai.ollama_client.request.urlopen", return_value=response) as urlopen:
        run_auto_writer(OllamaClient(), project, "write_empty", "", {}, maximum_tokens=300, temperature=0.2,
                        snapshot_name="Before", is_cancelled=lambda: False)
    payload = json.loads(urlopen.call_args.args[0].data)
    prompt = payload["messages"][1]["content"]
    assert "NOTE_TAIL" in prompt and "PROFILE_TAIL" in prompt
    assert note.id in prompt and character.id in prompt
    assert payload["truncate"] is False and payload["shift"] is False
