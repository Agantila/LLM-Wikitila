# Evidence-Backed Benefits (English)

Comparison of LLM-Wikitila with a **pure graph rack (GraphRAG)** and a **pure link search** — every benefit with a measurement from the AGANTILA vault (50-question catalog, state 2026-11-14).

## Baseline

| Approach | What it does | Measured |
|---|---|---|
| Graph rack / GraphRAG (`graphify query`) | Subgraph as context, neighborhoods, wiki summaries | R@10 **0.25** (MRR 0.067); older graph R@10 **0.00** |
| Pure link search | follows links only, no full-text ranking | in the stack only as a small boost (weight 0.05) |
| **LLM-Wikitila** | Full text + deterministic links + authority/freshness + evidence contract | R@10 **1.00**, MRR 0.785, p95 ~35 ms |

## The seven benefits

1. **Significantly higher hit rate.** R@10 1.00 vs. 0.25 for the graph rack. The graph alone barely finds "which file answers this"; it is navigation, not a finder.
2. **Fast and deterministic.** ~20 ms, no service, GPU, or Docker; BM25 and the link graph are reproducible.
3. **Evidence instead of claims.** Every answer carries file, heading, and original passage. Graph summaries alone are not evidence — they can amplify errors.
4. **Validity instead of mere relevance.** GraphRAG knows relevance, not validity. The authority register decides which source is authoritative and still current (price 299/499/699 → 549/899/1.199 resolved automatically).
5. **Controlled "not supported".** The answer gate reports missing knowledge (status + `unmatched_terms`/`top1_missing_terms`) instead of returning a plausible wrong answer.
6. **No vector store required.** An embedding only helped in an early measurement (up to +0.18 MRR); the final pipeline reaches R@10 1.00 without vectors. No service, no 80 MB vector database.
7. **No model in the runtime path.** Decision models worsened ranking (MRR 0.659/0.617 vs. 0.794) and answer gating (AUC 0.70/0.78 vs. 0.94). Models remain limited to the one-time graph build and an optional maintenance lint.

## Limits (honest)

- The numbers come from a 50-question self-catalog with known content; they prove **search quality**, not every factual correctness.
- Near-topic abstention is a semantic task for the agent (the stack provides the signals).
- Authority effects only apply once the owner maintains the register.
