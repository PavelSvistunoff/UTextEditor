"""Offline planning/Auto-pilot provenance, cancellation and application gates."""

import json

import pytest

from app.ai.context_budget import ContextBudgetError
from app.ai.project_planning import generate_project_outline, suggest_project_brief
from app.project import Project, ProjectError
from app.project.auto_writer_context import ContextReviewDecision
from app.project.autopilot import run_autopilot
from app.project.planning_context import PlanningRetrievalRun, TransientDraft
from app.project.rag_index import LexicalIndex
from app.project.rag_sources import BufferText, CaptureCancelled, capture_project_sources


PLAN = json.dumps({"chapters": [{"title": "New chapter", "scenes": [
    {"title": "Copper key", "purpose": "Find the key"},
    {"title": "Hidden door", "purpose": "Use the key"},
    {"title": "Return", "purpose": "Remember the key"}]}],
    "characters": [{"name": "Proposed guide", "profile": "A proposed new acquaintance."}]})


class Provider:
    def __init__(self, answers):
        self.answers = iter(answers)
        self.calls = []
        self.effect = lambda: None

    def generate_private(self, prompt, **options):
        self.calls.append((prompt, options))
        self.effect()
        return next(self.answers)


@pytest.fixture
def story(tmp_path):
    project = Project.create(tmp_path / "project", "Novel")
    chapter = project.add_chapter("Existing chapter")
    scene = project.add_scene("Copper key", chapter_id=chapter.id,
                              content="The copper key opens the hidden door in the garden.")
    note = project.add_note("Copper key", content="The copper key belongs to the old gardener.")
    character = project.add_character("Mara")
    character.primary_motivation = "Protect the copper key and the hidden door."
    project.update_character(character.id, character)
    cache = tmp_path / "cache"
    index = LexicalIndex(cache, project.root, project.manifest.project_id)
    index.refresh(capture_project_sources(project))
    return project, scene, note, cache, index


def run_context(story, **options):
    project, scene, note, cache, index = story
    defaults = dict(review=lambda title, captured, excluded: ContextReviewDecision("send", excluded),
                    is_cancelled=lambda: False)
    defaults.update(options)
    return PlanningRetrievalRun(project, cache, 65536, "A story about the copper key and hidden door", {}, **defaults)


@pytest.mark.parametrize("workflow", ["brief", "outline"])
def test_planning_preserves_mandatory_motivations_and_exact_source_review(story, workflow):
    project, scene, note, cache, index = story
    reviewed = []

    def review(title, captured, excluded):
        reviewed.append(captured)
        assert "Protect the copper key" in captured.prompt
        assert scene.id in captured.prompt and note.id in captured.prompt
        assert "[Suggestion: ...]" in captured.role
        assert "not established project facts" in captured.role
        return ContextReviewDecision("send", excluded)

    context = run_context(story, review=review)
    provider = Provider(["[Suggestion: a mystery]" if workflow == "brief" else "# New\n- Key"])
    function = suggest_project_brief if workflow == "brief" else generate_project_outline
    result = function(provider, context.brief, 1800, .2, retrieval=context)
    assert result
    assert provider.calls[0][0] == reviewed[0].prompt
    assert provider.calls[0][1]["role"] == reviewed[0].role
    assert provider.calls[0][1]["require_full_context"] is True
    assert context.steps[0].request.prompt == reviewed[0].prompt
    assert {p.source_id for p in context.steps[0].request.passages} >= {scene.id, note.id}
    assert len(tuple(project.iter_scenes())) == 1


@pytest.mark.parametrize("scope", ["none", "new_project", "missing_index"])
def test_new_project_no_index_and_no_project_report_actual_coverage(story, tmp_path, scope):
    project, scene, note, cache, index = story
    if scope == "none":
        project = None
    elif scope == "new_project":
        project = Project.create(tmp_path / "empty", "New")
    else:
        index.delete()
    reviews = []
    context = PlanningRetrievalRun(project, cache, 32768, "Copper key", {},
        review=lambda title, captured, excluded: (reviews.append(captured) or ContextReviewDecision("send")),
        is_cancelled=lambda: False)
    assert suggest_project_brief(Provider(["[Suggestion: mystery]"]), "Copper key", 1400, .2, retrieval=context)
    assert reviews[0].manifest.retrieval_state in {"standalone", "unavailable", "no_hits"}
    assert not context.steps[0].request.passages
    assert "Copper key" in context.steps[0].request.prompt
    if scope == "none":
        assert "No project:" in " ".join(reviews[0].manifest.notices)


def test_exclude_rebuild_and_cannot_send_changed_exclusions(story):
    project, scene, note, cache, index = story
    reviews = []

    def review(title, captured, excluded):
        reviews.append(captured)
        return ContextReviewDecision("rebuild", frozenset({note.id})) if not excluded else ContextReviewDecision("send", excluded)

    context = run_context(story, review=review)
    suggest_project_brief(Provider(["Ideas"]), context.brief, 1400, .2, retrieval=context)
    assert len(reviews) == 2
    assert any(d.source_id == note.id and d.reason == "excluded" for d in reviews[-1].manifest.decisions)
    invalid = run_context(story, review=lambda *args: ContextReviewDecision("send", frozenset({note.id})))
    with pytest.raises(ProjectError, match="Rebuild"):
        suggest_project_brief(Provider(["unused"]), invalid.brief, 1400, .2, retrieval=invalid)


def test_autopilot_full_transient_sources_and_provenance_never_enter_index(story):
    project, scene, note, cache, index = story
    before = index.path.read_bytes()
    context = run_context(story, require_complete=True)
    long_draft = "A first draft. " * 200 + "TAIL_BEYOND_1600"
    provider = Provider([PLAN, long_draft, "Second draft.", "Third draft."])
    result = run_autopilot(provider, context.brief, "# Existing", maximum_tokens=900, temperature=.2,
                           is_cancelled=lambda: False, retrieval=context)
    assert len(result.retrieval_steps) == 4
    assert "TAIL_BEYOND_1600" in provider.calls[2][0] and "TAIL_BEYOND_1600" in provider.calls[3][0]
    assert [source.source_id for source in result.retrieval_steps[-1].transient_sources] == [
        "generated-plan", "generated-scene-1", "generated-scene-2"]
    for step in result.retrieval_steps[1:]:
        assert "provisional generated draft; not saved or accepted" in step.request.prompt
        assert "Mandatory provisional generated sources" in " ".join(step.request.manifest.notices)
    assert index.path.read_bytes() == before
    assert len(tuple(project.iter_scenes())) == 1
    assert len(project.manifest.notes) == 1
    context.apply_autopilot(result.chapters, result.characters)
    assert project.read_scene(scene.id) == "The copper key opens the hidden door in the garden."
    assert len(tuple(Project.open(project.root).iter_scenes())) == 4
    assert index.path.read_bytes() == before  # Canonical cache only changes by explicit maintenance.


@pytest.mark.parametrize("step", [1, 2, 3, 4])
@pytest.mark.parametrize("failure", ["cancel", "provider"])
def test_multi_step_cancellation_or_failure_applies_nothing(story, step, failure):
    project, scene, note, cache, index = story
    before = project.manifest.to_mapping()
    provider = Provider([PLAN, "Draft one", "Draft two", "Draft three"])
    cancelled = [False]

    def effect():
        if len(provider.calls) == step:
            if failure == "provider":
                raise RuntimeError("Offline provider failure")
            cancelled[0] = True

    provider.effect = effect
    context = run_context(story, is_cancelled=lambda: cancelled[0])
    with pytest.raises((CaptureCancelled, RuntimeError, ProjectError)):
        run_autopilot(provider, context.brief, "", maximum_tokens=900, temperature=.2,
                      is_cancelled=lambda: cancelled[0], retrieval=context)
    assert project.manifest.to_mapping() == before
    assert len(tuple(project.iter_scenes())) == 1
    assert len(provider.calls) == step


@pytest.mark.parametrize("when", ["review", "generation", "between_steps", "application"])
def test_closed_source_changes_invalidate_whole_run(story, when):
    project, scene, note, cache, index = story
    context = run_context(story)
    provider = Provider(["Ideas", "More ideas"])

    def change():
        (project.root / note.path).write_text("An external author changed the source.", encoding="utf-8")

    if when == "review":
        context.review = lambda *args: (change() or ContextReviewDecision("send"))
    elif when == "generation":
        provider.effect = change
    if when in {"review", "generation"}:
        with pytest.raises(ProjectError):
            suggest_project_brief(provider, context.brief, 1400, .2, retrieval=context)
    else:
        suggest_project_brief(provider, context.brief, 1400, .2, retrieval=context)
        change()
        with pytest.raises(ProjectError):
            if when == "application":
                context.apply_outline((("New", ("Scene",)),))
            else:
                generate_project_outline(provider, context.brief, 1800, .2, retrieval=context)
    assert len(tuple(project.iter_scenes())) == 1


def test_unsaved_note_is_provenance_not_disk_cache(story):
    project, scene, note, cache, index = story
    before = index.path.read_bytes()
    context = run_context(story)
    context.buffers[note.id] = BufferText("The copper key is now kept by Mara in her pocket.", 7)
    provider = Provider(["Ideas"])
    suggest_project_brief(provider, context.brief, 1400, .2, retrieval=context)
    passage = next(p for p in context.steps[0].request.passages if p.source_id == note.id)
    assert passage.buffer_revision == 7 and "Mara" in passage.text
    assert index.path.read_bytes() == before


def test_oversized_required_transient_refuses_before_review_or_generation(story):
    context = run_context(story, review=lambda *a: pytest.fail("Overflow cannot be reviewed as a complete request"))
    context.context_tokens = 4096
    provider = Provider(["unused"])
    with pytest.raises(ContextBudgetError):
        context.generate(provider, "Scene", "Required task", role="Role", maximum_tokens=900, temperature=.2,
                         transient=(TransientDraft("draft-1", "Long draft", "x" * 10000),))
    assert not provider.calls


def test_run_evidence_limit_refuses_before_generation(story, monkeypatch):
    import app.project.planning_context as module
    monkeypatch.setattr(module, "MAX_REVIEW_BYTES", 1)
    context = run_context(story)
    provider = Provider(["unused"])
    with pytest.raises(ProjectError, match="16 MiB"):
        suggest_project_brief(provider, context.brief, 1400, .2, retrieval=context)
    assert not provider.calls


def test_application_failure_keeps_existing_files_and_rolls_back_additions(story, monkeypatch):
    project, scene, note, cache, index = story
    context = run_context(story)
    generate_project_outline(Provider(["# New\n- Scene"]), context.brief, 1800, .2, retrieval=context)
    manifest = project.manifest.to_mapping()
    before = set(project.root.rglob("*.txt"))

    def fail():
        raise ProjectError("Manifest write failed")

    monkeypatch.setattr(project, "_write_manifest", fail)
    with pytest.raises(ProjectError, match="Manifest write failed"):
        context.apply_autopilot((("New", (("Scene", "New draft"),)),), (("New character", "Profile"),))
    assert project.manifest.to_mapping() == manifest
    assert set(project.root.rglob("*.txt")) == before


def test_incomplete_autopilot_snapshot_refuses_without_a_model_call(story):
    project, scene, note, cache, index = story
    (project.root / note.path).unlink()
    context = run_context(story, require_complete=True)
    provider = Provider([PLAN])
    with pytest.raises(ProjectError, match="complete source snapshot"):
        run_autopilot(provider, context.brief, "", maximum_tokens=900, temperature=.2,
                      is_cancelled=lambda: False, retrieval=context)
    assert not provider.calls


def test_retrieved_autopilot_does_not_shorten_required_metadata_or_character_input(story):
    context = run_context(story)
    provider = Provider([PLAN, "First draft", "Second draft", "Third draft"])
    run_autopilot(provider, context.brief, "x" * 6000 + "OUTLINE_TAIL", character_context="y" * 6000 + "MOTIVATION_TAIL",
                  maximum_tokens=900, temperature=.2, is_cancelled=lambda: False, retrieval=context)
    assert "OUTLINE_TAIL" in provider.calls[0][0]
    assert all("MOTIVATION_TAIL" in prompt for prompt, options in provider.calls)


def test_complete_outline_metadata_is_opt_in_and_never_cuts_json(story):
    from app.project.outline import project_outline_metadata
    project, scene, note, cache, index = story
    # In-memory metadata suffices: this helper must not perform file I/O.
    from app.project.model import Chapter
    project.manifest.chapters.extend(Chapter(id=f"chapter-{i}", title="Long chapter " + str(i) + "x" * 150)
                                     for i in range(40))
    complete = json.loads(project_outline_metadata(project, complete=True))
    assert len(complete["chapters"]) == 41
    assert complete["chapters"][-1]["title"].startswith("Long chapter 39")
    assert len(project_outline_metadata(project)) <= 5000
