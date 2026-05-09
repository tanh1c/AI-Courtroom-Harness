# Orchestration Package

This package now owns the Phase 3 CPU-friendly courtroom runtime baseline.

Current scope:

- LangGraph-based simulation flow
- legal retrieval handoff into argument generation
- structured plaintiff, defense, judge, and clerk turns
- runtime state transitions for `/simulate`
- OpenRouter- or Groq-backed text generation with heuristic fallback

The runtime is still schema-first and retrieval-grounded. When `AI_COURT_LLM_PROVIDER` is set to
`openrouter` or `groq`, the package upgrades role messages and summaries with a live provider-backed model.
In `auto` mode, it prefers OpenRouter when that key is available, otherwise Groq.
If the provider is missing, rate-limited, or unavailable, it falls back to the deterministic heuristic path.
