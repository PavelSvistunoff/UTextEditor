from app.ai.prompts import DEFAULT_AI_ROLE
from app.settings.settings import AppSettings


def test_default_ai_role_predicts_the_next_user_text() -> None:
    assert AppSettings().ai_role == DEFAULT_AI_ROLE
    assert DEFAULT_AI_ROLE == "You are a medium. Predict what I will say next."


def test_settings_load_recovers_from_malformed_and_out_of_range_values(tmp_path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text('ollama_host: "not a url"\ncompletion_debounce_ms: -1\ntemperature: .nan\nlanguage: []\nfuture: true\n')

    settings = AppSettings.load(path)

    assert settings.completion_debounce_ms == AppSettings().completion_debounce_ms
    assert settings.temperature == AppSettings().temperature
    assert settings.language == "Auto"
    assert settings.ollama_host == AppSettings().ollama_host


def test_settings_validation_clamps_and_rejects_invalid_editor_preferences() -> None:
    settings = AppSettings(
        font_family="   ",
        font_size=99,
        tab_width=0,
        word_wrap="yes",
        line_numbers="no",
    )

    validated = settings.validated()

    assert validated.font_family == AppSettings().font_family
    assert validated.font_size == AppSettings().font_size
    assert validated.tab_width == AppSettings().tab_width
    assert validated.word_wrap is AppSettings().word_wrap
    assert validated.line_numbers is AppSettings().line_numbers
    assert validated.language == AppSettings().language


def test_settings_save_and_load_round_trip(tmp_path) -> None:
    path = tmp_path / "nested" / "settings.yaml"
    settings = AppSettings(language="Ukrainian", context_size=8192, font_family="Liberation Mono", font_size=14, tab_width=2, word_wrap=True, line_numbers=True)

    settings.save(path)
    loaded = AppSettings.load(path)

    assert loaded.language == "Ukrainian"
    assert loaded.context_size == 8192
    assert loaded.font_family == "Liberation Mono"
    assert loaded.font_size == 14
    assert loaded.tab_width == 2
    assert loaded.word_wrap is True
    assert loaded.line_numbers is True


def test_ui_language_is_a_separate_persisted_setting_and_invalid_values_fall_back(tmp_path):
    path = tmp_path / "settings.yaml"
    AppSettings(ui_language="uk", language="English").save(path)

    loaded = AppSettings.load(path)

    assert loaded.ui_language == "uk"
    assert loaded.language == "English"
    assert AppSettings(ui_language=["uk"]).validated().ui_language == "system"


def test_ai_context_consent_is_destination_specific_and_round_trips(tmp_path):
    path = tmp_path / "settings.yaml"
    settings = AppSettings(ai_context_consent_host="https://ollama.example:11434/")
    settings.save(path)
    loaded = AppSettings.load(path)

    assert loaded.has_ai_context_consent("https://ollama.example:11434")
    assert loaded.has_ai_context_consent("https://ollama.example:11434/")
    assert not loaded.has_ai_context_consent("http://localhost:11434")
    assert not loaded.has_ai_context_consent("http://ollama.example:11434")
    assert not AppSettings().has_ai_context_consent("http://localhost:11434")


def test_invalid_ai_context_consent_is_not_trusted():
    for value in (None, 123, "invalid", "https://user:password@example.com", "https://example.com/path"):
        settings = AppSettings(ai_context_consent_host=value).validated()
        assert settings.ai_context_consent_host == ""


def test_autosave_preferences_round_trip_and_validate_idle_interval(tmp_path) -> None:
    path = tmp_path / "settings.yaml"
    settings = AppSettings(autosave_enabled=False, autosave_idle_ms=3500)
    settings.save(path)

    loaded = AppSettings.load(path)

    assert not loaded.autosave_enabled
    assert loaded.autosave_idle_ms == 3500
    assert AppSettings(autosave_idle_ms=1).validated().autosave_idle_ms == 2000


def test_recent_projects_round_trip_and_validation(tmp_path) -> None:
    first = str((tmp_path / "first").resolve())
    second = str((tmp_path / "second").resolve())
    settings_path = tmp_path / "settings.yaml"
    AppSettings(recent_projects=[first, second]).save(settings_path)

    loaded = AppSettings.load(settings_path)
    validated = AppSettings(
        recent_projects=[first, "relative/project", first, "", 42]
    ).validated()
    capped = AppSettings(
        recent_projects=[str((tmp_path / f"project-{index}").resolve()) for index in range(12)]
    ).validated()

    assert loaded.recent_projects == [first, second]
    assert validated.recent_projects == [first]
    assert len(capped.recent_projects) == 10


def test_recent_files_are_separate_bounded_and_persisted(tmp_path):
    first = str(tmp_path / "first.txt")
    second = str(tmp_path / "second.txt")
    settings_path = tmp_path / "settings.yaml"
    AppSettings(recent_files=[first, second], recent_projects=[str(tmp_path)]).save(settings_path)
    loaded = AppSettings.load(settings_path)
    assert loaded.recent_files == [first, second]
    assert loaded.recent_projects == [str(tmp_path)]
    cleaned = AppSettings(recent_files=[first, "relative", first, "", 42]).validated()
    assert cleaned.recent_files == [first]
    spaced = str(tmp_path / "name with trailing space ")
    assert AppSettings(recent_files=[spaced]).validated().recent_files == [spaced]
    assert len(AppSettings(recent_files=[str(tmp_path / str(i)) for i in range(12)]).validated().recent_files) == 10


def test_automatic_project_context_setting_round_trips_and_validates(tmp_path):
    path = tmp_path / "settings.yaml"
    AppSettings(automatic_project_context=False).save(path)
    assert not AppSettings.load(path).automatic_project_context
    assert AppSettings(automatic_project_context="invalid").validated().automatic_project_context is True


def test_settings_ignore_legacy_theme_override(tmp_path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text("theme: Dark\n", encoding="utf-8")

    settings = AppSettings.load(path)

    assert settings == AppSettings()


def test_default_settings_path_uses_yaml_file() -> None:
    assert AppSettings._default_settings_path().name == "settings.yaml"


def test_default_settings_save_and_load_use_yaml(tmp_path, monkeypatch) -> None:
    path = tmp_path / "settings.yaml"
    monkeypatch.setattr(AppSettings, "_default_settings_path", staticmethod(lambda: path))
    settings = AppSettings(language="Ukrainian")

    settings.save()

    assert path.read_text(encoding="utf-8").startswith("ollama_host:")
    assert AppSettings.load() == settings


def test_settings_load_migrates_from_legacy_json_path(tmp_path, monkeypatch) -> None:
    path = tmp_path / "settings.yaml"
    path.with_name("settings.json").write_text('{"language": "Ukrainian"}', encoding="utf-8")
    monkeypatch.setattr(AppSettings, "_default_settings_path", staticmethod(lambda: path))

    settings = AppSettings.load()

    assert settings.language == "Ukrainian"


def test_settings_load_recovers_from_malformed_yaml(tmp_path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text("ollama_host: [unclosed\n", encoding="utf-8")

    assert AppSettings.load(path) == AppSettings()


def test_streaming_preview_setting_round_trips_and_rejects_invalid_values(tmp_path):
    path = tmp_path / "settings.yaml"
    AppSettings(streaming_preview=True).save(path)
    assert AppSettings.load(path).streaming_preview is True
    assert AppSettings(streaming_preview="yes").validated().streaming_preview is False
