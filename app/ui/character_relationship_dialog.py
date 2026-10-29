"""Editor for one directed character relationship."""

from copy import deepcopy

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from app.project.model import CharacterRelationship


class CharacterRelationshipDialog(QDialog):
    def __init__(self, relationship: CharacterRelationship, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Character Relationship"))
        self.relationship = deepcopy(relationship)
        form = QFormLayout()
        self.relationship_type = QLineEdit(relationship.relationship_type)
        self.attitude = QLineEdit(relationship.attitude)
        self.trust = QLineEdit("" if relationship.trust is None else str(relationship.trust))
        self.trust.setPlaceholderText(self.tr("Optional, 0–100"))
        self.status = QLineEdit(relationship.status)
        self.description = QPlainTextEdit(relationship.description)
        self.history = QPlainTextEdit(relationship.history)
        self.shared_secrets = QPlainTextEdit(relationship.shared_secrets)
        self.development_notes = QPlainTextEdit(relationship.development_notes)
        form.addRow(self.tr("Relationship type"), self.relationship_type)
        form.addRow(self.tr("Description"), self.description)
        form.addRow(self.tr("Emotional attitude"), self.attitude)
        form.addRow(self.tr("Trust (0–100)"), self.trust)
        form.addRow(self.tr("Status"), self.status)
        form.addRow(self.tr("Relevant history"), self.history)
        form.addRow(self.tr("Shared secrets or conflicts"), self.shared_secrets)
        form.addRow(self.tr("Development notes"), self.development_notes)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(self.tr("Save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _accept(self) -> None:
        relationship_type = self.relationship_type.text().strip()
        if not relationship_type:
            QMessageBox.warning(self, self.tr("Invalid relationship"), self.tr("Relationship type cannot be empty."))
            self.relationship_type.setFocus()
            return
        trust_text = self.trust.text().strip()
        try:
            trust = int(trust_text) if trust_text else None
        except ValueError:
            trust = -1
        if trust is not None and not 0 <= trust <= 100:
            QMessageBox.warning(self, self.tr("Invalid trust"), self.tr("Trust must be empty or a number from 0 to 100."))
            self.trust.setFocus()
            return
        self.relationship.relationship_type = relationship_type
        self.relationship.description = self.description.toPlainText().strip()
        self.relationship.attitude = self.attitude.text().strip()
        self.relationship.trust = trust
        self.relationship.status = self.status.text().strip() or "active"
        self.relationship.history = self.history.toPlainText().strip()
        self.relationship.shared_secrets = self.shared_secrets.toPlainText().strip()
        self.relationship.development_notes = self.development_notes.toPlainText().strip()
        self.accept()
