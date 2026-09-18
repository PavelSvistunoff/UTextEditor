from app.ai.prompts import DEFAULT_AI_ROLE
from app.settings.settings import AppSettings


def test_default_ai_role_predicts_the_next_user_text() -> None:
    assert AppSettings().ai_role == DEFAULT_AI_ROLE
    assert DEFAULT_AI_ROLE == "You are a medium. Predict what I will say next."
