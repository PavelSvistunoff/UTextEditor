import os
from pathlib import Path
from threading import Event
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QInputDialog

from app.document.revisions import RevisionComparison, RevisionStore, SceneChange
from app.project import Project, WordCount
from app.document.export import ExportChapter, ExportScene
from app.ui.main_window import MainWindow
from app.ui.project_view import ProjectView
from app.ui.character_dialog import CharacterDialog
from app.ui.character_relationship_dialog import CharacterRelationshipDialog
from app.ui.revision_history_dialog import RevisionHistoryDialog
from app.ui.settings_dialog import SettingsDialog
from app.settings.settings import AppSettings


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def isolate_settings(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.yaml"
    monkeypatch.setattr(
        AppSettings,
        "_default_settings_path",
        staticmethod(lambda: settings_path),
    )
    AppSettings(ui_language="en").save(settings_path)


def wait_until(predicate, application):
    if predicate():
        return
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)

    def check():
        if predicate():
            loop.quit()

    application.aboutToQuit.connect(loop.quit)
    timer.start(3000)
    while not predicate() and timer.isActive():
        QTimer.singleShot(10, check)
        loop.exec()
    assert predicate()


def test_project_tree_counts_and_project_scene_save_are_integrated(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter One")
    scene = project.add_scene("Opening", chapter_id=chapter.id, content="hello world")
    project.add_note("Character", "character", content="not manuscript")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)

    wait_until(lambda: window.project_view is not None and window.project_view.topLevelItemCount() > 0, application)

    root = window.project_view.topLevelItem(0)
    assert "2 words" in root.text(0)
    assert root.childCount() == 3
    chapter_item = root.child(0)
    assert "2 words" in chapter_item.text(0)
    scene_item = chapter_item.child(0)
    assert scene_item.data(0, Qt.ItemDataRole.UserRole + 1) == scene.id

    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    assert editor is not None
    assert editor.toPlainText() == "hello world"
    editor.setPlainText("edited manuscript")
    result: list[bool] = []
    window._save_editor(editor, callback=result.append)
    wait_until(lambda: result, application)

    assert result == [True]
    assert project.read_scene(scene.id) == "edited manuscript"
    assert not editor.document_state.dirty
    assert root.child(2).text(0) == "Characters (0)"
    window.close()


def test_activating_character_profile_opens_editor_instead_of_note_document(
    application, tmp_path, monkeypatch
):
    AppSettings(ui_language="en").save()
    project = Project.create(tmp_path / "character-project", "Novel")
    character = project.add_character("Mara")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    opened = []
    monkeypatch.setattr(window, "_edit_character", opened.append)
    window.project = project
    view = ProjectView()
    view.open_requested.connect(window._open_project_document)
    view.show_project(project, {}, {}, WordCount(0, True))
    character_group = next(
        view.topLevelItem(0).child(index)
        for index in range(view.topLevelItem(0).childCount())
        if view.topLevelItem(0).child(index).text(0).startswith("Characters (")
    )

    view.itemActivated.emit(character_group.child(0), 0)

    assert len(opened) == 1
    assert opened[0].id == character.id
    assert window.tabs.count() == 1
    translator = window._ui_translator
    window.close()
    if translator is not None:
        application.removeTranslator(translator)


def test_stale_note_tree_item_is_ignored_and_project_tree_refreshed(
    application, tmp_path, monkeypatch
):
    AppSettings(ui_language="en").save()
    project = Project.create(tmp_path / "stale-project", "Novel")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    refreshed = []
    monkeypatch.setattr(window, "_refresh_project_view", lambda: refreshed.append(True))
    window.project = project

    window._open_project_document("note", "removed-note-id")

    assert refreshed == [True]
    assert "no longer exists" in window.statusBar().currentMessage()
    assert not window._pending_project_opens
    translator = window._ui_translator
    window.close()
    if translator is not None:
        application.removeTranslator(translator)


def test_character_profile_dialog_keeps_edits_pending_until_save(application, monkeypatch):
    from app.project import Character

    character = Character(id="00000000-0000-4000-8000-000000000001", full_name="Mara")
    dialog = CharacterDialog(character)
    dialog.full_name.setText("Mara Venn")
    dialog.motivation.setPlainText("Expose the council")
    dialog.goals.setPlainText("Find the ledger | active | 1 | before the trial")
    assert character.full_name == "Mara"
    dialog._accept()
    assert dialog.character.full_name == "Mara Venn"
    assert dialog.character.primary_motivation == "Expose the council"
    assert dialog.character.goals[0].status == "active"
    assert dialog.character.goals[0].priority == 1
    assert dialog.character.goals[0].notes == "before the trial"
    dialog.close()


def test_character_ai_suggestions_require_review_and_leave_existing_fields(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    dialog = CharacterDialog(character)
    dialog.description.setPlainText("Existing description")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(window.provider, "generate_private", lambda *args, **kwargs: '{"primary_motivation":"Find the key"}')
    monkeypatch.setattr("app.ui.main_window.GeneratedTextDialog.exec", lambda self: self.DialogCode.Accepted)
    window._suggest_character_profile(dialog, project)
    wait_until(lambda: dialog.ai_button.isEnabled(), application)
    assert dialog.motivation.toPlainText() == "Find the key"
    assert dialog.description.toPlainText() == "Existing description"
    assert project.get_character(character.id).primary_motivation == ""
    dialog.reject()
    window.close()


def test_character_ai_discards_result_if_profile_changes(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    dialog = CharacterDialog(character)
    started, release = Event(), Event()
    def generate(*args, **kwargs):
        started.set()
        release.wait(3)
        return '{"primary_motivation":"Generated"}'
    messages = []
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *args: messages.append(args))
    monkeypatch.setattr(window.provider, "generate_private", generate)
    window._suggest_character_profile(dialog, project)
    wait_until(started.is_set, application)
    dialog.motivation.setPlainText("My idea")
    release.set()
    wait_until(lambda: bool(messages), application)
    assert dialog.motivation.toPlainText() == "My idea"
    dialog.reject()
    window.close()


def test_character_profile_relationships_are_staged_and_saved_together(application, tmp_path, monkeypatch):
    from app.project import CharacterRelationship
    from uuid import uuid4

    project = Project.create(tmp_path / "novel", "Novel")
    mara = project.add_character("Mara")
    ivo = project.add_character("Ivo")
    relation = CharacterRelationship(str(uuid4()), ivo.id, mara.id, relationship_type="rival")
    project.add_character_relationship(relation)
    dialog = CharacterDialog(mara, project_characters=project.manifest.characters,
                             project_relationships=project.manifest.character_relationships)
    assert "← Ivo: rival" in dialog.relationship_list.item(0).text()
    dialog.relationship_list.setCurrentRow(0)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    dialog._remove_relationship()
    assert len(project.manifest.character_relationships) == 1
    dialog.full_name.setText("Mara Venn")
    dialog._accept()
    project.update_character_with_relationships(mara.id, dialog.character, dialog.relationships)
    reopened = Project.open(project.root)
    assert reopened.get_character(mara.id).full_name == "Mara Venn"
    assert reopened.manifest.character_relationships == []
    dialog.close()


def test_character_profile_adds_relationship_without_mutating_project(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    mara = project.add_character("Mara")
    ivo = project.add_character("Ivo")
    dialog = CharacterDialog(mara, project_characters=project.manifest.characters)
    monkeypatch.setattr(QInputDialog, "getItem", lambda *args: (args[3][0], True))
    monkeypatch.setattr(CharacterRelationshipDialog, "exec", lambda self: self.DialogCode.Accepted)
    dialog._add_relationship()
    assert len(dialog.relationships) == 1
    assert (dialog.relationships[0].source_id, dialog.relationships[0].target_id) == (mara.id, ivo.id)
    dialog.relationship_list.setCurrentRow(0)
    def edit_relationship(self):
        self.relationship.relationship_type = "ally"
        return self.DialogCode.Accepted
    monkeypatch.setattr(CharacterRelationshipDialog, "exec", edit_relationship)
    dialog._edit_relationship()
    assert dialog.relationships[0].relationship_type == "ally"
    assert not project.manifest.character_relationships
    dialog.reject()
    assert not Project.open(project.root).manifest.character_relationships


def test_profile_and_relationship_update_rolls_back_on_write_failure(tmp_path, monkeypatch):
    from app.project import CharacterRelationship
    from uuid import uuid4

    project = Project.create(tmp_path / "novel", "Novel")
    mara = project.add_character("Mara")
    ivo = project.add_character("Ivo")
    mara.full_name = "Changed"
    relationship = CharacterRelationship(str(uuid4()), mara.id, ivo.id, "ally")
    def fail_write():
        raise OSError("write failed")
    monkeypatch.setattr(project, "_write_manifest", fail_write)
    with pytest.raises(OSError, match="write failed"):
        project.update_character_with_relationships(mara.id, mara, [relationship])
    assert project.get_character(mara.id).full_name == "Mara"
    assert not project.manifest.character_relationships
    assert Project.open(project.root).get_character(mara.id).full_name == "Mara"


def test_character_profile_dialog_rejects_invalid_goal_status(application, monkeypatch):
    from app.project import Character

    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    dialog = CharacterDialog(Character(id="00000000-0000-4000-8000-000000000001", full_name="Mara"))
    dialog.goals.setPlainText("Find the ledger | unknown | 3")
    dialog._accept()
    assert dialog.result() == 0
    assert warnings
    dialog.close()


def test_character_profile_dialog_can_clear_existing_personality_fields(application):
    from app.project import Character

    character = Character(
        id="00000000-0000-4000-8000-000000000001",
        full_name="Mara",
        personality={"strengths": ["patient"], "fears": ["fire"]},
    )
    dialog = CharacterDialog(character)
    dialog.personality_fields["strengths"].clear()
    dialog.personality_fields["fears"].setPlainText("")

    dialog._accept()

    assert "strengths" not in dialog.character.personality
    assert "fears" not in dialog.character.personality
    assert character.personality == {"strengths": ["patient"], "fears": ["fire"]}
    dialog.close()


def test_character_relationship_dialog_edits_structured_fields_and_validates_trust(
    application, monkeypatch
):
    from uuid import uuid4

    from app.project import CharacterRelationship

    relationship = CharacterRelationship(str(uuid4()), str(uuid4()), str(uuid4()))
    dialog = CharacterRelationshipDialog(relationship)
    dialog.relationship_type.setText("reluctant ally")
    dialog.attitude.setText("wary")
    dialog.trust.setText("72")
    dialog.status.setText("strained")
    dialog.shared_secrets.setPlainText("They both hid the letter.")
    dialog._accept()

    assert dialog.relationship.relationship_type == "reluctant ally"
    assert dialog.relationship.attitude == "wary"
    assert dialog.relationship.trust == 72
    assert dialog.relationship.status == "strained"
    assert dialog.relationship.shared_secrets == "They both hid the letter."
    assert relationship.relationship_type == "unknown"
    dialog.close()

    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    invalid = CharacterRelationshipDialog(relationship)
    invalid.trust.setText("101")
    invalid._accept()
    assert invalid.result() == 0
    assert warnings
    invalid.close()


def test_scene_character_selector_disambiguates_duplicate_display_names(
    application, tmp_path, monkeypatch
):
    project = Project.create(tmp_path / "novel", "Novel")
    first = project.add_character("Alex")
    second = project.add_character("Alex")
    scene = project.add_scene("Meeting")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    monkeypatch.setattr(window, "_selected_project_item", lambda: ("scene", scene.id))
    choices = []

    def choose(_parent, _title, _label, items, *_args):
        choices.append(list(items))
        return items[1], True

    monkeypatch.setattr(QInputDialog, "getItem", choose)
    monkeypatch.setattr(QInputDialog, "getText", lambda *_args, **_kwargs: ("purpose", True))
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *_args: ("", True))
    mutations = []
    monkeypatch.setattr(
        window, "_run_project_mutation", lambda operation, *args, **kwargs: mutations.append((operation, args))
    )

    window.associate_project_character()

    assert choices[0][0] != choices[0][1]
    association = mutations[0][1][1]
    assert association.character_id == second.id
    assert association.character_id != first.id
    window.close()


def test_reassociating_character_prefills_existing_scene_development_and_state(
    application, tmp_path, monkeypatch
):
    from app.project import CharacterStateChange, SceneCharacterAssociation

    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    scene = project.add_scene("Meeting")
    existing = SceneCharacterAssociation(
        character.id,
        presence="mentioned",
        purpose="warns Ivo",
        development_notes=["admits she is afraid"],
        state_changes=[
            CharacterStateChange("knowledge", "knows the code", "does not know", "reads the letter")
        ],
    )
    project.associate_character(scene.id, existing)
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    monkeypatch.setattr(window, "_selected_project_item", lambda: ("scene", scene.id))
    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        lambda _p, title, _l, items, index, _editable: (
            items[-1] if title == "Associate character" else items[index],
            True,
        ),
    )
    text_defaults = []

    def get_text(_parent, _title, _label, **kwargs):
        text_defaults.append(kwargs.get("text", ""))
        return kwargs.get("text", ""), True

    def get_multiline(_parent, _title, _label, default=""):
        text_defaults.append(default)
        return default, True

    monkeypatch.setattr(QInputDialog, "getText", get_text)
    monkeypatch.setattr(QInputDialog, "getMultiLineText", get_multiline)
    mutations = []
    monkeypatch.setattr(
        window,
        "_run_project_mutation",
        lambda operation, *args, **kwargs: mutations.append((operation, args)),
    )

    window.associate_project_character()

    updated = mutations[0][1][1]
    assert updated.presence == "mentioned"
    assert updated.purpose == "warns Ivo"
    assert updated.development_notes == ["admits she is afraid"]
    assert updated.state_changes == existing.state_changes
    assert text_defaults == [
        "warns Ivo",
        "admits she is afraid",
        "knowledge | knows the code | does not know | reads the letter",
    ]
    window.close()


def test_project_tree_character_filter_searches_profile_metadata(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    mara = project.add_character("Mara Venn")
    mara.role = "investigator"
    mara.primary_motivation = "Expose the council"
    project.update_character(mara.id, mara)
    project.add_character("Ivo")
    view = ProjectView()
    view.show_project(project, {}, {}, type("Count", (), {"count": 0, "complete": True})())
    view.filter_characters("council")
    group = view.topLevelItem(0).child(view.topLevelItem(0).childCount() - 1)
    assert group.childCount() == 2
    assert not group.child(0).isHidden()
    assert group.child(1).isHidden()
    view.close()


def test_character_context_menu_exposes_relationship_io_and_scene_search():
    action_ids = {
        action_id for _label, action_id in ProjectView.context_actions("character")
    }
    assert {
        "manage_relationships",
        "find_character_scenes",
        "import_character",
        "export_character",
    } <= action_ids


@pytest.mark.parametrize("kind", ["", "project", "group", "character", "scene", "note", "chapter"])
def test_project_context_menu_offers_new_character(kind):
    assert ("New Character…", "new_character") in ProjectView.context_actions(kind)


def test_project_context_menu_creates_character(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    monkeypatch.setattr(QInputDialog, "getText", lambda *args: ("Mara", True))
    window.project_view.context_action_requested.emit("new_character", "group", "")
    wait_until(lambda: any(c.full_name == "Mara" for c in project.manifest.characters) and not window._project_busy, application)
    assert Project.open(project.root).manifest.characters[0].full_name == "Mara"
    window.close()


def test_repeated_project_document_open_coalesces_pending_reads(
    application, tmp_path, monkeypatch
):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="original")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)

    read_started = Event()
    release_read = Event()
    read_calls = []
    original_read = project.read_scene

    def delayed_read(scene_id):
        read_calls.append(scene_id)
        read_started.set()
        if not release_read.wait(3):
            raise TimeoutError("Test did not release the project scene read.")
        return original_read(scene_id)

    monkeypatch.setattr(project, "read_scene", delayed_read)
    try:
        window._open_project_document("scene", scene.id)
        assert read_started.wait(2)
        window._open_project_document("scene", scene.id)
        assert read_calls == [scene.id]

        release_read.set()
        wait_until(lambda: window.tabs.count() == 2, application)

        path = project.root / scene.path
        window._project_document_opened(
            project, "scene", scene.id, path, "original"
        )
        window._open_project_document("scene", scene.id)
        assert window.tabs.count() == 2
        assert read_calls == [scene.id]
        assert sum(
            binding.item_id == scene.id
            for binding in window._project_documents.values()
        ) == 1
    finally:
        release_read.set()
        window.close()


def test_project_tree_context_actions_route_to_selected_scene(
    application, tmp_path, monkeypatch
):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="A beginning.")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    wait_until(
        lambda: window.project_view is not None
        and window.project_view.topLevelItemCount() > 0,
        application,
    )

    item = window.project_view.topLevelItem(0).child(0).child(0)
    window.project_view.setCurrentItem(item)
    actions = dict(ProjectView.context_actions("scene"))
    assert "move_to_chapter" in actions.values()
    assert "summarize" in actions.values()
    called = []
    monkeypatch.setattr(
        window,
        "rename_project_item",
        lambda: called.append(window._selected_project_item()),
    )
    window.project_view.context_action_requested.emit("rename", "scene", scene.id)

    assert called == [("scene", scene.id)]
    window.close()


def test_settings_connection_test_runs_and_reports_result(application, monkeypatch):
    monkeypatch.setattr(
        "app.ui.main_window.OllamaClient.check_connection", lambda _self: True
    )
    window = MainWindow()
    dialog = SettingsDialog(window.settings, window)

    window._test_settings_connection(
        dialog, "http://localhost:11434", "gemma4:12b"
    )
    wait_until(
        lambda: "Connected" in dialog.connection_status.text(),
        application,
    )

    assert "gemma4:12b" in dialog.connection_status.text()
    dialog.close()
    window.close()


def test_project_open_failure_keeps_previous_project_and_documents(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "working", "Working")
    bad_project = tmp_path / "bad"
    bad_project.mkdir()
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    original_editor = window.tabs.current_editor()
    monkeypatch.setattr(QMessageBox, "warning", lambda *_args: QMessageBox.StandardButton.Ok)

    window._open_project_worker(Project.open, bad_project)
    wait_until(lambda: not window._project_busy, application)

    assert window.project is project
    assert window.tabs.current_editor() is original_editor
    window.close()


def test_recent_projects_menu_tracks_successful_opens_and_routes_selection(
    application, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "app.ui.main_window.OllamaClient.check_connection", lambda _self: True
    )
    older = Project.create(tmp_path / "older-project", "Older")
    recent = Project.create(tmp_path / "recent-project", "Recent")
    window = MainWindow()
    window._project_opened(older)
    window._project_opened(recent)

    assert window.settings.recent_projects == [str(recent.root), str(older.root)]
    recent_menu = window._recent_projects_menu
    window._populate_recent_projects_menu()
    selected = next(
        action for action in recent_menu.actions()
        if action.data() == str(older.root)
    )
    assert "older-project" in selected.text()

    opened = []
    monkeypatch.setattr(
        window,
        "_open_project_worker",
        lambda operation, *args: opened.append((operation, args)),
    )
    selected.trigger()
    assert opened == [(Project.open, (str(older.root),))]

    clear_action = next(
        action for action in recent_menu.actions()
        if action.text() == "Clear Recent Projects"
    )
    clear_action.trigger()
    assert window.settings.recent_projects == []
    assert recent_menu.actions()[0].text() == "No Recent Projects"
    window.close()


def test_selected_scene_export_does_not_read_unselected_scene(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter One")
    included = project.add_scene("Included", chapter_id=chapter.id, content="Export this.")
    excluded = project.add_scene("Excluded", chapter_id=chapter.id, content="Unavailable.")
    (project.root / project.get_scene(excluded.id).path).unlink()

    output = MainWindow._export_project_snapshot(
        project,
        [ExportChapter("Chapter One", (
            ExportScene(included.id, "Included"),
            ExportScene(excluded.id, "Excluded"),
        ))],
        [],
        {},
        tmp_path / "selected.md",
        "markdown",
        False,
        {included.id},
        True,
        True,
        "\n\n",
    )

    assert output.read_text(encoding="utf-8") == (
        "# Chapter One\n\n## Included\n\nExport this."
    )


def test_revision_history_dialog_loads_and_compares_snapshots(
    application, tmp_path
):
    project = Project.create(tmp_path / "novel", "Novel")
    scene_id = project.add_scene("Opening", content="First draft.").id
    store = RevisionStore(project.root / ".utexteditor" / "revisions")
    before = store.create(
        "Before",
        structure={},
        scene_order=[scene_id],
        scene_titles={scene_id: "Opening"},
        documents={scene_id: "First draft.\n"},
    )
    store.create(
        "After",
        structure={},
        scene_order=[scene_id],
        scene_titles={scene_id: "Opening"},
        documents={scene_id: "Second draft.\n"},
    )
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)

    window.review_revision_snapshots()
    wait_until(
        lambda: window._revision_history_dialog is not None
        and window._revision_history_dialog.snapshots.count() == 2,
        application,
    )
    dialog = window._revision_history_dialog
    assert dialog is not None
    dialog.snapshots.item(0).setSelected(True)
    dialog.snapshots.item(1).setSelected(True)
    dialog.compare_button.click()
    wait_until(
        lambda: "Second draft." in dialog.details.toPlainText(),
        application,
    )

    assert "Text Changed: Opening" in dialog.details.toPlainText()
    assert "-First draft." in dialog.details.toPlainText()
    assert "+Second draft." in dialog.details.toPlainText()
    dialog.snapshots.clearSelection()
    dialog.show_error("Comparison failed.")
    assert not dialog.compare_button.isEnabled()
    dialog.close()
    window.close()


def test_revision_history_dialog_labels_reference_note_changes(application):
    dialog = RevisionHistoryDialog()

    dialog.show_comparison(RevisionComparison((
        SceneChange(
            "character-id",
            "type-changed",
            old_title="Mira",
            new_title="Mira",
            item_type="note",
            old_note_type="character",
            new_note_type="research",
        ),
    )))

    assert "Reference Note Type Changed: Mira" in dialog.details.toPlainText()
    assert "Type: character → research" in dialog.details.toPlainText()
    assert "1 project item change" in dialog.status.text()
    dialog.close()


def test_project_translation_actions_translate_and_refresh_open_documents(
    application, tmp_path, monkeypatch
):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter One")
    scene = project.add_scene(
        "Opening", chapter_id=chapter.id, content="Original scene."
    )
    note = project.add_note("Character", "character", content="Original note.")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window.settings.autosave_enabled = False
    confirmation_text = []

    def confirm_translation(_parent, _title, text, *_args, **_kwargs):
        confirmation_text.append(text)
        return QMessageBox.StandardButton.Yes

    monkeypatch.setattr(
        QMessageBox,
        "question",
        confirm_translation,
    )
    prompts = []

    def translate(prompt, **_options):
        prompts.append(prompt)
        return f"Translated {len(prompts)}"

    monkeypatch.setattr(window.provider, "generate_private", translate)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("Unsaved scene text.")

    project_menu = next(
        action.menu()
        for action in window.menuBar().actions()
        if action.text() == "Project"
    )
    menu_actions = {action.text() for action in project_menu.actions()}
    assert "Translate Project to Ukrainian…" in menu_actions
    assert "Translate Project to English…" in menu_actions

    window.translate_project_to_ukrainian()
    assert confirmation_text and window.provider.host in confirmation_text[0]
    wait_until(
        lambda: not window._project_busy
        and window.project is not None
        and window.project.manifest.title == "Translated 1",
        application,
    )

    assert window.project is not None
    assert window.project.manifest.chapters[0].title == "Translated 2"
    assert window.project.get_scene(scene.id).title == "Translated 3"
    assert window.project.get_note(note.id).title == "Translated 4"
    assert window.project.read_scene(scene.id) == "Translated 5"
    assert window.project.read_note(note.id) == "Translated 6"
    assert editor.toPlainText() == "Translated 5"
    assert not editor.document_state.dirty
    assert any("Unsaved scene text." in prompt for prompt in prompts)
    editor.document_state.mark_saved()
    window.close()


def test_project_scene_autosaves_after_idle_and_can_be_disabled(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="original")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    wait_until(lambda: window.project_view is not None and window.project_view.topLevelItemCount() > 0, application)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    assert editor is not None
    window.settings.autosave_idle_ms = 250
    editor.setPlainText("autosaved words")

    timer = window._autosave_timers[editor]
    assert timer.isActive()
    assert timer.interval() == 250
    timer.timeout.emit()
    wait_until(
        lambda: project.read_scene(scene.id) == "autosaved words" and not editor.document_state.dirty,
        application,
    )

    window.settings.autosave_enabled = False
    editor.setPlainText("manual save required")
    assert not timer.isActive()
    window._autosave_project_document(editor)
    assert editor.document_state.dirty
    assert project.read_scene(scene.id) == "autosaved words"
    editor.document_state.mark_saved()
    window.close()


def test_project_scene_save_preserves_crlf_line_endings(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="first\nsecond\n")
    target = project.root / scene.path
    target.write_bytes(b"first\r\nsecond\r\n")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    assert editor is not None
    assert editor.toPlainText() == "first\nsecond\n"
    assert editor.document_state.line_ending == "CRLF"
    editor.setPlainText("first\nchanged\n")
    result: list[bool] = []
    window._save_editor(editor, callback=result.append)
    wait_until(lambda: result, application)

    assert result == [True]
    assert target.read_bytes() == b"first\r\nchanged\r\n"
    editor.document_state.mark_saved()
    window.close()


def test_compile_book_uses_unsaved_scene_buffer_without_changing_project(
    application, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "app.ui.main_window.OllamaClient.check_connection", lambda _self: True
    )
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter One")
    scene = project.add_scene("Opening", chapter_id=chapter.id, content="saved text")
    target = tmp_path / "compiled-book.pdf"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(target), "PDF book (*.pdf)"),
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    compile_errors = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *_args: compile_errors.append(_args[-1]),
    )
    window = MainWindow()
    # PDF compilation is independent of AI; keep the test offline and avoid
    # scheduling completion/spellcheck workers while editing the fixture.
    window.settings.ai_enabled = False
    window._project_opened(project)
    assert window._project_actions["Compile Book as PDF…"].isEnabled()
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    window.settings.autosave_enabled = False
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("current unsaved text")

    window.compile_project_book()
    wait_until(
        lambda: (
            "Book PDF compiled" in window.statusBar().currentMessage()
            or bool(compile_errors)
        ),
        application,
    )
    assert not compile_errors, compile_errors

    pdf = QPdfDocument(application)
    pdf.load(str(target))
    content = "\n".join(
        pdf.getAllText(index).text() for index in range(pdf.pageCount())
    )
    assert "current unsaved text" in content
    assert "\r\nsaved text\r\n" not in content
    assert project.read_scene(scene.id) == "saved text"
    editor.document_state.mark_saved()
    window.close()


def test_project_analysis_uses_only_explicit_scene_and_reference_context(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="scene text")
    selected = project.add_note("Selected", "character", content="selected reference")
    other = project.add_note("Not selected", "research", content="private unrelated note")

    class FakeProvider:
        prompt = None

        def generate_private(self, prompt, **_options):
            self.prompt = prompt
            return ""

    provider = FakeProvider()
    result = MainWindow._run_project_analysis(
        provider,
        project,
        "continuity",
        scene.id,
        (selected.id,),
        {},
        2000,
        "review only",
        100,
        0.2,
    )

    assert result == ""
    assert "scene text" in provider.prompt
    assert "selected reference" in provider.prompt
    assert "private unrelated note" not in provider.prompt
    assert other.id not in provider.prompt


def test_project_analysis_includes_only_associated_character_context(tmp_path):
    from app.project import CharacterKnowledge, SceneCharacterAssociation

    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="scene text")
    selected = project.add_character("Mara")
    selected.primary_motivation = "Expose the council"
    selected.knowledge = [CharacterKnowledge("does_not_know", "The witness survived")]
    project.update_character(selected.id, selected)
    unrelated = project.add_character("Ivo")
    unrelated.primary_motivation = "Irrelevant plan"
    project.update_character(unrelated.id, unrelated)
    project.associate_character(scene.id, SceneCharacterAssociation(selected.id))

    class FakeProvider:
        prompt = None

        def generate_private(self, prompt, **_options):
            self.prompt = prompt
            return "review"

    provider = FakeProvider()
    MainWindow._run_project_analysis(provider, project, "continuity", scene.id, (), {}, 4000, "review", 100, 0.2)
    assert "Expose the council" in provider.prompt
    assert "The witness survived" in provider.prompt
    assert "Irrelevant plan" not in provider.prompt


def test_project_scene_completion_receives_notes_and_associated_characters(application, tmp_path, monkeypatch):
    from app.project import SceneCharacterAssociation
    from PySide6.QtGui import QTextCursor

    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="The beginning")
    note = project.add_note("World", content="A hidden door")
    character = project.add_character("Mara")
    character.primary_motivation = "Find the key"
    project.update_character(character.id, character)
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: any(b.item_id == scene.id for b in window._project_documents.values()), application)
    editor = window.tabs.current_editor()
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window.settings.ai_enabled = True
    window.settings.completion_enabled = True
    received = []
    monkeypatch.setattr(window.completion_service, "complete", lambda context, language, **kw: (received.append(context) or " continues"))
    window.request_completion()
    wait_until(lambda: bool(received), application)
    assert "Find the key" in received[0]
    assert "A hidden door" in received[0]
    assert "The beginning" in received[0]
    window.close()


def test_scene_summary_requires_confirmation_and_never_modifies_source(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="original manuscript")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    wait_until(lambda: window.project_view is not None and window.project_view.topLevelItemCount() > 0, application)
    scene_item = window.project_view.topLevelItem(0).child(0).child(0)
    window.project_view.setCurrentItem(scene_item)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args: QMessageBox.StandardButton.Yes,
    )
    received: list[str] = []
    monkeypatch.setattr(
        window.provider,
        "generate_private",
        lambda prompt, **_options: (received.append(prompt) or "A review summary."),
    )

    window.summarize_project_scene()
    wait_until(lambda: bool(window._analysis_windows), application)

    assert received and "original manuscript" in received[0]
    assert window._analysis_windows[0].output.toPlainText() == "A review summary."
    assert project.read_scene(scene.id) == "original manuscript"
    window.close()
