"""Minimal AI settings dialog for the MVP."""

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFontComboBox, QFormLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QSpinBox
from urllib.parse import urlsplit

from app.ai.prompts import completion_prompt
from app.settings.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Settings")
        self.settings = settings
        # Connection
        self.host = QLineEdit(settings.ollama_host)
        self.model = QLineEdit(settings.ollama_model)
        # Role and template
        self.role = QPlainTextEdit(settings.ai_role)
        self.role.setPlaceholderText("Instructions that define the AI's completion role")
        self.role.setFixedHeight(70)
        self.template = QPlainTextEdit(settings.completion_template)
        self.template.setPlaceholderText("Use {context} and {language} placeholders")
        self.template.setFixedHeight(140)
        # Completion settings
        from PySide6.QtWidgets import QDoubleSpinBox

        self.completion_enabled = QCheckBox("Enable completion")
        self.completion_enabled.setChecked(settings.completion_enabled)
        self.debounce = QSpinBox()
        self.debounce.setRange(100, 5000)
        self.debounce.setValue(settings.completion_debounce_ms)
        self.max_length = QSpinBox()
        self.max_length.setRange(1, 10000)
        self.max_length.setValue(settings.maximum_suggestion_length)
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.05)
        self.temperature.setValue(settings.temperature)
        self.context_size = QSpinBox()
        self.context_size.setRange(64, 65536)
        self.context_size.setValue(settings.context_size)
        # Spellcheck settings
        self.spellcheck_enabled = QCheckBox("Enable spellchecking")
        self.spellcheck_enabled.setChecked(settings.spellcheck_enabled)
        self.automatic_spellcheck = QCheckBox("Automatic spellcheck")
        self.automatic_spellcheck.setChecked(settings.automatic_spellcheck)
        # Language selection
        self.language = QComboBox()
        self.language.addItems(["Auto", "English", "Ukrainian"])
        try:
            idx = ["Auto", "English", "Ukrainian"].index(settings.language)
        except ValueError:
            idx = 0
        self.language.setCurrentIndex(idx)
        # Editor appearance settings
        self.font_family = QFontComboBox()
        self.font_family.setCurrentFont(QFont(settings.font_family))
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 32)
        self.font_size.setValue(settings.font_size)
        self.tab_width = QSpinBox()
        self.tab_width.setRange(2, 8)
        self.tab_width.setValue(settings.tab_width)
        self.word_wrap = QCheckBox("Wrap long lines")
        self.word_wrap.setChecked(settings.word_wrap)
        self.line_numbers = QCheckBox("Show line numbers")
        self.line_numbers.setChecked(settings.line_numbers)
        self.autosave_enabled = QCheckBox("Automatically save project scenes and notes")
        self.autosave_enabled.setChecked(settings.autosave_enabled)
        self.autosave_idle = QSpinBox()
        self.autosave_idle.setRange(250, 60000)
        self.autosave_idle.setSingleStep(250)
        self.autosave_idle.setValue(settings.autosave_idle_ms)

        form = QFormLayout(self)
        form.addRow("Ollama host", self.host)
        form.addRow(QLabel("Text used for AI requests is sent to this configured Ollama host."))
        form.addRow("Model", self.model)
        form.addRow(self.completion_enabled)
        form.addRow("Debounce (ms)", self.debounce)
        form.addRow("Maximum suggestion length", self.max_length)
        form.addRow("Temperature", self.temperature)
        form.addRow("Context size (chars)", self.context_size)
        form.addRow(self.spellcheck_enabled)
        form.addRow(self.automatic_spellcheck)
        form.addRow("Language", self.language)
        form.addRow("Font", self.font_family)
        form.addRow("Font size", self.font_size)
        form.addRow("Tab width", self.tab_width)
        form.addRow(self.word_wrap)
        form.addRow(self.line_numbers)
        form.addRow(self.autosave_enabled)
        form.addRow("Autosave after idle (ms)", self.autosave_idle)
        form.addRow("AI role", self.role)
        form.addRow("Context template", self.template)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def accept(self) -> None:
        template = self.template.toPlainText().strip()
        try:
            parsed_host = urlsplit(self.host.text().strip())
            valid_host = (
                parsed_host.scheme in {"http", "https"}
                and bool(parsed_host.hostname)
                and parsed_host.username is None
                and parsed_host.password is None
                and parsed_host.path in {"", "/"}
                and not parsed_host.query
                and not parsed_host.fragment
                and (parsed_host.port is None or 1 <= parsed_host.port <= 65535)
            )
        except ValueError:
            valid_host = False
        if not valid_host:
            QMessageBox.warning(self, "Invalid Ollama host", "Enter an HTTP or HTTPS host URL without credentials or a path.")
            return
        if "{context}" not in template:
            QMessageBox.warning(self, "Invalid context template", "The context template must include {context}.")
            return
        try:
            completion_prompt("", "", template)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid context template", str(exc))
            return
        # Save settings back to the AppSettings instance
        self.settings.ollama_host = self.host.text().strip() or self.settings.ollama_host
        self.settings.ollama_model = self.model.text().strip() or self.settings.ollama_model
        self.settings.ai_role = self.role.toPlainText().strip() or self.settings.ai_role
        self.settings.completion_template = template
        self.settings.completion_debounce_ms = int(self.debounce.value())
        self.settings.maximum_suggestion_length = int(self.max_length.value())
        self.settings.temperature = float(self.temperature.value())
        self.settings.context_size = int(self.context_size.value())
        self.settings.completion_enabled = bool(self.completion_enabled.isChecked())
        self.settings.spellcheck_enabled = bool(self.spellcheck_enabled.isChecked())
        self.settings.automatic_spellcheck = bool(self.automatic_spellcheck.isChecked())
        self.settings.language = self.language.currentText()
        self.settings.font_family = self.font_family.currentFont().family()
        self.settings.font_size = int(self.font_size.value())
        self.settings.tab_width = int(self.tab_width.value())
        self.settings.word_wrap = bool(self.word_wrap.isChecked())
        self.settings.line_numbers = bool(self.line_numbers.isChecked())
        self.settings.autosave_enabled = bool(self.autosave_enabled.isChecked())
        self.settings.autosave_idle_ms = int(self.autosave_idle.value())
        super().accept()
