"""Title-page and paper options for compiling a book."""

from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout


class PdfOptionsDialog(QDialog):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Book PDF options"))
        self.title = QLineEdit(title, self)
        self.author = QLineEdit(self)
        self.page_size = QComboBox(self)
        self.page_size.addItems(["A5", "A4", "Letter"])
        self.scene_headings = QCheckBox(self.tr("Include scene headings"), self)
        self.scene_headings.setChecked(True)
        form = QFormLayout()
        form.addRow(self.tr("Title"), self.title)
        form.addRow(self.tr("Author"), self.author)
        form.addRow(self.tr("Page size"), self.page_size)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("OK"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.title.textChanged.connect(lambda text: buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(text.strip())))
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(title.strip()))
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.scene_headings)
        layout.addWidget(buttons)
