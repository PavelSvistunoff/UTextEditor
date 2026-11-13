# Run Codex with a local Ollama model (optional)

These examples show a **local Codex CLI configuration**. They are not required to build or test UTextEditor, and the model names are illustrative; make sure Ollama has the model installed before running Codex.

```bash
codex --oss --local-provider ollama --model qwen3-coder:30b
# Or:
codex --oss --local-provider ollama --model gemma4:12b
```

Before changing code, follow [AGENTS.md](AGENTS.md) and select a bounded, verifiable item in [TASKS.md](TASKS.md). Use the current [checkpoint](IMPLEMENTATION_PROGRESS.md); do not automatically implement every open parent.
