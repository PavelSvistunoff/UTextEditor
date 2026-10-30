"""Minimal AI settings dialog for the MVP."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFontComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from urllib.parse import urlsplit

from app.ai.prompts import completion_prompt
from app.settings.settings import AppSettings
from app.ui.font_utils import editor_font
from app.i18n import format_qt


class SettingsDialog(QDialog):
    connection_test_requested = Signal(str, str)

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("AI Settings"))
        self.resize(640, 600)
        self.settings = settings
        # Connection
        self.host = QLineEdit(settings.ollama_host)
        self.model = QLineEdit(settings.ollama_model)
        # Role and template
        self.role = QPlainTextEdit(settings.ai_role)
        self.role.setPlaceholderText(self.tr("Instructions that define the AI's completion role"))
        self.role.setFixedHeight(70)
        self.template = QPlainTextEdit(settings.completion_template)
        self.template.setPlaceholderText(self.tr("Use {context} and {language} placeholders"))
        self.template.setFixedHeight(140)
        # Completion settings
        self.completion_enabled = QCheckBox(self.tr("Enable completion"))
        self.completion_enabled.setChecked(settings.completion_enabled)
        self.automatic_project_context = QCheckBox(self.tr("Include project context in automatic completions"))
        self.automatic_project_context.setChecked(settings.automatic_project_context)
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
        self.spellcheck_enabled = QCheckBox(self.tr("Enable spellchecking"))
        self.spellcheck_enabled.setChecked(settings.spellcheck_enabled)
        self.automatic_spellcheck = QCheckBox(self.tr("Automatic spellcheck"))
        self.automatic_spellcheck.setChecked(settings.automatic_spellcheck)
        # Language selection
        self.language = QComboBox()
        self.language.addItem(self.tr("Automatic"), "Auto")
        self.language.addItem("English", "English")
        self.language.addItem("Українська", "Ukrainian")
        self.language.setCurrentIndex(max(0, self.language.findData(settings.language)))
        self.ui_language = QComboBox()
        self.ui_language.addItem(self.tr("System default"), "system")
        self.ui_language.addItem("English", "en")
        self.ui_language.addItem("Українська", "uk")
        self.ui_language.setCurrentIndex(max(0, self.ui_language.findData(settings.ui_language)))
        # Editor appearance settings
        self.font_family = QFontComboBox()
        self.font_family.setCurrentFont(
            editor_font(settings.font_family, settings.font_size)
        )
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 32)
        self.font_size.setValue(settings.font_size)
        self.tab_width = QSpinBox()
        self.tab_width.setRange(2, 8)
        self.tab_width.setValue(settings.tab_width)
        self.word_wrap = QCheckBox(self.tr("Wrap long lines"))
        self.word_wrap.setChecked(settings.word_wrap)
        self.line_numbers = QCheckBox(self.tr("Show line numbers"))
        self.line_numbers.setChecked(settings.line_numbers)
        self.autosave_enabled = QCheckBox(self.tr("Automatically save project scenes and notes"))
        self.autosave_enabled.setChecked(settings.autosave_enabled)
        self.autosave_idle = QSpinBox()
        self.autosave_idle.setRange(250, 60000)
        self.autosave_idle.setSingleStep(250)
        self.autosave_idle.setValue(settings.autosave_idle_ms)

        tabs = QTabWidget(self)
        connection_tab = QWidget(tabs)
        connection_form = QFormLayout(connection_tab)
        connection_form.addRow(self.tr("Ollama host"), self.host)
        connection_form.addRow(
            QLabel(self.tr("Text used for AI requests is sent to this configured Ollama host."))
        )
        connection_form.addRow(self.tr("Model"), self.model)
        self.test_connection_button = QPushButton(self.tr("Test connection"), connection_tab)
        self.test_connection_button.clicked.connect(self._request_connection_test)
        self.connection_status = QLabel(connection_tab)
        connection_form.addRow(self.test_connection_button, self.connection_status)
        connection_form.addRow(self.autosave_enabled)
        connection_form.addRow(self.tr("Autosave after idle (ms)"), self.autosave_idle)
        tabs.addTab(connection_tab, self.tr("Connection"))

        writing_tab = QWidget(tabs)
        writing_form = QFormLayout(writing_tab)
        writing_form.addRow(self.tr("Writing language"), self.language)
        writing_form.addRow(self.tr("Interface language"), self.ui_language)
        writing_form.addRow(QLabel(self.tr("Interface language changes take effect after restart.")))
        writing_form.addRow(self.tr("Font"), self.font_family)
        writing_form.addRow(self.tr("Font size"), self.font_size)
        writing_form.addRow(self.tr("Tab width"), self.tab_width)
        writing_form.addRow(self.word_wrap)
        writing_form.addRow(self.line_numbers)
        tabs.addTab(writing_tab, self.tr("Writing"))

        assistance_tab = QWidget(tabs)
        assistance_form = QFormLayout(assistance_tab)
        assistance_form.addRow(self.completion_enabled)
        assistance_form.addRow(self.automatic_project_context)
        assistance_form.addRow(self.tr("Completion delay (ms)"), self.debounce)
        assistance_form.addRow(self.tr("Maximum suggestion length"), self.max_length)
        assistance_form.addRow(self.tr("Temperature"), self.temperature)
        assistance_form.addRow(self.tr("Context size (chars)"), self.context_size)
        assistance_form.addRow(self.spellcheck_enabled)
        assistance_form.addRow(self.automatic_spellcheck)
        tabs.addTab(assistance_tab, self.tr("AI assistance"))

        prompts_tab = QWidget(tabs)
        prompts_form = QFormLayout(prompts_tab)
        prompts_form.addRow(
            QLabel(self.tr("Advanced prompt instructions. Most users can leave these unchanged."))
        )
        prompts_form.addRow(self.tr("AI role"), self.role)
        prompts_form.addRow(self.tr("Context template"), self.template)
        tabs.addTab(prompts_tab, self.tr("Advanced prompts"))

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("OK"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        self.reset_button = buttons.addButton(
            self.tr("Reset to defaults"), QDialogButtonBox.ButtonRole.ResetRole
        )
        self.reset_button.clicked.connect(self._reset_to_defaults)
        layout.addWidget(buttons)

    def _request_connection_test(self) -> None:
        host = self.host.text().strip()
        model = self.model.text().strip()
        if not host or not model:
            self.connection_status.setText(self.tr("Enter both a host and model."))
            return
        self.connection_status.setText(self.tr("Testing model connection…"))
        self.connection_test_requested.emit(host, model)

    def set_connection_test_result(self, available: bool, model: str) -> None:
        if available:
            self.connection_status.setText(
                format_qt(self.tr("Connected; model “%1” is available."), model)
            )
        else:
            self.connection_status.setText(
                format_qt(
                    self.tr(
                        "Could not connect or find “%1”. Check Ollama is running and run `ollama pull %1` if needed."
                    ),
                    model,
                )
            )

    def _reset_to_defaults(self) -> None:
        defaults = AppSettings()
        self.host.setText(defaults.ollama_host)
        self.model.setText(defaults.ollama_model)
        self.role.setPlainText(defaults.ai_role)
        self.template.setPlainText(defaults.completion_template)
        self.completion_enabled.setChecked(defaults.completion_enabled)
        self.automatic_project_context.setChecked(defaults.automatic_project_context)
        self.debounce.setValue(defaults.completion_debounce_ms)
        self.max_length.setValue(defaults.maximum_suggestion_length)
        self.temperature.setValue(defaults.temperature)
        self.context_size.setValue(defaults.context_size)
        self.spellcheck_enabled.setChecked(defaults.spellcheck_enabled)
        self.automatic_spellcheck.setChecked(defaults.automatic_spellcheck)
        self.language.setCurrentIndex(self.language.findData(defaults.language))
        self.ui_language.setCurrentIndex(self.ui_language.findData(defaults.ui_language))
        self.font_family.setCurrentFont(
            editor_font(defaults.font_family, defaults.font_size)
        )
        self.font_size.setValue(defaults.font_size)
        self.tab_width.setValue(defaults.tab_width)
        self.word_wrap.setChecked(defaults.word_wrap)
        self.line_numbers.setChecked(defaults.line_numbers)
        self.autosave_enabled.setChecked(defaults.autosave_enabled)
        self.autosave_idle.setValue(defaults.autosave_idle_ms)
        self.connection_status.clear()

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
        self.settings.automatic_project_context = bool(self.automatic_project_context.isChecked())
        self.settings.spellcheck_enabled = bool(self.spellcheck_enabled.isChecked())
        self.settings.automatic_spellcheck = bool(self.automatic_spellcheck.isChecked())
        self.settings.language = self.language.currentData()
        self.settings.ui_language = self.ui_language.currentData()
        self.settings.font_family = self.font_family.currentFont().family()
        self.settings.font_size = int(self.font_size.value())
        self.settings.tab_width = int(self.tab_width.value())
        self.settings.word_wrap = bool(self.word_wrap.isChecked())
        self.settings.line_numbers = bool(self.line_numbers.isChecked())
        self.settings.autosave_enabled = bool(self.autosave_enabled.isChecked())
        self.settings.autosave_idle_ms = int(self.autosave_idle.value())
        super().accept()
