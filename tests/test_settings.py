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
