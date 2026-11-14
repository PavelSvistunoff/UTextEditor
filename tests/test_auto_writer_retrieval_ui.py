"""Worker/Qt reviews for Auto-writer RAG; native gate is explicitly separate."""

import os
from threading import Event, get_ident
from time import monotonic
from unittest.mock import patch

import pytest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QThreadPool, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QPushButton, QDialogButtonBox

from app.project import Project
from app.project.rag_index import LexicalIndex, fts5_available
from app.project.rag_sources import capture_project_sources
from app.settings.settings import AppSettings
from app.ui.auto_writer_dialog import AutoWriterDialog
from app.ui.auto_writer_review_dialog import AutoWriterReviewDialog
from app.ui.main_window import MainWindow
from app.ui.rag_completion import RAGCompletionDialog


@pytest.fixture(scope='module')
def application(): return QApplication.instance() or QApplication([])


def wait(predicate,application):
    deadline=monotonic()+8
    while not predicate():
        application.processEvents()
        assert monotonic()<deadline,'Auto-writer UI did not finish'
        QTest.qWait(5)


@pytest.fixture
def writer(application,tmp_path,monkeypatch):
    if not fts5_available(): pytest.skip('SQLite FTS5 unavailable')
    monkeypatch.setattr(AppSettings,'_default_settings_path',staticmethod(lambda:tmp_path/'cache/settings.yaml'))
    project=Project.create(tmp_path/'project','Novel')
    chapter=project.add_chapter('Chapter')
    far=project.add_scene('Archive',chapter_id=chapter.id,content='The silver compass is hidden in an old oak tree.')
    project.add_scene('Interlude',chapter_id=chapter.id,content='They walked in silence.')
    target=project.add_scene('Find the silver compass',chapter_id=chapter.id)
    with patch('app.ui.main_window.OllamaClient.check_connection',return_value=True): window=MainWindow()
    window.settings.completion_enabled=False;window.settings.automatic_spellcheck=False
    window.settings.ollama_context_length=32768;window.settings.ai_enabled=True
    window.settings.autosave_enabled=False
    window._project_opened(project)
    window._open_project_document('scene',target.id)
    wait(lambda:any(item.item_id==target.id for item in window._project_documents.values()),application)
    monkeypatch.setattr(window,'_ensure_ai_context_consent',lambda **kw:True)
    monkeypatch.setattr(QMessageBox,'question',lambda *a:QMessageBox.StandardButton.Yes)
    LexicalIndex(tmp_path/'cache',project.root,project.manifest.project_id).refresh(capture_project_sources(project))
    yield window,project,far,target
    window.cancel_auto_writer()
    QThreadPool.globalInstance().waitForDone(5000)
    application.processEvents()
    for i in range(window.tabs.count()): window.tabs.widget(i).document_state.mark_saved()
    window.close()


def enable_options(monkeypatch):
    def options(dialog):
        dialog.retrieval.setChecked(True)
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(AutoWriterDialog,'exec',options)


def test_capture_review_send_and_final_evidence_use_gui_thread_and_apply_only_after_review(writer,monkeypatch,application):
    window,project,far,target=writer
    enable_options(monkeypatch)
    gui=get_ident();reviews=[];prompts=[]
    def review(dialog):
        assert get_ident()==gui
        reviews.append(dialog.context.toPlainText())
        assert 'silver compass' in reviews[0] and project.read_scene(target.id)==''
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(RAGCompletionDialog,'exec',review)
    def generate(prompt,**kw):
        assert get_ident()!=gui
        prompts.append(prompt)
        return 'The silver compass glimmered beneath the oak.'
    monkeypatch.setattr(window.provider,'generate_private',generate)
    def final_review(dialog):
        assert get_ident()==gui and project.read_scene(target.id)==''
        assert dialog.sources is not None and far.id in dialog.sources.toPlainText()
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(AutoWriterReviewDialog,'exec',final_review)
    window.start_auto_writer()
    wait(lambda:not window._project_busy,application)
    assert prompts[0]==reviews[0].split('\n\n--- SOURCE MANIFEST')[0]
    assert project.read_scene(target.id)=='The silver compass glimmered beneath the oak.'


@pytest.mark.parametrize('action',['cancel','buffer','settings','project'])
def test_context_review_cancel_or_stale_state_never_dispatches_generation(writer,monkeypatch,application,action):
    window,project,far,target=writer
    enable_options(monkeypatch)
    def review(dialog):
        if action=='buffer': window.tabs.current_editor().insertPlainText('Changed author text')
        elif action=='settings': window._settings_generation+=1
        elif action=='project': window._project_generation+=1
        return QDialog.DialogCode.Rejected if action=='cancel' else QDialog.DialogCode.Accepted
    monkeypatch.setattr(RAGCompletionDialog,'exec',review)
    monkeypatch.setattr(window.provider,'generate_private',lambda *a,**kw:pytest.fail('Stale/cancelled request dispatched'))
    window.start_auto_writer()
    wait(lambda:not window._project_busy,application)
    assert project.read_scene(target.id)==''


@pytest.mark.skipif(os.environ.get('QT_QPA_PLATFORM')!='cocoa',reason='Direct macOS Cocoa native walkthrough only')
def test_native_auto_writer_options_source_review_cancel_rebuild_and_apply(writer,monkeypatch,application):
    window,project,far,target=writer
    window.show();window.activateWindow()
    errors=[];source_visits=[];generated=[];final=[]
    original_options=AutoWriterDialog.exec
    def options(dialog):
        def keys():
            try:
                dialog.retrieval.setFocus();QTest.keyClick(dialog.retrieval,Qt.Key.Key_Space)
                assert dialog.retrieval.isChecked()
                QTest.keyClick(dialog,Qt.Key.Key_Return)
            except BaseException as exc: errors.append(exc);dialog.reject()
        QTimer.singleShot(50,keys)
        return original_options(dialog)
    monkeypatch.setattr(AutoWriterDialog,'exec',options)
    original_context=RAGCompletionDialog.exec
    def sources(dialog):
        def keys():
            try:
                source_visits.append(True)
                dialog.context.setFocus();QTest.keyClick(dialog.context,Qt.Key.Key_Tab)
                assert dialog.sources.hasFocus()
                if len(source_visits)==1:
                    QTest.keyClick(dialog,Qt.Key.Key_Escape)
                elif len(source_visits)==2:
                    QTest.keyClick(dialog.sources,Qt.Key.Key_Space)
                    assert not dialog.send_button.isEnabled()
                    # Rebuild using a real button, then send its captured version.
                    button=next(b for b in dialog.findChildren(QPushButton)
                                if b.text()=='Rebuild context')
                    button.setFocus();QTest.keyClick(button,Qt.Key.Key_Space)
                else:
                    dialog.send_button.setFocus();QTest.keyClick(dialog.send_button,Qt.Key.Key_Return)
            except BaseException as exc: errors.append(exc);dialog.reject()
        QTimer.singleShot(50,keys)
        return original_context(dialog)
    monkeypatch.setattr(RAGCompletionDialog,'exec',sources)
    monkeypatch.setattr(window.provider,'generate_private',lambda prompt,**kw:(generated.append(prompt) or 'A reviewed native draft.'))
    original_final=AutoWriterReviewDialog.exec
    def review(dialog):
        def keys():
            try:
                assert project.read_scene(target.id)==''
                assert dialog.sources is not None
                dialog.list.setFocus();QTest.keyClick(dialog.list,Qt.Key.Key_Space)
                assert not dialog.selected_ids()
                QTest.keyClick(dialog.list,Qt.Key.Key_Space)
                button=dialog.findChild(QDialogButtonBox)
                apply=button.button(button.StandardButton.Apply)
                apply.setFocus();QTest.keyClick(apply,Qt.Key.Key_Space)
                final.append(True)
            except BaseException as exc: errors.append(exc);dialog.reject()
        QTimer.singleShot(50,keys)
        return original_final(dialog)
    monkeypatch.setattr(AutoWriterReviewDialog,'exec',review)
    window.start_auto_writer()
    wait(lambda:not window._project_busy,application)
    assert not errors and not generated and project.read_scene(target.id)==''
    window.start_auto_writer()
    wait(lambda:not window._project_busy,application)
    assert not errors and len(source_visits)==3 and final
    assert project.read_scene(target.id)=='A reviewed native draft.'


def test_buffer_edit_during_generation_discards_obsolete_provider_failure(writer,monkeypatch,application):
    window,project,far,target=writer
    enable_options(monkeypatch)
    entered,release=Event(),Event();warnings=[]
    monkeypatch.setattr(RAGCompletionDialog,'exec',lambda _:QDialog.DialogCode.Accepted)
    monkeypatch.setattr(QMessageBox,'warning',lambda *args:warnings.append(args))
    def blocked(*args,**kwargs):
        entered.set();assert release.wait(5)
        raise RuntimeError('obsolete provider failure')
    monkeypatch.setattr(window.provider,'generate_private',blocked)
    window.start_auto_writer()
    try:
        wait(entered.is_set,application)
        window.tabs.current_editor().insertPlainText('New author text')
    finally: release.set()
    wait(lambda:not window._project_busy,application)
    assert not warnings
    assert window.tabs.current_editor().toPlainText()=='New author text'
    window.tabs.current_editor().undo()
    assert window.tabs.current_editor().toPlainText()==''
    assert project.read_scene(target.id)==''


def test_declined_embedding_destination_never_starts_auto_writer(writer,monkeypatch):
    window,project,far,target=writer
    def options(dialog):
        dialog.retrieval.setChecked(True);dialog.hybrid.setChecked(True)
        return QDialog.DialogCode.Accepted
    notices=[]
    def confirm(parent,title,text,*args):
        notices.append(text)
        return QMessageBox.StandardButton.No if title=='Embedding destination' else QMessageBox.StandardButton.Yes
    monkeypatch.setattr(AutoWriterDialog,'exec',options)
    monkeypatch.setattr(QMessageBox,'question',confirm)
    monkeypatch.setattr('app.ui.main_window.OllamaClient',lambda *a,**kw:pytest.fail('No embedding provider before consent'))
    window.start_auto_writer()
    assert not window._project_busy and window._auto_writer_worker is None
    assert 'provisional generated drafts' in notices[-1]
    assert project.read_scene(target.id)==''
