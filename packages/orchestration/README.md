# Orchestration Package

This package now owns the Phase 3 CPU-friendly courtroom runtime baseline.

Current scope:

- LangGraph-based simulation flow
- legal retrieval handoff into argument generation
- structured plaintiff, defense, judge, and clerk turns
- runtime state transitions for `/simulate`
- OpenRouter-, Groq-, or Ollama Cloud-backed text generation with heuristic fallback

The runtime is still schema-first and retrieval-grounded. When `AI_COURT_LLM_PROVIDER` is set to
`openrouter`, `groq`, or `ollama`, the package upgrades role messages and summaries with a live provider-backed model.
In `auto` mode, it prefers OpenRouter when that key is available, otherwise Groq, otherwise Ollama Cloud.
If the provider is missing, rate-limited, or unavailable, it falls back to the deterministic heuristic path.

The recommended MVP chain is:

- primary: `openrouter / inclusionai/ring-2.6-1t:free`
- fallback: `groq / qwen/qwen3-32b`
- final: heuristic runtime text
