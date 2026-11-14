"""Audit tripwire for provider dispatches, including bound methods and streams.

Behavior regressions live in the listed modules; this inventory makes a newly
introduced dispatch require an explicit context/consent policy review.
"""

import ast
from collections import Counter
from pathlib import Path


# File, function, provider method, references, policy, behavioral regression module.
DISPATCH_POLICIES = (
    ("ai/captured_completion.py", "generate_captured_completion", "generate_private", 1, "frozen-reviewed", "test_captured_generation.py"),
    ("ai/captured_completion.py", "generate_captured_completion", "generate_stream", 1, "frozen-reviewed", "test_rag_generation.py"),
    ("ai/character_development.py", "suggest_character_development", "generate_private", 1, "selected-excerpt-or-reviewed", "test_analysis_retrieval.py"),
    ("ai/character_profile.py", "suggest_character_fields", "generate_private", 1, "full-notes-or-reviewed", "test_analysis_retrieval.py"),
    ("ai/completion_service.py", "complete", "complete", 1, "paragraph-and-explicit-project-input", "test_completion_service.py"),
    ("ai/completion_service.py", "generate", "generate", 1, "author-prompt-only", "test_completion_service.py"),
    ("ai/project_analysis.py", "run_project_analysis", "generate_private", 1, "selected-sources-or-reviewed", "test_analysis_retrieval_ui.py"),
    ("ai/project_planning.py", "suggest_project_brief", "generate_private", 1, "brief-or-reviewed", "test_planning_retrieval_ui.py"),
    ("ai/project_planning.py", "generate_project_outline", "generate_private", 1, "brief-or-reviewed", "test_planning_retrieval_ui.py"),
    ("ai/spellcheck_service.py", "check", "check_spelling", 1, "target-only", "test_spellcheck_service.py"),
    ("project/analysis_context.py", "generate", "generate_private", 1, "frozen-reviewed", "test_analysis_retrieval.py"),
    ("project/auto_writer.py", "run_auto_writer", "generate_private", 1, "full-reference-or-reviewed", "test_auto_writer_retrieval.py"),
    ("project/autopilot.py", "run_autopilot", "generate_private", 2, "brief-plan-or-reviewed-transients", "test_planning_retrieval.py"),
    ("project/spelling_context.py", "generate", "generate_private", 1, "reviewed-dictionary-no-prose", "test_spelling_dictionary.py"),
    ("project/translation.py", "translate", "generate_private", 1, "full-target-only", "test_project_translation.py"),
    ("project/translation_context.py", "generate", "generate_private", 1, "reviewed-glossary-examples", "test_translation_retrieval.py"),
    ("ui/main_window.py", "generate_from_prompt", "generate_stream", 1, "author-prompt-only", "test_ai_workflows_e2e.py"),
    ("ui/main_window.py", "generate_from_prompt", "generate", 1, "author-prompt-only", "test_ai_workflows_e2e.py"),
    ("ui/main_window.py", "request_completion", "complete", 2, "paragraph-or-project-capture", "test_ai_workflows_e2e.py"),
)


def test_every_provider_dispatch_has_an_audited_policy_and_behavior_tests():
    root = Path(__file__).resolve().parents[1]
    actual = Counter()
    methods = {"generate", "generate_private", "generate_stream", "complete", "check_spelling"}
    receivers = {"provider", "self.provider", "window.provider", "self.completion_service", "self.spellcheck_service"}

    def visit(node, path, function=""):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function = node.name
        if isinstance(node, ast.Attribute) and node.attr in methods and ast.unparse(node.value) in receivers:
            actual[path, function, node.attr] += 1
        for child in ast.iter_child_nodes(node):
            visit(child, path, function)

    for path in (root / "app").rglob("*.py"):
        # The protocol and HTTP implementation implement these methods; they do
        # not select user workflow context. Infrastructure never retrieves.
        if path.name in {"provider.py", "ollama_client.py"}:
            continue
        visit(ast.parse(path.read_text()), str(path.relative_to(root / "app")))
    expected = Counter({(path, function, method): count
                        for path, function, method, count, policy, test in DISPATCH_POLICIES})
    assert actual == expected, "Audit new/removed provider dispatches and update the workflow matrix."
    for _path, _function, _method, _count, policy, test in DISPATCH_POLICIES:
        assert policy and (root / "tests" / test).is_file(), test
