import os
import json
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from app.project import Project, ProjectError, parse_outline
from app.project.autopilot import AutopilotCancelled, run_autopilot
from app.project.auto_writer import run_auto_writer
from app.settings.settings import AppSettings
from app.ui.main_window import MainWindow
from app.ui.project_brief_dialog import PROJECT_BRIEF_TEMPLATE, ProjectBriefDialog
from app.ui.auto_writer_dialog import AutoWriterDialog, AutoWriterProgressDialog
from app.ui.project_setup_dialog import ProjectSetupDialog


@pytest.fixture(autouse=True)
def isolate_settings(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.yaml"
    monkeypatch.setattr(
        AppSettings,
        "_default_settings_path",
        staticmethod(lambda: settings_path),
    )
    AppSettings(ui_language="en").save(settings_path)


def test_parse_outline_returns_chapters_and_scenes():
    assert parse_outline(
        "\n# Arrival\n- Find the signal\n- Meet the guide\n\n# Departure\n"
    ) == (
        ("Arrival", ("Find the signal", "Meet the guide")),
        ("Departure", ()),
    )


@pytest.mark.parametrize(
    "text",
    [
        "",
        "- Scene before chapter",
        "# \n- Scene",
        "# Chapter\nUnstructured prose",
        "# " + ("x" * 161),
    ],
)
def test_parse_outline_rejects_invalid_or_oversized_content(text):
    with pytest.raises(ProjectError):
        parse_outline(text)


def test_add_outline_creates_empty_files_and_preserves_existing_project(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    original = project.add_scene("Existing", content="keep this prose")

    chapters = project.add_outline(
        (
            ("New Chapter", ("Opening", "Turning Point")),
            ("New Chapter", ("Opening",)),
        )
    )

    assert [chapter.title for chapter in chapters] == ["New Chapter", "New Chapter"]
    assert [scene.path for scene in chapters[0].scenes] == [
        "manuscript/opening.txt",
        "manuscript/turning-point.txt",
    ]
    assert chapters[1].scenes[0].path == "manuscript/opening-2.txt"
    assert all(project.read_scene(scene.id) == "" for chapter in chapters for scene in chapter.scenes)
    assert project.read_scene(original.id) == "keep this prose"
    reopened = Project.open(project.root)
    assert [chapter.title for chapter in reopened.manifest.chapters] == [
        "New Chapter",
        "New Chapter",
    ]


def test_add_outline_rolls_back_new_files_when_manifest_write_fails(tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    original_manifest = project.manifest.to_mapping()

    def fail_write():
        raise ProjectError("manifest write failed")

    monkeypatch.setattr(project, "_write_manifest", fail_write)
    with pytest.raises(ProjectError, match="manifest write failed"):
        project.add_outline((("Chapter", ("Scene",)),))

    assert project.manifest.to_mapping() == original_manifest
    assert not (project.root / "manuscript" / "scene.txt").exists()
    assert Project.open(project.root).manifest.to_mapping() == original_manifest


def test_autopilot_batch_adds_scene_drafts_and_character_notes(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    existing = project.add_scene("Existing", content="existing prose stays unchanged")

    chapters, characters = project.add_autopilot_content(
        (("New Chapter", (("Opening", "Generated scene text."),)),),
        (("Mara", "A careful cartographer seeking her missing mentor."),),
    )

    assert project.read_scene(existing.id) == "existing prose stays unchanged"
    assert project.read_scene(chapters[0].scenes[0].id) == "Generated scene text."
    assert characters[0].type == "character"
    assert project.read_note(characters[0].id).startswith("A careful cartographer")
    reopened = Project.open(project.root)
    assert reopened.read_scene(chapters[0].scenes[0].id) == "Generated scene text."


def test_autopilot_batch_rolls_back_files_and_manifest_on_failure(tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    original_manifest = project.manifest.to_mapping()
    original_write = project._write_manifest
    calls = 0

    def fail_write_after_validation():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ProjectError("manifest write failed")
        original_write()

    monkeypatch.setattr(project, "_write_manifest", fail_write_after_validation)
    with pytest.raises(ProjectError, match="manifest write failed"):
        project.add_autopilot_content(
            (("Chapter", (("Scene", "draft text"),)),),
            (("Character", "profile text"),),
        )

    assert project.manifest.to_mapping() == original_manifest
    assert not (project.root / "manuscript" / "scene.txt").exists()
    assert not (project.root / "notes" / "character.txt").exists()
    assert Project.open(project.root).manifest.to_mapping() == original_manifest


def test_project_outline_generation_uses_private_provider_and_limited_tokens():
    class FakeProvider:
        prompt = None
        options = None

        def generate_private(self, prompt, **options):
            self.prompt = prompt
            self.options = options
            return "# First Steps\n- Begin"

    provider = FakeProvider()
    result = MainWindow._generate_project_outline(provider, "A quiet mystery", 3000, 0.4)

    assert result == "# First Steps\n- Begin"
    assert "A quiet mystery" in provider.prompt
    assert "write any scene content" in provider.prompt
    assert provider.options["maximum_tokens"] == 1800
    assert provider.options["temperature"] == 0.4
    assert "Return an outline for author review" in provider.options["role"]


def test_autopilot_creates_bounded_plan_and_sequential_scene_drafts():
    plan = {
        "chapters": [
            {
                "title": "The Map Room",
                "scenes": [
                    {"title": "A Missing Atlas", "purpose": "Mara finds a hidden clue."},
                    {"title": "The Night Visit", "purpose": "An ally warns her."},
                ],
            }
        ],
        "characters": [{"name": "Mara", "profile": "A curious cartographer."}],
    }

    class FakeProvider:
        prompts = []

        def generate_private(self, prompt, **_options):
            self.prompts.append(prompt)
            if len(self.prompts) == 1:
                return json.dumps(plan)
            return f"Draft scene {len(self.prompts) - 1}."

    provider = FakeProvider()
    draft = run_autopilot(
        provider,
        "A cartographer finds a secret map.",
        '{"project":"Novel","chapters":[]}',
        maximum_tokens=900,
        temperature=0.3,
        is_cancelled=lambda: False,
    )

    assert draft.chapters == (
        (
            "The Map Room",
            (
                ("A Missing Atlas", "Draft scene 1."),
                ("The Night Visit", "Draft scene 2."),
            ),
        ),
    )
    assert draft.characters == (("Mara", "A curious cartographer."),)
    assert "A cartographer finds a secret map." in provider.prompts[0]
    assert "existing project outline metadata" in provider.prompts[0]
    assert "Draft scene 1." in provider.prompts[2]


def test_autopilot_cancellation_prevents_later_ai_calls():
    calls = []
    plan = {
        "chapters": [
            {"title": "One", "scenes": [{"title": "First", "purpose": "Open."}]}
        ],
        "characters": [],
    }

    class FakeProvider:
        def generate_private(self, prompt, **_options):
            calls.append(prompt)
            return json.dumps(plan)

    with pytest.raises(AutopilotCancelled):
        run_autopilot(
            FakeProvider(),
            "Brief",
            "Existing",
            maximum_tokens=900,
            temperature=0.2,
            is_cancelled=lambda: True,
        )
    assert calls == []


def test_autopilot_rejects_invalid_plan_without_scene_generation():
    class FakeProvider:
        calls = 0

        def generate_private(self, _prompt, **_options):
            self.calls += 1
            return '{"chapters": [], "characters": []}'

    provider = FakeProvider()
    with pytest.raises(ProjectError, match="must contain"):
        run_autopilot(
            provider,
            "Brief",
            "Existing",
            maximum_tokens=900,
            temperature=0.2,
            is_cancelled=lambda: False,
        )
    assert provider.calls == 1


def test_autopilot_context_contains_project_outline_metadata_not_document_text(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Existing Chapter")
    project.add_scene(
        "Existing Scene",
        chapter_id=chapter.id,
        content="private existing manuscript text",
    )
    project.add_note("Existing Character", "character", content="private character profile")

    metadata = MainWindow._project_outline_metadata(project)

    assert "Existing Chapter" in metadata
    assert "Existing Scene" in metadata
    assert "Existing Character" in metadata
    assert "private existing manuscript text" not in metadata
    assert "private character profile" not in metadata


def test_autopilot_ui_applies_complete_local_run_without_changing_existing_files(
    tmp_path, monkeypatch
):
    application = QApplication.instance() or QApplication([])
    project = Project.create(tmp_path / "novel", "Novel")
    existing = project.add_scene("Existing", content="keep existing text")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    dialog = ProjectBriefDialog(window)
    window._project_setup_brief_dialog = dialog
    dialog.autopilot_requested.connect(
        lambda brief: window._start_project_autopilot(project, dialog, brief)
    )
    plan = {
        "chapters": [
            {
                "title": "Added Chapter",
                "scenes": [{"title": "New Scene", "purpose": "Open the mystery."}],
            }
        ],
        "characters": [{"name": "New Character", "profile": "A careful observer."}],
    }
    calls = []

    def generate_private(prompt, **_options):
        calls.append(prompt)
        return json.dumps(plan) if len(calls) == 1 else "A complete draft scene."

    monkeypatch.setattr(window.provider, "generate_private", generate_private)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args: QMessageBox.StandardButton.Yes,
    )
    dialog.editor.setPlainText("Premise: a quiet mystery")
    dialog.autopilot_requested.emit(dialog.brief())

    loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)

    def check_complete():
        if (
            not window._project_busy
            and any(chapter.title == "Added Chapter" for chapter in project.manifest.chapters)
        ):
            loop.quit()

    timeout.start(3000)
    while (
        window._project_busy
        or not any(chapter.title == "Added Chapter" for chapter in project.manifest.chapters)
    ) and timeout.isActive():
        QTimer.singleShot(10, check_complete)
        loop.exec()

    added = next(chapter for chapter in project.manifest.chapters if chapter.title == "Added Chapter")
    character = next(note for note in project.manifest.notes if note.title == "New Character")
    assert project.read_scene(added.scenes[0].id) == "A complete draft scene."
    assert project.read_note(character.id) == "A careful observer."
    assert project.read_scene(existing.id) == "keep existing text"
    assert len(calls) == 2
    window._project_setup_brief_dialog = None
    dialog.close()
    window.close()


def test_auto_writer_refines_whole_project_and_snapshots_originals(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter One")
    scene = project.add_scene(
        "Opening", chapter_id=chapter.id, content="The old opening."
    )
    note = project.add_note(
        "Mara", "character", content="Mara keeps a journal."
    )

    class FakeProvider:
        prompt = None
        options = None

        def generate_private(self, prompt, **options):
            self.prompt = prompt
            self.options = options
            return "A refined opening."

    provider = FakeProvider()
    result = run_auto_writer(
        provider,
        project,
        "refine_all",
        "Keep a quiet, reflective voice.",
        {},
        maximum_tokens=1200,
        temperature=0.3,
        snapshot_name="Before Auto-writer",
        is_cancelled=lambda: False,
    )

    assert result.replacements == {scene.id: "A refined opening."}
    assert result.expected_disk_text == {scene.id: "The old opening."}
    assert "quiet, reflective voice" in provider.prompt
    assert "Mara keeps a journal" in provider.prompt
    assert "The old opening." in provider.prompt
    assert provider.options["timeout"] == 300
    from app.document.revisions import RevisionStore

    snapshot = RevisionStore(project.root / ".utexteditor" / "revisions").read(
        result.snapshot_path
    )
    assert snapshot.documents[scene.id] == "The old opening."
    assert snapshot.documents[note.id] == "Mara keeps a journal."
    assert chapter.title in str(snapshot.structure)


def test_auto_writer_uses_only_scene_associated_character_context(tmp_path):
    from app.project import CharacterStateChange, SceneCharacterAssociation

    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening")
    note = project.add_note("World", "general", content="Old note")
    associated = project.add_character("Mara")
    associated.primary_motivation = "Expose the council"
    project.update_character(associated.id, associated)
    unrelated = project.add_character("Ivo")
    unrelated.primary_motivation = "Unrelated secret plan"
    project.update_character(unrelated.id, unrelated)
    project.associate_character(
        scene.id,
        SceneCharacterAssociation(
            associated.id,
            state_changes=[CharacterStateChange("knowledge", "learned the code", evidence="Read the letter")],
        ),
    )

    class FakeProvider:
        prompt = ""

        def generate_private(self, prompt, **_options):
            self.prompt = prompt
            return "Draft text."

    provider = FakeProvider()
    run_auto_writer(provider, project, "write_empty", "", {note.id: "Unsaved world detail"}, maximum_tokens=900,
                    temperature=0.2, snapshot_name="Before draft", is_cancelled=lambda: False)
    assert "Unsaved world detail" in provider.prompt
    assert "Old note" not in provider.prompt
    assert "Expose the council" in provider.prompt
    assert "learned the code" in provider.prompt
    assert "Read the letter" in provider.prompt
    assert "Unrelated secret plan" not in provider.prompt


def test_story_planning_context_includes_directed_relationship_conflicts(tmp_path):
    from uuid import uuid4

    from app.project import CharacterRelationship
    from app.project.character_context import project_planning_context

    project = Project.create(tmp_path / "novel", "Novel")
    investigator = project.add_character("Mara")
    investigator.primary_motivation = "Expose the council"
    project.update_character(investigator.id, investigator)
    protector = project.add_character("Ivo")
    protector.primary_motivation = "Keep the council in power"
    project.update_character(protector.id, protector)
    outsider = project.add_character("Nia")
    project.update_character(outsider.id, outsider)
    project.add_character_relationship(CharacterRelationship(
        str(uuid4()), investigator.id, protector.id,
        relationship_type="opponents", description="Both need the ledger",
    ))

    context = project_planning_context(project)

    assert "Expose the council" in context
    assert "Keep the council in power" in context
    assert "Directed relationship: Mara → Ivo: opponents" in context
    assert "Nia" not in context


def test_auto_writer_writes_only_empty_scenes(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter")
    empty = project.add_scene("Empty", chapter_id=chapter.id)
    full = project.add_scene("Existing", chapter_id=chapter.id, content="Keep.")
    completed_scenes = []

    class FakeProvider:
        prompts = []
        options = []

        def generate_private(self, prompt, **options):
            self.prompts.append(prompt)
            self.options.append(options)
            return "Newly drafted scene."

    provider = FakeProvider()
    result = run_auto_writer(
        provider,
        project,
        "write_empty",
        "",
        {},
        maximum_tokens=1000,
        temperature=0.2,
        snapshot_name="Before writing",
        is_cancelled=lambda: False,
        scene_completed=lambda title, text, completed, total: completed_scenes.append(
            (title, text, completed, total)
        ),
    )

    assert result.replacements == {empty.id: "Newly drafted scene."}
    assert full.id not in result.replacements
    assert len(provider.prompts) == 1
    assert provider.options[0]["timeout"] == 300
    assert completed_scenes == [("Empty", "Newly drafted scene.", 1, 1)]


def test_auto_writer_progress_dialog_shows_completed_drafts():
    application = QApplication.instance() or QApplication([])
    dialog = AutoWriterProgressDialog()

    dialog.append_scene("Opening", "The rain began.", 1, 2)

    assert "Completed scene 1 of 2: Opening" == dialog.status.text()
    assert "The rain began." in dialog.output.toPlainText()
    dialog.finish("Auto-writer cancelled. No scene changes were applied.")
    assert dialog.cancel_button.text() == "Close"
    dialog.close()


def test_auto_writer_refuses_to_apply_if_project_text_changed(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="Original.")
    target = project.root / scene.path
    target.write_text("External edit.", encoding="utf-8")

    with pytest.raises(ProjectError, match="changed on disk"):
        project.replace_scenes_transactionally(
            {scene.id: "Generated."},
            expected_contents={scene.id: "Original."},
        )

    assert target.read_text(encoding="utf-8") == "External edit."


def test_auto_writer_transaction_replaces_all_targets_preserving_line_endings(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    first = project.add_scene("First", content="Before one.")
    second = project.add_scene("Second", content="Before two.")
    first_path = project.root / first.path
    second_path = project.root / second.path
    first_path.write_bytes(b"Before one.\r\n")
    first_path.chmod(0o640)

    persisted = project.replace_scenes_transactionally(
        {first.id: "After one.\nLine two.", second.id: "After two."},
        expected_contents={
            first.id: "Before one.\r\n",
            second.id: "Before two.",
        },
    )

    assert persisted[first.id] == "After one.\r\nLine two."
    assert first_path.read_bytes() == b"After one.\r\nLine two."
    assert first_path.stat().st_mode & 0o777 == 0o640
    assert second_path.read_text(encoding="utf-8") == "After two."


def test_auto_writer_transaction_rolls_back_all_targets_on_replace_failure(
    tmp_path, monkeypatch
):
    from pathlib import Path

    project = Project.create(tmp_path / "novel", "Novel")
    first = project.add_scene("First", content="Original one.")
    second = project.add_scene("Second", content="Original two.")
    first_path = project.root / first.path
    second_path = project.root / second.path
    original_rename = Path.rename
    failed_once = False

    def fail_second_install(path, target):
        nonlocal failed_once
        if (
            not failed_once
            and path.parent == second_path.parent
            and path.name.endswith(".tmp")
            and Path(target) == second_path
        ):
            failed_once = True
            raise OSError("simulated install failure")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_second_install)
    with pytest.raises(ProjectError, match="could not replace"):
        project.replace_scenes_transactionally(
            {first.id: "Generated one.", second.id: "Generated two."},
            expected_contents={
                first.id: "Original one.",
                second.id: "Original two.",
            },
        )

    assert first_path.read_text(encoding="utf-8") == "Original one."
    assert second_path.read_text(encoding="utf-8") == "Original two."
    assert not list(project.root.rglob("*.bak"))
    assert not list(project.root.rglob("*.tmp"))


def test_auto_writer_stage_failure_cleans_temporary_files(tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    first = project.add_scene("First", content="Original one.")
    second = project.add_scene("Second", content="Original two.")
    original_fsync = os.fsync
    calls = 0

    def fail_second_fsync(descriptor):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated staging failure")
        return original_fsync(descriptor)

    monkeypatch.setattr("app.project.service.os.fsync", fail_second_fsync)
    with pytest.raises(ProjectError, match="Cannot stage Auto-writer"):
        project.replace_scenes_transactionally(
            {first.id: "Generated one.", second.id: "Generated two."},
            expected_contents={
                first.id: "Original one.",
                second.id: "Original two.",
            },
        )

    assert project.read_scene(first.id) == "Original one."
    assert project.read_scene(second.id) == "Original two."
    assert not list(project.root.rglob("*.tmp"))


def test_auto_writer_keeps_pre_run_snapshot_if_generation_fails(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="Original text.")

    class FailedProvider:
        def generate_private(self, _prompt, **_options):
            raise RuntimeError("model unavailable")

    with pytest.raises(RuntimeError, match="model unavailable"):
        run_auto_writer(
            FailedProvider(),
            project,
            "refine_all",
            "",
            {},
            maximum_tokens=1200,
            temperature=0.2,
            snapshot_name="Before failed run",
            is_cancelled=lambda: False,
        )
    from app.document.revisions import RevisionStore

    snapshots, issues = RevisionStore(project.root / ".utexteditor" / "revisions").list_snapshots()
    assert not issues
    assert snapshots[0].documents[scene.id] == "Original text."


def test_auto_writer_ui_refines_scene_and_updates_open_buffer(
    tmp_path, monkeypatch
):
    application = QApplication.instance() or QApplication([])
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="Original text.")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window._open_project_document("scene", scene.id)

    loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)

    def check_opened():
        if window.tabs.count() == 2:
            loop.quit()

    timeout.start(3000)
    while window.tabs.count() != 2 and timeout.isActive():
        QTimer.singleShot(10, check_opened)
        loop.exec()
    editor = window.tabs.current_editor()
    assert editor is not None

    monkeypatch.setattr(
        AutoWriterDialog, "exec", lambda _self: QDialog.DialogCode.Accepted
    )
    monkeypatch.setattr(
        AutoWriterDialog, "values", lambda _self: ("refine_all", "Keep the voice quiet.")
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        window.provider,
        "generate_private",
        lambda _prompt, **_options: "Revised scene text.",
    )

    window.start_auto_writer()

    def check_written():
        if (
            not window._project_busy
            and project.read_scene(scene.id) == "Revised scene text."
        ):
            loop.quit()

    timeout.start(3000)
    while (
        window._project_busy
        or project.read_scene(scene.id) != "Revised scene text."
    ) and timeout.isActive():
        QTimer.singleShot(10, check_written)
        loop.exec()

    binding = window._project_documents[editor]
    assert editor.toPlainText() == "Revised scene text."
    assert not editor.document_state.dirty
    assert binding.expected_text == "Revised scene text."
    window.close()


def test_project_setup_dialog_requires_a_valid_author_reviewed_outline():
    application = QApplication.instance() or QApplication([])
    dialog = ProjectSetupDialog("# Chapter\nUnstructured text")
    assert not dialog.apply_button.isEnabled()

    dialog.editor.setPlainText("# Chapter\n- Opening")
    assert dialog.apply_button.isEnabled()
    assert dialog.outline() == (("Chapter", ("Opening",)),)

    dialog.apply_button.click()
    assert dialog.result() == QDialog.DialogCode.Accepted
    dialog.close()


def test_project_brief_dialog_starts_with_editable_template():
    application = QApplication.instance() or QApplication([])
    dialog = ProjectBriefDialog()

    assert dialog.brief() == PROJECT_BRIEF_TEMPLATE
    assert "Story premise:" in dialog.brief()
    assert "Structure preferences:" in dialog.brief()
    dialog.editor.setPlainText("My story details")
    assert dialog.brief() == "My story details"
    dialog.close()


def test_suggest_action_fills_template_using_private_local_ai(tmp_path, monkeypatch):
    application = QApplication.instance() or QApplication([])
    project = Project.create(tmp_path / "novel", "Novel")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    dialog = ProjectBriefDialog(window)
    window._project_setup_brief_dialog = dialog
    dialog.suggest_requested.connect(
        lambda text: window._suggest_project_brief(project, dialog, text)
    )
    submitted = "Story premise:\nA quiet mystery\n\nGenre:\n[unknown]"
    dialog.editor.setPlainText(submitted)
    prompt_capture = []

    def generate_private(prompt, **_options):
        prompt_capture.append(prompt)
        return "Story premise:\nA quiet mystery\n\nGenre:\n[Suggestion: cozy mystery]"

    monkeypatch.setattr(window.provider, "generate_private", generate_private)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args: QMessageBox.StandardButton.Yes,
    )
    dialog.suggest_button.click()

    loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)

    def check_complete():
        if dialog.brief().endswith("[Suggestion: cozy mystery]"):
            loop.quit()

    timeout.start(3000)
    while not dialog.brief().endswith("[Suggestion: cozy mystery]") and timeout.isActive():
        QTimer.singleShot(10, check_complete)
        loop.exec()

    assert dialog.brief().endswith("[Suggestion: cozy mystery]")
    assert submitted in prompt_capture[0]
    assert "other project" not in prompt_capture[0]
    assert not window._project_busy
    window._project_setup_brief_dialog = None
    dialog.close()
    window.close()
