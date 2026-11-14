"""Explicit run-wide terminology choices before contextual translation."""

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout,
)
from PySide6.QtCore import Qt

from app.project.translation_context import GlossaryTerm, ambiguous_terms, validate_glossary
from app.project.model import ProjectError


class TranslationGlossaryDialog(QDialog):
    def __init__(self, terms: tuple[GlossaryTerm, ...], parent=None) -> None:
        super().__init__(parent)
        self.terms = terms
        self.setWindowTitle(self.tr("Review translation glossary"))
        self.resize(760, 480)
        layout = QVBoxLayout(self)
        message = QLabel(self.tr(
            "Edit approved translations for names and reference-note titles. Unchanged values preserve "
            "the original spelling. Ambiguous names require your review. These decisions apply to "
            "every translated item in this run; reference examples are reviewed separately."
        ), self)
        message.setWordWrap(True)
        layout.addWidget(message)
        self.table = QTableWidget(len(terms), 3, self)
        self.table.setAccessibleName(self.tr("Translation glossary"))
        self.table.setHorizontalHeaderLabels([self.tr("Source term"), self.tr("Approved translation"), self.tr("Review")])
        ambiguous = ambiguous_terms(terms)
        for row, term in enumerate(terms):
            for column, text in enumerate((term.source, term.target,
                                          self.tr("Ambiguous name") if term.source in ambiguous else "")):
                item = QTableWidgetItem(text)
                if column != 1:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, column, item)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.error = QLabel(self)
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self._approve)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def glossary(self) -> tuple[GlossaryTerm, ...]:
        return tuple(GlossaryTerm(term.source, self.table.item(row, 1).text(), term.owners)
                     for row, term in enumerate(self.terms))

    def _approve(self) -> None:
        try:
            validate_glossary(self.glossary())
        except ProjectError as exc:
            self.error.setText(str(exc))
            return
        self.accept()
