# Model Benchmarks

This note records quick courtroom-simulation benchmark results for the current MVP runtime.

Date: `2026-05-09`

Scenario:

- `civil_contract_dispute`
- Vietnamese contract dispute over delayed vehicle delivery
- Same backend runtime, retrieval, verification, and shared contracts
- Only the `plaintiff`, `defense`, `judge summary`, and `report summary` language-generation path used the live model

Evaluation criteria:

- provider compatibility with the repo's strict JSON contract
- relevance to the courtroom/legal scenario
- role consistency, especially whether `defense` actually argued for the defense
- summary quality
- latency

## OpenRouter

| Model | Provider smoke | Simulation quality | Latency | Notes |
| --- | --- | --- | --- | --- |
| `inclusionai/ring-2.6-1t:free` | Pass | Best overall | ~39.5s | Most balanced and natural courtroom output. Strong plaintiff, defense, judge, and report summary. |
| `tencent/hy3-preview` | Pass | Very good | ~93.9s | Strong legal framing, but much slower and more verbose than `ring`. |
| `baidu/cobuddy:free` | Pass | Good | ~60.5s | Clean and usable, but shallower than `ring`. |
| `openrouter/free` | Pass | Good with caveats | ~79.5s | Usable, but sometimes over-infers remedies such as contract cancellation. |
| `openai/gpt-oss-120b:free` | Pass | Weak | ~47.5s | Defense reasoning drifted toward the plaintiff side in testing. |
| `poolside/laguna-xs.2:free` | Pass | Weak | ~36.2s | Defense stance also drifted and felt less trustworthy. |
| `nvidia/nemotron-3-super-120b-a12b:free` | Pass | Weak | ~161.8s | Output mixed Vietnamese with other languages/symbols. |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | Partial | Weak | ~370.2s | Too slow for MVP and not worth the latency. |
| `google/gemma-4-31b-it:free` | Rate-limited | Not ranked | N/A | Returned `429 Too Many Requests` during testing. |
| `google/gemma-4-26b-a4b-it:free` | Rate-limited | Not ranked | N/A | Returned `429 Too Many Requests` during testing. |
| `tencent/hy3-preview:free` | Fail | Not ranked | N/A | Previously returned `404` on OpenRouter and should not be used. |

OpenRouter winner: `inclusionai/ring-2.6-1t:free`
Retest note: quality remains the best, but the free route showed intermittent `429` rate limiting during a later retest on the same day.

## Groq

| Model | Provider smoke | Simulation quality | Latency | Notes |
| --- | --- | --- | --- | --- |
| `qwen/qwen3-32b` | Pass | Best on Groq | ~7.4s | Best balance of speed and courtroom relevance on Groq. Strong plaintiff and defense framing. |
| `groq/compound` | Pass | Good | ~26.7s | Rich output, but slower and slightly more assumption-prone than `qwen`. |
| `llama-3.3-70b-versatile` | Pass | Acceptable | ~7.1s | Very fast, but too terse for the courtroom simulation. |
| `openai/gpt-oss-120b` | Pass | Mixed | ~6.1s | Some generations looked close to heuristic fallback rather than a strong upgrade. |
| `llama-3.1-8b-instant` | Contract issue | Fallback-heavy | ~6.1s | Failed the strict JSON smoke once, so simulation quality is not reliable for structured generation. |

Groq winner: `qwen/qwen3-32b`
Retest note: this model remained stable on both provider smoke and courtroom simulation retests.

## Ollama Cloud

| Model | Provider smoke | Simulation quality | Latency | Notes |
| --- | --- | --- | --- | --- |
| `deepseek-v4-flash:cloud` | Fail on tested key | Not ranked | N/A | Official Python SDK integration worked technically, but the tested key returned `403` with `this model requires a subscription, upgrade for access`. |

## Final Recommendation

Overall winner for the current MVP: `inclusionai/ring-2.6-1t:free` on OpenRouter

Why:

- best courtroom tone and role consistency
- strongest end-to-end quality in plaintiff, defense, judge summary, and report summary
- fewer obvious reasoning drifts than the other free models tested

Best Groq option: `qwen/qwen3-32b`

MVP default pair:

- OpenRouter: `inclusionai/ring-2.6-1t:free`
- Groq: `qwen/qwen3-32b`

Operational note:

- Use `ring` as the preferred OpenRouter model for quality.
- Keep `qwen` on Groq as the most reliable alternate path when OpenRouter free capacity is rate-limited.

Best Ollama Cloud status on the tested key: no usable benchmark yet because the requested model requires a subscription tier that the tested key does not currently have.

Suggested fallback order:

1. `inclusionai/ring-2.6-1t:free`
2. `qwen/qwen3-32b`
3. `groq/compound`
4. `baidu/cobuddy:free`
5. `openrouter/free`

## Practical Setup

OpenRouter:

```powershell
$env:AI_COURT_LLM_PROVIDER="openrouter"
$env:OPENROUTER_MODEL="inclusionai/ring-2.6-1t:free"
```

Groq:

```powershell
$env:AI_COURT_LLM_PROVIDER="groq"
$env:GROQ_MODEL="qwen/qwen3-32b"
```

Ollama Cloud:

```powershell
$env:AI_COURT_LLM_PROVIDER="ollama"
$env:OLLAMA_MODEL="deepseek-v4-flash:cloud"
```
