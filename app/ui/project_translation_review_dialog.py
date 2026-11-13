"""Side-by-side review of a complete project translation."""

from app.project.character_translation import CharacterTextField

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QPlainTextEdit, QVBoxLayout


class ProjectTranslationReviewDialog(QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Review project translation"))
        self.resize(900, 600)
        self.items = tuple(items)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Review the complete translation. Apply commits all items together.")))
        self.list = QListWidget(self)
        self.list.setAccessibleName(self.tr("Translation items"))
        self.list.addItems([item[0] for item in self.items])
        layout.addWidget(self.list)
        columns = QHBoxLayout()
        self.original = QPlainTextEdit(self)
        self.original.setAccessibleName(self.tr("Original text"))
        self.original.setReadOnly(True)
        self.translated = QPlainTextEdit(self)
        self.translated.setAccessibleName(self.tr("Translated text"))
        self.translated.setReadOnly(True)
        for title, editor in ((self.tr("Original"), self.original), (self.tr("Translation"), self.translated)):
            column = QVBoxLayout()
            column.addWidget(QLabel(title))
            column.addWidget(editor)
            columns.addLayout(column)
        layout.addLayout(columns)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.list.currentRowChanged.connect(self._show_item)
        if self.items:
            self.list.setCurrentRow(0)

    def _show_item(self, row: int) -> None:
        if 0 <= row < len(self.items):
            _, original, translated = self.items[row]
            self.original.setPlainText(original)
            self.translated.setPlainText(translated)

    @staticmethod
    def character_field_label(field: CharacterTextField) -> str:
        """Identify reviewed prose with stable IDs and translated field captions."""
        labels = {
            'full_name': ProjectTranslationReviewDialog.tr('Full name'),
            'display_name': ProjectTranslationReviewDialog.tr('Display name'),
            'aliases': ProjectTranslationReviewDialog.tr('Aliases'),
            'role': ProjectTranslationReviewDialog.tr('Role'),
            'description': ProjectTranslationReviewDialog.tr('Description'),
            'primary_motivation': ProjectTranslationReviewDialog.tr('Primary motivation'),
            'secondary_motivations': ProjectTranslationReviewDialog.tr('Secondary motivations'),
            'desires': ProjectTranslationReviewDialog.tr('Desires'),
            'needs': ProjectTranslationReviewDialog.tr('Needs'),
            'obstacles': ProjectTranslationReviewDialog.tr('Obstacles'),
            'accepted_risks': ProjectTranslationReviewDialog.tr('Risks they accept'),
            'refusals': ProjectTranslationReviewDialog.tr('Things they refuse to do'),
            'internal_conflicts': ProjectTranslationReviewDialog.tr('Internal conflicts'),
            'background': ProjectTranslationReviewDialog.tr('Background'),
            'personality': ProjectTranslationReviewDialog.tr('Personality'),
            'goals': ProjectTranslationReviewDialog.tr('Goals'),
            'knowledge': ProjectTranslationReviewDialog.tr('Knowledge and secrets'),
            'arc': ProjectTranslationReviewDialog.tr('Arc notes'),
            'age': ProjectTranslationReviewDialog.tr('Age'),
            'occupation': ProjectTranslationReviewDialog.tr('Occupation'),
            'origin': ProjectTranslationReviewDialog.tr('Origin and culture'),
            'appearance': ProjectTranslationReviewDialog.tr('Appearance'),
            'history': ProjectTranslationReviewDialog.tr('History'),
            'social_status': ProjectTranslationReviewDialog.tr('Status and affiliations'),
            'traits': ProjectTranslationReviewDialog.tr('Personality traits'),
            'strengths': ProjectTranslationReviewDialog.tr('Strengths'),
            'weaknesses': ProjectTranslationReviewDialog.tr('Weaknesses'),
            'fears': ProjectTranslationReviewDialog.tr('Fears'),
            'values': ProjectTranslationReviewDialog.tr('Values and beliefs'),
            'habits': ProjectTranslationReviewDialog.tr('Habits'),
            'emotional_triggers': ProjectTranslationReviewDialog.tr('Emotional triggers'),
            'contradictions': ProjectTranslationReviewDialog.tr('Contradictions'),
            'speech_patterns': ProjectTranslationReviewDialog.tr('Speech patterns'),
            'attitudes': ProjectTranslationReviewDialog.tr('Attitudes'),
            'status': ProjectTranslationReviewDialog.tr('Status'),
            'notes': ProjectTranslationReviewDialog.tr('Notes'),
            'statement': ProjectTranslationReviewDialog.tr('Statement'),
            'initial_worldview': ProjectTranslationReviewDialog.tr('Initial worldview'),
            'initial_state': ProjectTranslationReviewDialog.tr('Initial state'),
            'desired_transformation': ProjectTranslationReviewDialog.tr('Desired transformation'),
            'lessons': ProjectTranslationReviewDialog.tr('Lessons'),
            'turning_points': ProjectTranslationReviewDialog.tr('Turning points'),
            'expected_end_state': ProjectTranslationReviewDialog.tr('Expected end state'),
            'current_state': ProjectTranslationReviewDialog.tr('Current state'),
            'unresolved_conflicts': ProjectTranslationReviewDialog.tr('Unresolved conflicts'),
            'relationship_type': ProjectTranslationReviewDialog.tr('Relationship type'),
            'attitude': ProjectTranslationReviewDialog.tr('Emotional attitude'),
            'shared_secrets': ProjectTranslationReviewDialog.tr('Shared secrets or conflicts'),
            'development_notes': ProjectTranslationReviewDialog.tr('Development notes'),
            'purpose': ProjectTranslationReviewDialog.tr('Scene purpose'),
            'relevant_goals': ProjectTranslationReviewDialog.tr('Scene-relevant goals'),
            'state_changes': ProjectTranslationReviewDialog.tr('State changes'),
            'value': ProjectTranslationReviewDialog.tr('Value'),
            'previous_value': ProjectTranslationReviewDialog.tr('Previous value'),
            'evidence': ProjectTranslationReviewDialog.tr('Evidence'),
        }
        if field.path[0] == "characters":
            category = ProjectTranslationReviewDialog.tr("Character profile")
            path = field.path[2:]
        elif field.path[0] == "character_relationships":
            category = ProjectTranslationReviewDialog.tr("Character relationship")
            path = field.path[2:]
        else:
            category = ProjectTranslationReviewDialog.tr("Scene development")
            association_index = field.path.index("character_associations")
            path = field.path[association_index + 2:]
        caption = " / ".join(str(key + 1) if isinstance(key, int) else labels[key] for key in path)
        return f"{category}: {field.owner_name} [{field.owner_id}] — {caption}"
