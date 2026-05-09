# Orchestration Package

This package now owns the Phase 3 CPU-friendly courtroom runtime baseline.

Current scope:

- LangGraph-based simulation flow
- legal retrieval handoff into argument generation
- structured plaintiff, defense, judge, and clerk turns
- runtime state transitions for `/simulate`
- OpenRouter-backed text generation with heuristic fallback

The runtime is still schema-first and retrieval-grounded. When `OPENROUTER_API_KEY` is set, the package
auto-upgrades role messages and summaries with a live OpenRouter model unless you explicitly force
`AI_COURT_LLM_PROVIDER=heuristic`.
If the provider is missing, rate-limited, or unavailable, it falls back to the deterministic heuristic path.
