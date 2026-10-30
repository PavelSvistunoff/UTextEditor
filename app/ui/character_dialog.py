"""Small structured editor for first-class project characters."""

from copy import deepcopy
from uuid import uuid4

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QPlainTextEdit,
    QTabWidget, QVBoxLayout, QWidget,
    QMessageBox, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QInputDialog,
)
from PySide6.QtCore import Qt, Signal

from app.project.model import (
    CHARACTER_ARC_FIELDS, CHARACTER_GOAL_STATES, CHARACTER_KNOWLEDGE_KINDS,
    Character, CharacterGoal, CharacterKnowledge, CharacterRelationship,
)
from .character_relationship_dialog import CharacterRelationshipDialog


class CharacterDialog(QDialog):
    """Edit an author's character profile with explicit Save/Cancel controls."""
    fill_requested = Signal()

    def __init__(
        self,
        character: Character,
        timeline: list[str] | None = None,
        parent=None,
        *,
        project_characters: list[Character] | None = None,
        project_relationships: list[CharacterRelationship] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Character Profile"))
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
        identity_form.addRow(self.tr("Full name"), self.full_name)
        identity_form.addRow(self.tr("Display name"), self.display_name)
        identity_form.addRow(self.tr("Aliases (one per line)"), self.aliases)
        identity_form.addRow(self.tr("Role"), self.role)
        identity_form.addRow(self.tr("Description"), self.description)
        tabs.addTab(identity, self.tr("Identity"))

        story = QWidget(tabs)
        story_form = QFormLayout(story)
        self.motivation = QPlainTextEdit(character.primary_motivation)
        self.goals = QPlainTextEdit("\n".join(f"{g.description} | {g.status} | {g.priority} | {g.notes}".rstrip(" | ") for g in character.goals))
        self.goals.setToolTip(self.tr("One goal per line: description | active/completed/abandoned/blocked | priority 1–5 | notes"))
        self.traits = QPlainTextEdit("\n".join(character.personality.get("traits", [])))
        self.knowledge = QPlainTextEdit("\n".join(f"{k.kind}: {k.statement}" for k in character.knowledge))
        self.arc = QPlainTextEdit("\n".join(f"{k}: {v}" for k, v in character.arc.items()))
        story_form.addRow(self.tr("Primary motivation"), self.motivation)
        story_form.addRow(self.tr("Goals (one per line)"), self.goals)
        story_form.addRow(self.tr("Personality traits"), self.traits)
        story_form.addRow(self.tr("Knowledge and secrets (kind: statement)"), self.knowledge)
        story_form.addRow(self.tr("Arc notes (field: value)"), self.arc)
        self.secondary = QPlainTextEdit("\n".join(character.secondary_motivations))
        self.desires = QPlainTextEdit("\n".join(character.desires))
        self.needs = QPlainTextEdit("\n".join(character.needs))
        self.obstacles = QPlainTextEdit("\n".join(character.obstacles))
        self.accepted_risks = QPlainTextEdit("\n".join(character.accepted_risks))
        self.refusals = QPlainTextEdit("\n".join(character.refusals))
        self.conflicts = QPlainTextEdit("\n".join(character.internal_conflicts))
        story_form.addRow(self.tr("Secondary motivations"), self.secondary)
        story_form.addRow(self.tr("Desires"), self.desires)
        story_form.addRow(self.tr("Needs"), self.needs)
        story_form.addRow(self.tr("Obstacles"), self.obstacles)
        story_form.addRow(self.tr("Risks they accept"), self.accepted_risks)
        story_form.addRow(self.tr("Things they refuse to do"), self.refusals)
        story_form.addRow(self.tr("Internal conflicts"), self.conflicts)
        tabs.addTab(story, self.tr("Story"))

        context = QWidget(tabs)
        context_form = QFormLayout(context)
        self.background_fields = {}
        labels = {
            "Age": self.tr("Age"), "Occupation": self.tr("Occupation"),
            "Origin and culture": self.tr("Origin and culture"),
            "Appearance": self.tr("Appearance"), "Formative history": self.tr("Formative history"),
            "Status and affiliations": self.tr("Status and affiliations"),
            "Strengths": self.tr("Strengths"), "Weaknesses": self.tr("Weaknesses"),
            "Fears": self.tr("Fears"), "Values and beliefs": self.tr("Values and beliefs"),
            "Habits": self.tr("Habits"), "Emotional triggers": self.tr("Emotional triggers"),
            "Contradictions": self.tr("Contradictions"), "Speech patterns": self.tr("Speech patterns"),
            "Attitudes": self.tr("Attitudes"),
        }
        for field, label in (("age", "Age"), ("occupation", "Occupation"), ("origin", "Origin and culture"), ("appearance", "Appearance"), ("history", "Formative history"), ("social_status", "Status and affiliations")):
            widget = QPlainTextEdit(character.background.get(field, ""))
            self.background_fields[field] = widget
            context_form.addRow(labels[label], widget)
        self.personality_fields = {}
        for field, label in (("strengths", "Strengths"), ("weaknesses", "Weaknesses"), ("fears", "Fears"), ("values", "Values and beliefs"), ("habits", "Habits"), ("emotional_triggers", "Emotional triggers"), ("contradictions", "Contradictions"), ("speech_patterns", "Speech patterns"), ("attitudes", "Attitudes")):
            widget = QPlainTextEdit("\n".join(character.personality.get(field, [])))
            self.personality_fields[field] = widget
            context_form.addRow(labels[label], widget)
        tabs.addTab(context, self.tr("Background and personality"))

        self.project_characters = {item.id: deepcopy(item) for item in (project_characters or [])}
        self.relationships = deepcopy(project_relationships or [])
        relation_page = QWidget(tabs)
        relation_layout = QVBoxLayout(relation_page)
        self.relationship_list = QListWidget(relation_page)
        self.relationship_list.setAccessibleName(self.tr("Relationships"))
        relation_layout.addWidget(self.relationship_list)
        controls = QHBoxLayout()
        self.add_relationship_button = QPushButton(self.tr("Add Relationship…"))
        self.edit_relationship_button = QPushButton(self.tr("Edit Relationship…"))
        self.remove_relationship_button = QPushButton(self.tr("Remove Relationship"))
        for button in (self.add_relationship_button, self.edit_relationship_button, self.remove_relationship_button):
            controls.addWidget(button)
        relation_layout.addLayout(controls)
        self.add_relationship_button.clicked.connect(self._add_relationship)
        self.edit_relationship_button.clicked.connect(self._edit_relationship)
        self.remove_relationship_button.clicked.connect(self._remove_relationship)
        self.relationship_list.itemDoubleClicked.connect(lambda _: self._edit_relationship())
        self.relationship_list.currentRowChanged.connect(self._update_relationship_buttons)
        self._refresh_relationships()
        tabs.addTab(relation_page, self.tr("Relationships"))
        timeline_page = QPlainTextEdit("\n".join(timeline or ()))
        timeline_page.setReadOnly(True)
        tabs.addTab(timeline_page, self.tr("Scene development"))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(self.tr("Save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        self.ai_button = QPushButton(self.tr("Fill Empty Fields with AI…"), self)
        self.ai_button.clicked.connect(self.fill_requested.emit)
        layout.addWidget(self.ai_button)
        layout.addWidget(buttons)

    def profile_fields(self) -> dict[str, str]:
        return {key: (widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText())
                for key, widget in self._profile_widgets().items()}

    def _profile_widgets(self) -> dict:
        return {
            "full_name": self.full_name, "display_name": self.display_name, "aliases": self.aliases,
            "role": self.role, "description": self.description, "primary_motivation": self.motivation,
            "goals": self.goals, "traits": self.traits, "knowledge": self.knowledge, "arc": self.arc,
            "secondary_motivations": self.secondary, "desires": self.desires, "needs": self.needs,
            "obstacles": self.obstacles, "accepted_risks": self.accepted_risks, "refusals": self.refusals,
            "internal_conflicts": self.conflicts,
            **{f"background_{key}": widget for key, widget in self.background_fields.items()},
            **{f"personality_{key}": widget for key, widget in self.personality_fields.items()},
        }

    def apply_profile_suggestions(self, suggestions: dict[str, str]) -> None:
        for key, value in suggestions.items():
            widget = self._profile_widgets()[key]
            if isinstance(widget, QLineEdit):
                if not widget.text().strip():
                    widget.setText(value)
            elif not widget.toPlainText().strip():
                widget.setPlainText(value)

    def _refresh_relationships(self) -> None:
        self.relationship_list.clear()
        for relation in self.relationships:
            other_id = relation.target_id if relation.source_id == self.character.id else relation.source_id
            other = self.project_characters.get(other_id)
            name = (other.display_name or other.full_name) if other else other_id
            arrow = "→" if relation.source_id == self.character.id else "←"
            item = QListWidgetItem(f"{arrow} {name}: {relation.relationship_type} — {relation.description}")
            item.setData(Qt.ItemDataRole.UserRole, relation.id)
            self.relationship_list.addItem(item)
        self._update_relationship_buttons()

    def _update_relationship_buttons(self, *_args) -> None:
        selected = self.relationship_list.currentItem() is not None
        self.add_relationship_button.setEnabled(any(key != self.character.id for key in self.project_characters))
        self.edit_relationship_button.setEnabled(selected)
        self.remove_relationship_button.setEnabled(selected)

    def _selected_relationship(self):
        item = self.relationship_list.currentItem()
        return next((relation for relation in self.relationships if item and relation.id == item.data(Qt.ItemDataRole.UserRole)), None)

    def _add_relationship(self) -> None:
        choices = {f"{c.display_name or c.full_name} — {c.role} [{c.id}]": c for c in self.project_characters.values() if c.id != self.character.id}
        if not choices:
            return
        label, accepted = QInputDialog.getItem(self, self.tr("Character relationship"), self.tr("Related character:"), list(choices), 0, False)
        if not accepted or label not in choices:
            return
        dialog = CharacterRelationshipDialog(CharacterRelationship(str(uuid4()), self.character.id, choices[label].id), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.relationships.append(dialog.relationship)
            self._refresh_relationships()

    def _edit_relationship(self) -> None:
        relation = self._selected_relationship()
        if relation is None:
            return
        dialog = CharacterRelationshipDialog(relation, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.relationships[self.relationships.index(relation)] = dialog.relationship
            self._refresh_relationships()

    def _remove_relationship(self) -> None:
        relation = self._selected_relationship()
        if relation is not None and QMessageBox.question(self, self.tr("Remove relationship"), self.tr("Remove this directed relationship?")) == QMessageBox.StandardButton.Yes:
            self.relationships.remove(relation)
            self._refresh_relationships()

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
                QMessageBox.warning(self, self.tr("Invalid goal"), self.tr("Use a supported goal status and a priority from 1 to 5."))
                self.goals.setFocus()
                return
            notes = parts[3] if len(parts) > 3 else ""
            self.character.goals.append(CharacterGoal(parts[0], status, priority, notes))
        self.character.personality["traits"] = _lines(self.traits.toPlainText())
        self.character.knowledge = []
        for line in _lines(self.knowledge.toPlainText()):
            kind, separator, statement = line.partition(":")
            if not separator or kind.strip() not in CHARACTER_KNOWLEDGE_KINDS or not statement.strip():
                QMessageBox.warning(self, self.tr("Invalid knowledge entry"), self.tr("Use a supported category followed by ': ' and a statement."))
                self.knowledge.setFocus()
                return
            self.character.knowledge.append(CharacterKnowledge(kind.strip(), statement.strip()))
        self.character.arc = {}
        for line in _lines(self.arc.toPlainText()):
            field, separator, value = line.partition(":")
            if not separator or field.strip() not in CHARACTER_ARC_FIELDS or not value.strip():
                QMessageBox.warning(self, self.tr("Invalid arc note"), self.tr("Use a supported arc field followed by ': ' and a value."))
                self.arc.setFocus()
                return
            self.character.arc[field.strip()] = value.strip()
        self.accept()


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]
