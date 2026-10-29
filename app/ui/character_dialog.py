"""Small structured editor for first-class project characters."""

from copy import deepcopy

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QPlainTextEdit,
    QTabWidget, QVBoxLayout, QWidget,
    QMessageBox,
)

from app.project.model import (
    CHARACTER_ARC_FIELDS, CHARACTER_GOAL_STATES, CHARACTER_KNOWLEDGE_KINDS,
    Character, CharacterGoal, CharacterKnowledge,
)


class CharacterDialog(QDialog):
    """Edit an author's character profile with explicit Save/Cancel controls."""

    def __init__(
        self,
        character: Character,
        relationships: list[str] | None = None,
        timeline: list[str] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Character Profile")
        self.setMinimumSize(560, 520)
        self.character = deepcopy(character)
        tabs = QTabWidget(self)
        identity = QWidget(tabs)
        identity_form = QFormLayout(identity)
        self.full_name = QLineEdit(character.full_name)
        self.display_name = QLineEdit(character.display_name)
        self.aliases = QPlainTextEdit("\n".join(character.aliases))
        self.role = QLineEdit(character.role)
        self.description = QPlainTextEdit(character.description)
        identity_form.addRow("Full name", self.full_name)
        identity_form.addRow("Display name", self.display_name)
        identity_form.addRow("Aliases (one per line)", self.aliases)
        identity_form.addRow("Role", self.role)
        identity_form.addRow("Description", self.description)
        tabs.addTab(identity, "Identity")

        story = QWidget(tabs)
        story_form = QFormLayout(story)
        self.motivation = QPlainTextEdit(character.primary_motivation)
        self.goals = QPlainTextEdit("\n".join(f"{g.description} | {g.status} | {g.priority} | {g.notes}".rstrip(" | ") for g in character.goals))
        self.goals.setToolTip("One goal per line: description | active/completed/abandoned/blocked | priority 1–5 | notes")
        self.traits = QPlainTextEdit("\n".join(character.personality.get("traits", [])))
        self.knowledge = QPlainTextEdit("\n".join(f"{k.kind}: {k.statement}" for k in character.knowledge))
        self.arc = QPlainTextEdit("\n".join(f"{k}: {v}" for k, v in character.arc.items()))
        story_form.addRow("Primary motivation", self.motivation)
        story_form.addRow("Goals (one per line)", self.goals)
        story_form.addRow("Personality traits", self.traits)
        story_form.addRow("Knowledge and secrets (kind: statement)", self.knowledge)
        story_form.addRow("Arc notes (field: value)", self.arc)
        self.secondary = QPlainTextEdit("\n".join(character.secondary_motivations))
        self.desires = QPlainTextEdit("\n".join(character.desires))
        self.needs = QPlainTextEdit("\n".join(character.needs))
        self.obstacles = QPlainTextEdit("\n".join(character.obstacles))
        self.accepted_risks = QPlainTextEdit("\n".join(character.accepted_risks))
        self.refusals = QPlainTextEdit("\n".join(character.refusals))
        self.conflicts = QPlainTextEdit("\n".join(character.internal_conflicts))
        story_form.addRow("Secondary motivations", self.secondary)
        story_form.addRow("Desires", self.desires)
        story_form.addRow("Needs", self.needs)
        story_form.addRow("Obstacles", self.obstacles)
        story_form.addRow("Risks they accept", self.accepted_risks)
        story_form.addRow("Things they refuse to do", self.refusals)
        story_form.addRow("Internal conflicts", self.conflicts)
        tabs.addTab(story, "Story")

        context = QWidget(tabs)
        context_form = QFormLayout(context)
        self.background_fields = {}
        for field, label in (("age", "Age"), ("occupation", "Occupation"), ("origin", "Origin and culture"), ("appearance", "Appearance"), ("history", "Formative history"), ("social_status", "Status and affiliations")):
            widget = QPlainTextEdit(character.background.get(field, ""))
            self.background_fields[field] = widget
            context_form.addRow(label, widget)
        self.personality_fields = {}
        for field, label in (("strengths", "Strengths"), ("weaknesses", "Weaknesses"), ("fears", "Fears"), ("values", "Values and beliefs"), ("habits", "Habits"), ("emotional_triggers", "Emotional triggers"), ("contradictions", "Contradictions"), ("speech_patterns", "Speech patterns"), ("attitudes", "Attitudes")):
            widget = QPlainTextEdit("\n".join(character.personality.get(field, [])))
            self.personality_fields[field] = widget
            context_form.addRow(label, widget)
        tabs.addTab(context, "Background and personality")

        relation_page = QPlainTextEdit("\n".join(relationships or ()))
        relation_page.setReadOnly(True)
        tabs.addTab(relation_page, "Relationships")
        timeline_page = QPlainTextEdit("\n".join(timeline or ()))
        timeline_page.setReadOnly(True)
        tabs.addTab(timeline_page, "Scene development")
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    def _accept(self) -> None:
        name = self.full_name.text().strip()
        if not name:
            self.full_name.setFocus()
            return
        self.character.full_name = name
        self.character.display_name = self.display_name.text().strip()
        self.character.aliases = _lines(self.aliases.toPlainText())
        self.character.role = self.role.text().strip() or "supporting character"
        self.character.description = self.description.toPlainText().strip()
        self.character.primary_motivation = self.motivation.toPlainText().strip()
        self.character.secondary_motivations = _lines(self.secondary.toPlainText())
        self.character.desires = _lines(self.desires.toPlainText())
        self.character.needs = _lines(self.needs.toPlainText())
        self.character.obstacles = _lines(self.obstacles.toPlainText())
        self.character.accepted_risks = _lines(self.accepted_risks.toPlainText())
        self.character.refusals = _lines(self.refusals.toPlainText())
        self.character.internal_conflicts = _lines(self.conflicts.toPlainText())
        self.character.background = {key: widget.toPlainText().strip() for key, widget in self.background_fields.items() if widget.toPlainText().strip()}
        self.character.personality = {
            key: values
            for key, widget in self.personality_fields.items()
            if (values := _lines(widget.toPlainText()))
        }
        self.character.goals = []
        for line in _lines(self.goals.toPlainText()):
            parts = [part.strip() for part in line.split("|", 3)]
            status = parts[1] if len(parts) > 1 and parts[1] else "active"
            try:
                priority = int(parts[2]) if len(parts) > 2 and parts[2] else 3
            except ValueError:
                priority = 0
            if status not in CHARACTER_GOAL_STATES or not 1 <= priority <= 5:
                QMessageBox.warning(self, "Invalid goal", "Use a supported goal status and a priority from 1 to 5.")
                self.goals.setFocus()
                return
            notes = parts[3] if len(parts) > 3 else ""
            self.character.goals.append(CharacterGoal(parts[0], status, priority, notes))
        self.character.personality["traits"] = _lines(self.traits.toPlainText())
        self.character.knowledge = []
        for line in _lines(self.knowledge.toPlainText()):
            kind, separator, statement = line.partition(":")
            if not separator or kind.strip() not in CHARACTER_KNOWLEDGE_KINDS or not statement.strip():
                QMessageBox.warning(self, "Invalid knowledge entry", "Use a supported category followed by ': ' and a statement.")
                self.knowledge.setFocus()
                return
            self.character.knowledge.append(CharacterKnowledge(kind.strip(), statement.strip()))
        self.character.arc = {}
        for line in _lines(self.arc.toPlainText()):
            field, separator, value = line.partition(":")
            if not separator or field.strip() not in CHARACTER_ARC_FIELDS or not value.strip():
                QMessageBox.warning(self, "Invalid arc note", "Use a supported arc field followed by ': ' and a value.")
                self.arc.setFocus()
                return
            self.character.arc[field.strip()] = value.strip()
        self.accept()


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]
