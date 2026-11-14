"""Exact sent evidence, mandatory allocation and character boundary regressions."""

import json

import pytest

from app.ai.character_development import suggest_character_development
from app.ai.context_budget import ContextBudgetError
from app.ai.project_analysis import run_project_analysis
from app.project import Project, SceneCharacterAssociation, ProjectError
from app.project.analysis_context import AnalysisRetrieval
from app.project.auto_writer_context import ContextReviewDecision
from app.project.character_suggestions import suggest_project_character_fields
from app.project.rag_sources import BufferText, CaptureCancelled, capture_project_sources
from app.project.rag_index import LexicalIndex
from app.project.rag_context import ProjectContextService


class Provider:
    def __init__(self, response='{"findings": []}'):
        self.response = response
        self.calls = []
        self.effect = lambda: None

    def generate_private(self, prompt, **options):
        self.calls.append((prompt, options))
        self.effect()
        return self.response


@pytest.fixture
def story(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    chapter = project.add_chapter("Chapter")
    earlier = project.add_scene("Copper key", chapter_id=chapter.id,
                                content="Mara hides the copper key in the garden.")
    scene = project.add_scene("Copper key", chapter_id=chapter.id,
                              content="Mara opens the copper door with her key.")
    future = project.add_scene("Copper key", chapter_id=chapter.id,
                               content="Mara destroys the copper key tomorrow.")
    note = project.add_note("Copper key", content="The copper key opens only the garden door.")
    character = project.add_character("Mara")
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    cache = tmp_path / "cache"
    index = LexicalIndex(cache, project.root, project.manifest.project_id)
    index.refresh(capture_project_sources(project))
    return project, earlier, scene, future, note, character, cache, index


def context(story, **overrides):
    project, earlier, scene, future, note, character, cache, index = story
    values = dict(title="Copper key continuity", review=lambda title, captured, excluded:
        ContextReviewDecision("send", excluded), is_cancelled=lambda: False,
        scene_id=scene.id, mandatory_source_ids=frozenset({scene.id, note.id, character.id}))
    values.update(overrides)
    return AnalysisRetrieval(project, cache, 65536, {}, **values)


def analyze(story, run, provider, task="continuity"):
    project, earlier, scene, future, note, character, cache, index = story
    return run_project_analysis(provider, project, task, scene.id, (note.id,), {},
                                32000, "Review only", 1600, .2, retrieval=run)


def finding(scene, source, quote, characters=()):
    return json.dumps({"findings": [{"confidence": "possible", "scene_id": scene.id,
        "character_ids": list(characters), "concern": "Check the key", "evidence":
        {"source_id": source.id, "quote": quote}, "suggestion": "Review chronology"}]})


@pytest.mark.parametrize("task", ["summary", "continuity"])
def test_exact_review_required_sources_and_presence_chronology(story, task):
    project, earlier, scene, future, note, character, cache, index = story
    reviewed = []
    run = context(story, review=lambda title, captured, excluded:
        (reviewed.append(captured) or ContextReviewDecision("send", excluded)))
    provider = Provider("Summary" if task == "summary" else '{"findings": []}')
    result = analyze(story, run, provider, task)
    assert "contextual" in result.lower()
    assert provider.calls[0][0] == reviewed[0].prompt == run.evidence.prompt
    assert provider.calls[0][1]["require_full_context"] is True
    assert {scene.id, note.id, character.id} <= {d.source_id for d in run.evidence.manifest.decisions if d.disposition == "mandatory"}
    assert earlier.id in run.optional_sources() and future.id not in run.optional_sources()
    assert "neither physical presence nor character knowledge" in reviewed[0].role
    assert "does not prove story chronology" in reviewed[0].role
    assert project.read_scene(scene.id) == "Mara opens the copper door with her key."


def test_retrieved_quote_accepted_but_future_invented_unassociated_rejected(story):
    project, earlier, scene, future, note, character, cache, index = story
    result = analyze(story, context(story), Provider(finding(scene, earlier, "Mara hides the copper key")))
    assert earlier.id in result
    for source, quote, characters in [(future, "Mara destroys", ()), (earlier, "invented", ()),
                                       (earlier, "Mara hides", ("unassociated",))]:
        with pytest.raises(ValueError):
            analyze(story, context(story), Provider(finding(scene, source, quote, characters)))


def test_excluded_citation_and_changed_exclusion_without_rebuild_rejected(story):
    project, earlier, scene, future, note, character, cache, index = story
    def review(title, captured, excluded):
        return ContextReviewDecision("send" if excluded else "rebuild", frozenset({earlier.id}))
    with pytest.raises(ValueError, match="outside"):
        analyze(story, context(story, review=review), Provider(finding(scene, earlier, "Mara hides")))
    provider = Provider()
    with pytest.raises(ProjectError, match="Rebuild"):
        analyze(story, context(story, review=lambda *args: ContextReviewDecision("send", frozenset({earlier.id}))), provider)
    assert not provider.calls


@pytest.mark.parametrize("source", ["scene", "note", "profile"])
def test_required_sources_cannot_be_excluded(story, source):
    selected = {"scene": story[2], "note": story[4], "profile": story[5]}[source]
    provider = Provider()
    with pytest.raises(ProjectError, match="Required"):
        analyze(story, context(story, review=lambda *args:
            ContextReviewDecision("rebuild", frozenset({selected.id}))), provider)
    assert not provider.calls


@pytest.mark.parametrize("when", ["review", "generate", "after"])
def test_disk_change_invalidates_request_or_pending_review(story, when):
    project, earlier, scene, future, note, character, cache, index = story
    change = lambda: (project.root / earlier.path).write_text("Changed evidence", encoding="utf-8")
    def review(title, captured, excluded):
        if when == "review":
            change()
        return ContextReviewDecision("send", excluded)
    run = context(story, review=review)
    provider = Provider()
    if when == "generate":
        provider.effect = change
    if when == "after":
        analyze(story, run, provider)
        change()
        with pytest.raises(ProjectError):
            run.verify_current()
    else:
        with pytest.raises(ProjectError):
            analyze(story, run, provider)
        assert len(provider.calls) == (when == "generate")


@pytest.mark.parametrize("mode", ["cancel", "reject", "budget", "character_limit"])
def test_no_dispatch_on_rejected_cancelled_or_oversized_mandatory(story, mode):
    run = context(story, is_cancelled=lambda: mode == "cancel", review=lambda *args:
        ContextReviewDecision("cancel" if mode == "reject" else "send"))
    if mode == "budget":
        run.context_tokens = 100
    provider = Provider()
    with pytest.raises((CaptureCancelled, ContextBudgetError)):
        if mode == "character_limit":
            project, _, scene, _, note, _, _, _ = story
            run_project_analysis(provider, project, "summary", scene.id, (note.id,), {}, 20,
                                 "Review", 100, .2, retrieval=run)
        else:
            analyze(story, run, provider)
    assert not provider.calls


def test_missing_index_reports_partial_no_findings_without_false_audit(story):
    story[-1].delete()
    run = context(story)
    result = analyze(story, run, Provider())
    assert run.evidence.manifest.retrieval_state == "unavailable"
    assert not run.optional_sources()
    assert "no whole-project audit" in result


def test_full_notes_and_unsaved_buffers_retained_for_empty_fields(story):
    project, earlier, scene, future, note, character, cache, index = story
    full = "Copper key notes. " * 700 + "UNIQUE REQUIRED ENDING"
    run = context(story, scene_id=None, mandatory_source_ids=frozenset({note.id}))
    run.buffers[note.id] = BufferText(full, 9)
    original = index.path.read_bytes()
    provider = Provider('{"role":"Gardener"}')
    result = suggest_project_character_fields(provider, project, {"full_name": "Mara", "role": ""},
        "English", .2, {note.id: full}, fallback_language="English", retrieval=run)
    assert result.values == {"role": "Gardener"}
    assert "UNIQUE REQUIRED ENDING" in provider.calls[0][0]
    assert provider.calls[0][1]["timeout"] == 300 and provider.calls[0][1]["json_mode"]
    assert any(d.source_id == note.id and d.buffer_revision == 9 for d in run.evidence.manifest.decisions)
    result.verify_current()
    assert index.path.read_bytes() == original
    assert project.read_note(note.id) != full


@pytest.mark.parametrize("supported", [True, False])
def test_background_cannot_justify_arc_update(story, supported):
    project, earlier, scene, future, note, character, cache, index = story
    quote = "opens the copper door" if supported else "hides the copper key"
    provider = Provider(json.dumps({"proposals": [{"field": "current_state", "value": "Trusts Mara", "evidence": quote}]}))
    run = context(story, mandatory_source_ids=frozenset())
    if supported:
        assert suggest_character_development(provider, {"full_name": "Mara"}, project.read_scene(scene.id),
            "English", .2, retrieval=run)[0].evidence == quote
    else:
        with pytest.raises(ValueError, match="outside the captured scene"):
            suggest_character_development(provider, {"full_name": "Mara"}, project.read_scene(scene.id),
                "English", .2, retrieval=run)
    assert earlier.id in run.optional_sources()


def test_disjoint_optional_spans_cannot_form_invented_quote():
    from app.ai.continuity import parse_continuity_findings
    class Source:
        id = "scene"
    with pytest.raises(ValueError, match="outside"):
        parse_continuity_findings(finding(Source(), Source(), "endstart"), scene_id="scene",
            character_ids=set(), sources={"scene": ("end", "start")})


def test_task_read_capture_race_refuses_old_mandatory_text(story, monkeypatch):
    project, earlier, scene, future, note, character, cache, index = story
    original_capture = ProjectContextService.capture
    def changed_capture(service, *args, **options):
        (project.root / scene.path).write_text("New source after task read", encoding="utf-8")
        return original_capture(service, *args, **options)
    monkeypatch.setattr('app.project.analysis_context.ProjectContextService.capture', changed_capture)
    provider = Provider()
    with pytest.raises(ProjectError, match="Required task inputs changed"):
        analyze(story, context(story), provider)
    assert not provider.calls


def test_no_hits_preserves_required_context_and_reports_coverage(story):
    run = context(story)
    run.title = "zzzzunmatchedquery"
    run.scene_id = None
    provider = Provider()
    run.generate(provider, "zzzzunmatchedquery", role="Review", maximum_tokens=100, temperature=.2)
    assert run.evidence.manifest.retrieval_state == "no_hits"
    assert not run.optional_sources()
    assert story[2].id in provider.calls[0][0]
