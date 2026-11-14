import pytest

from app.ai.context_budget import ContextBudget, ContextBudgetError


@pytest.mark.parametrize("text", ["The quiet night", "Тиха українська ніч", "і\u0308 🌙"])
def test_budget_counts_rendered_utf8_and_response_reserves(text):
    role = "Author assistant"
    prompt = f"Instruction\n<data>{text}</data>"
    required = len((role + prompt).encode("utf-8")) + 40 + 16 + 32
    budget = ContextBudget(required, output_tokens=40, safety_tokens=16)
    assert budget.remaining_tokens(role, prompt) == 0
    budget.require_fit(role, prompt)
    with pytest.raises(ContextBudgetError, match="not an exact token count"):
        ContextBudget(required - 1, 40, safety_tokens=16).require_fit(role, prompt)


def test_budget_refuses_tiny_window_and_never_trims_mandatory_text():
    with pytest.raises(ContextBudgetError, match="no content was truncated"):
        ContextBudget(64, 64).require_fit("role", "required evidence")
    assert ContextBudget(1024, 100).remaining_tokens("r", "p") == 634


@pytest.mark.parametrize("options", [
    {"context_tokens": 0}, {"context_tokens": True}, {"context_tokens": 1.5},
    {"output_tokens": -1}, {"safety_tokens": -1}, {"message_overhead_tokens": False},
])
def test_budget_rejects_invalid_units(options):
    with pytest.raises(ValueError):
        ContextBudget(**({"context_tokens": 2048, "output_tokens": 100} | options))
