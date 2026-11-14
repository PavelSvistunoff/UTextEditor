"""Run-wide glossary, exact source review and translation transaction boundaries."""

import json

import pytest

from app.ai.context_budget import ContextBudgetError
from app.project import Project, ProjectError
from app.project.auto_writer_context import ContextReviewDecision
from app.project.rag_context import ProjectContextService
from app.project.rag_index import LexicalIndex
from app.project.rag_sources import BufferText, capture_project_sources
from app.project.translation import run_project_translation, commit_project_translation
from app.project.translation_context import (
    GlossaryTerm, TranslationRetrieval, ambiguous_terms, project_terminology, validate_glossary,
)


class Provider:
    def __init__(self):
        self.calls = []
        self.response = '{"translation":"Переклад"}'
        self.effect = lambda: None

    def generate_private(self, prompt, **options):
        self.calls.append((prompt, options))
        self.effect()
        return self.response


@pytest.fixture
def story(tmp_path):
    project = Project.create(tmp_path / "project", "Mara's key")
    scene = project.add_scene("Mara", content="Mara carries the copper key.")
    note = project.add_note("Copper key", content="Mara hides the copper key in the garden.")
    project.add_character("Mara")
    cache = tmp_path / "cache"
    LexicalIndex(cache, project.root, project.manifest.project_id).refresh(capture_project_sources(project))
    return project, scene, note, cache


def run(story, provider=None, review=None, tokens=65536, buffers=None):
    project, scene, note, cache = story
    provider = provider or Provider()
    retrieval = TranslationRetrieval(project, cache, tokens, buffers or {},
        (GlossaryTerm("Mara", "Мара"), GlossaryTerm("copper key", "мідний ключ")),
        review=review or (lambda title, captured, excluded: ContextReviewDecision("send", excluded)),
        is_cancelled=lambda: False)
    result = run_project_translation(provider, project, "English", "Ukrainian",
        {key: value.text for key, value in (buffers or {}).items()}, is_cancelled=lambda: False,
        retrieval=retrieval)
    return result, retrieval, provider


def payload(prompt):
    context = json.loads(prompt.split("<captured_context>\n")[1].split("\n</captured_context>")[0])
    return context, json.loads(context["mandatory_text"])


def test_same_approved_glossary_across_titles_contents_character_fields_and_exact_reviews(story):
    reviews = []
    def review(title, captured, excluded):
        reviews.append(captured)
        return ContextReviewDecision("send", excluded)
    result, retrieval, provider = run(story, review=review)
    assert len(provider.calls) >= 7
    for (prompt, options), reviewed in zip(provider.calls, reviews, strict=True):
        assert prompt == reviewed.prompt and options["role"] == reviewed.role
        assert options["json_mode"] and options["require_full_context"] and options["timeout"] == 300
        context, task = payload(prompt)
        assert task["direction"] == ["English", "Ukrainian"]
        assert task["author_approved_glossary"][0]["approved_translation"] == "Мара"
        assert "never reference passages" in options["role"]
    project, scene, note, _cache = story
    assert result.contents[scene.id] == "Переклад"
    assert project.read_scene(scene.id) == "Mara carries the copper key."
    assert len(retrieval.evidence) == len(provider.calls)
    commit = commit_project_translation(project, result)
    assert commit.project.read_scene(scene.id) == "Переклад"


def test_unsaved_target_full_and_reference_text_not_part_of_return_value(story):
    scene = story[1]
    original = "  Mara " + "x" * 14000 + "\r\n"
    result, retrieval, provider = run(story, buffers={scene.id: BufferText(original, 4)})
    assert any(payload(prompt)[1]["target_text"] == original for prompt, _ in provider.calls)
    assert result.contents[scene.id] == "  Переклад\r\n"


@pytest.mark.parametrize("response", ['plain prose', '{}', '{"translation":"x","references":"extra"}',
    '{"translation":[]}', '{"translation":""}', '{"translation":"\\u0000"}',
    '{"translation":"first","translation":"second"}'])
def test_malformed_or_extra_output_refuses_without_changing_project(story, response):
    provider = Provider()
    provider.response = response
    before = story[0].manifest_path.read_bytes()
    with pytest.raises(ProjectError):
        run(story, provider)
    assert story[0].manifest_path.read_bytes() == before


@pytest.mark.parametrize("when", ["review", "generation", "commit"])
def test_changed_reference_invalidates_whole_run_and_commit(story, when):
    project, scene, note, cache = story
    before = project.manifest_path.read_bytes()
    change = lambda: (project.root / note.path).write_text("Changed", encoding="utf-8")
    provider = Provider()
    def review(title, captured, excluded):
        if when == "review":
            change()
        return ContextReviewDecision("send", excluded)
    if when == "generation":
        provider.effect = change
    if when == "commit":
        result, _, _ = run(story, provider, review)
        change()
        with pytest.raises(ProjectError):
            commit_project_translation(project, result)
    else:
        with pytest.raises(ProjectError):
            run(story, provider, review)
    assert project.manifest_path.read_bytes() == before
    assert project.read_scene(scene.id) == "Mara carries the copper key."
    if when == "review":
        assert not provider.calls


def test_cancel_tiny_window_and_changed_exclusions_do_not_send(story):
    for review, tokens in [(lambda *args: ContextReviewDecision("cancel"), 65536),
        (lambda *args: ContextReviewDecision("send"), 100),
        (lambda *args: ContextReviewDecision("send", frozenset({story[2].id})), 65536)]:
        provider = Provider()
        with pytest.raises((ProjectError, ContextBudgetError)):
            run(story, provider, review, tokens)
        assert not provider.calls


def test_exclusions_rebuilt_and_reused_across_items(story):
    reviews = []
    excluded = frozenset({story[2].id})
    def review(title, captured, current):
        reviews.append(current)
        return ContextReviewDecision("send" if current else "rebuild", excluded)
    _, retrieval, provider = run(story, review=review)
    assert reviews[0] == frozenset() and all(item == excluded for item in reviews[1:])
    assert all(passage.source_id != story[2].id for evidence in retrieval.evidence for passage in evidence.passages)
    assert "Мара" in provider.calls[-1][0]


def test_no_index_and_no_matching_terms_keep_complete_task(story):
    project, scene, note, cache = story
    LexicalIndex(cache, project.root, project.manifest.project_id).delete()
    result, retrieval, provider = run(story)
    assert result.contents[scene.id] == "Переклад"
    assert all(not evidence.passages for evidence in retrieval.evidence)
    assert "if no term matches" in provider.calls[0][1]["role"]


def test_ambiguous_names_are_flagged_and_glossary_is_bounded(story):
    project = story[0]
    project.add_character("Mara")
    terms = project_terminology(project)
    assert "Mara" in ambiguous_terms(terms)
    assert ambiguous_terms((GlossaryTerm("Марія", "Maria"), GlossaryTerm("МАРІЯ", "Maria")))
    for invalid in [(GlossaryTerm("a", ""),), (GlossaryTerm("a", "b"),) * 2,
                    tuple(GlossaryTerm(str(i), "b") for i in range(257)),
                    (GlossaryTerm("a", "b" * 17000),)]:
        with pytest.raises(ProjectError):
            validate_glossary(invalid)


def test_cross_project_context_refused(story, tmp_path):
    other = Project.create(tmp_path / "other", "Other")
    retrieval = TranslationRetrieval(story[0], story[3], 65536, {}, (),
        review=lambda *args: ContextReviewDecision("send"), is_cancelled=lambda: False)
    with pytest.raises(ProjectError, match="another project"):
        run_project_translation(Provider(), other, "English", "Ukrainian", {},
                                is_cancelled=lambda: False, retrieval=retrieval)


def test_task_read_capture_race_refuses_before_send(story, monkeypatch):
    original = ProjectContextService.capture
    def capture(service, *args, **options):
        (story[0].root / story[2].path).write_text("Raced", encoding="utf-8")
        return original(service, *args, **options)
    monkeypatch.setattr(ProjectContextService, "capture", capture)
    provider = Provider()
    with pytest.raises(ProjectError, match="inputs changed"):
        run(story, provider)
    assert not provider.calls
