"""Dictionary guidance cannot change target offsets or suppress valid findings."""

import json

import pytest

from app.ai.spellcheck_service import SpellcheckService
from app.project import Project, ProjectError
from app.project.auto_writer_context import ContextReviewDecision
from app.project.spelling_context import SpellingDictionary


class Provider:
    def __init__(self):
        self.calls = []
        self.effect = lambda: None

    def generate_private(self, prompt, **options):
        self.calls.append((prompt, options))
        self.effect()
        return json.dumps([{"start": 3, "end": 7, "replacement": "Марія", "original_text": "Мара"}])

    def check_spelling(self, text, language):
        self.calls.append((text, language))
        return []


@pytest.fixture
def dictionary(tmp_path):
    project = Project.create(tmp_path / "project", "Story")
    project.add_character("Мара")
    scene = project.add_scene("Private scene", content="UNRELATED MANUSCRIPT DO NOT SEND")
    note = project.add_note("Key", content="UNRELATED NOTE PROSE DO NOT SEND")
    run = SpellingDictionary(project, 32768,
        review=lambda title, captured, excluded: ContextReviewDecision("send", excluded),
        is_cancelled=lambda: False)
    return project, scene, note, run


def test_dictionary_sends_only_names_not_prose_and_preserves_unicode_offsets(dictionary):
    project, scene, note, run = dictionary
    provider = Provider()
    reviews = []
    run.review = lambda title, captured, excluded: (reviews.append(captured) or ContextReviewDecision("send", excluded))
    suggestions = SpellcheckService(provider).check("🙂: Мара тут.", "Ukrainian", 9, dictionary=run)
    assert len(suggestions) == 1 and suggestions[0].start == 3 and suggestions[0].revision == 9
    assert suggestions[0].original_text == "Мара"  # A dictionary match is still a reviewable finding.
    prompt, options = provider.calls[0]
    assert prompt == reviews[0].prompt and options["require_full_context"] and options["json_mode"]
    assert "UNRELATED" not in prompt and "Private scene" not in prompt
    assert "Мара" in prompt and "Key" in prompt
    assert not [item for item in reviews[0].manifest.decisions if item.disposition in {"included", "shortened"}]
    assert "never the surrounding JSON" in options["role"]


def test_default_and_standalone_path_is_target_only(dictionary):
    provider = Provider()
    assert SpellcheckService(provider).check("teh", "English", 2) == []
    assert provider.calls == [("teh", "English")]


@pytest.mark.parametrize("change", ["review", "generation", "cancel", "exclude"])
def test_stale_cancelled_or_excluded_dictionary_refuses(dictionary, change):
    project, scene, note, run = dictionary
    provider = Provider()
    def mutate():
        (project.root / note.path).write_text("Changed source", encoding="utf-8")
    if change == "generation":
        provider.effect = mutate
    def review(*args):
        if change == "review":
            mutate()
        return ContextReviewDecision("cancel" if change == "cancel" else "send",
            frozenset({note.id}) if change == "exclude" else frozenset())
    run.review = review
    with pytest.raises(ProjectError):
        SpellcheckService(provider).check("🙂: Мара тут.", "Ukrainian", 3, dictionary=run)
    assert len(provider.calls) == (1 if change == "generation" else 0)


def test_no_dictionary_terms_and_no_index_remain_usable(tmp_path):
    project = Project.create(tmp_path / "empty", "Empty")
    run = SpellingDictionary(project, 32768, review=lambda *args: ContextReviewDecision("send"),
                             is_cancelled=lambda: False)
    provider = Provider()
    SpellcheckService(provider).check("🙂: Мара тут.", "Ukrainian", 3, dictionary=run)
    assert 'project_dictionary\\\": []' in provider.calls[0][0]


def test_other_project_dictionary_cannot_leak(dictionary, tmp_path):
    other = Project.create(tmp_path / "other", "Other")
    other.add_character("Isolated")
    provider = Provider()
    run = SpellingDictionary(other, 32768, review=lambda *args: ContextReviewDecision("send"),
                             is_cancelled=lambda: False)
    SpellcheckService(provider).check("🙂: Мара тут.", "Ukrainian", 3, dictionary=run)
    prompt = provider.calls[0][0]
    assert "Isolated" in prompt and "Key" not in prompt
