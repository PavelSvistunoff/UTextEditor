"""Minimal AI settings dialog for the MVP."""

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox, QPlainTextEdit, QSpinBox

from app.ai.prompts import completion_prompt
from app.settings.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Settings")
        self.settings = settings
        self.host = QLineEdit(settings.ollama_host)
        self.model = QLineEdit(settings.ollama_model)
        self.role = QPlainTextEdit(settings.ai_role)
        self.role.setPlaceholderText("Instructions that define the AI's completion role")
        self.role.setFixedHeight(70)
        self.template = QPlainTextEdit(settings.completion_template)
        self.template.setPlaceholderText("Use {context} and {language} placeholders")
        self.template.setFixedHeight(140)
        self.debounce = QSpinBox()
        self.debounce.setRange(100, 5000)
        self.debounce.setValue(settings.completion_debounce_ms)
        form = QFormLayout(self)
        form.addRow("Ollama host", self.host)
        form.addRow("Model", self.model)
        form.addRow("AI role", self.role)
        form.addRow("Context template", self.template)
        form.addRow("Debounce (ms)", self.debounce)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def accept(self) -> None:
        template = self.template.toPlainText().strip()
        if "{context}" not in template:
            QMessageBox.warning(self, "Invalid context template", "The context template must include {context}.")
            return
        try:
            completion_prompt("", "", template)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid context template", str(exc))
            return
        self.settings.ollama_host = self.host.text().strip() or self.settings.ollama_host
        self.settings.ollama_model = self.model.text().strip() or self.settings.ollama_model
        self.settings.ai_role = self.role.toPlainText().strip() or self.settings.ai_role
        self.settings.completion_template = template
        self.settings.completion_debounce_ms = self.debounce.value()
        super().accept()
