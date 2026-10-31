from pathlib import Path

from tools.audit_ui_strings import audit_source, main


def test_audit_reports_unmarked_ui_literals_and_fstrings():
    source = '''
QMessageBox.warning(self, "Save failed", f"Could not save {path}")
QInputDialog.getText(self, "New scene", "Title:")
button = QPushButton("Open")
status.showMessage(f"Saved to {path}")
QFileDialog.getOpenFileName(self, "Open file", "", "Text (*.txt)")
label.setText(self.tr("Translated"))
label.setText(value)
other("Not a recognized UI call")
'''
    findings = audit_source(source, Path("example.py"))
    assert len(findings) == 8
    assert any("Save failed" in item for item in findings)
    assert any("Could not save" in item for item in findings)
    assert any("New scene" in item for item in findings)
    assert any("Open" in item for item in findings)
    assert any("Saved to" in item for item in findings)
    assert any("Text (*.txt)" in item for item in findings)
    assert all("Translated" not in item and "Not a recognized" not in item for item in findings)


def test_audit_cli_can_fail_on_findings_and_reports_parse_errors(tmp_path, capsys):
    source = tmp_path / "window.py"
    source.write_text('button.setText("Hello")\n', encoding="utf-8")
    assert main([str(source)]) == 0
    assert main([str(source), "--fail-on-findings"]) == 1
    source.write_text("def broken(\n", encoding="utf-8")
    assert main([str(source)]) == 2
    assert "audit failed" in capsys.readouterr().err


def test_audit_covers_tabs_items_and_dialog_details():
    source = '''
tabs.addTab(page, "Details")
tabs.addTab(page, icon, "Advanced")
tabs.setTabText(0, "General")
combo.addItem("English")
combo.setItemText(0, "Other")
dialog.setInformativeText("Details")
dialog.setCancelButtonText("Stop")
tabs.addTab(page, self.tr("Translated"))
'''
    findings = audit_source(source, Path("example.py"))
    assert len(findings) == 7
    assert all("Translated" not in item for item in findings)
