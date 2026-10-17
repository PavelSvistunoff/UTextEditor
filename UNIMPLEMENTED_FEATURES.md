# Unimplemented features compared to SPEC.md

Overall: most of the MVP editor + Ollama + completion + spellcheck flow is already present. The remaining gaps are relatively small but still meaningful.

## 1) Editor appearance settings are not implemented

Spec requirement:
- Section 28: Editor settings should include font, font size, tab width, word wrap, line numbers, and theme/dark mode.

Current status:
- `AppSettings` in `app/settings/settings.py` stores AI-related values only (`ollama_host`, `ollama_model`, completion settings, spellcheck settings, language).
- `SettingsDialog` in `app/ui/settings_dialog.py` is an AI settings dialog only; it does not expose editor configuration.
- `EditorWidget` in `app/ui/editor_widget.py` has no editor preference state for font, tab width, word wrap, line numbers, or dark theme.

Impact:
- The application does not yet satisfy the editor-settings portion of the specification.


## 2) `Auto` language detection is only exposed in settings, not actually implemented

Spec requirement:
- Section 25: supported languages should include `Auto`, `English`, and `Ukrainian`.
- The architecture should pass the selected language to AI services, and `Auto` may use automatic detection.

Current status:
- The UI in `app/ui/settings_dialog.py` includes `Auto`, `English`, and `Ukrainian`.
- `AppSettings.language` exists and is passed into AI completion/spellcheck calls.
- There is no actual automatic-language detection logic in the codebase, and no language-aware logic beyond passing the selected string to the model.

Impact:
- The settings UI is present, but the `Auto` mode is effectively not implemented as a real feature.

## Conclusion

The codebase is close to the MVP spec for editor functionality, AI completion, and spellcheck, but the following items remain incomplete:

1. editor appearance settings;
2. real `Auto` language detection.
