"""Non-editing review panel for local project-analysis responses."""

from PySide6.QtWidgets import QDialog, QLabel, QPlainTextEdit, QVBoxLayout


class AnalysisWindow(QDialog):
    def __init__(self, title: str, sources: str, result: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(720, 520)
        self.sources = QLabel(sources, self)
        self.sources.setWordWrap(True)
        self.output = QPlainTextEdit(self)
        self.output.setReadOnly(True)
        self.output.setPlainText(result)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Model output is untrusted analysis; it has not changed any document."), self))
        layout.addWidget(self.sources)
        layout.addWidget(self.output)
