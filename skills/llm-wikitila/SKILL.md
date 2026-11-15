---
name: llm-wikitila
description: Use when setting up or operating LLM-Wikitila search and graph on any project folder.
license: MIT
---

# LLM-Wikitila: fast, evidence-backed search and local graph

Tools: `wikitila.py` (search/build/status/manifest/check/eval/embed), `wikitila_graph.py` (local Graphify extraction), `validate_catalog.py` (validation). Docs: `docs/` (German + English). Agent rules: `AGENTS.md` / `docs/agentic-setup.en.md`.

## When to load

- A folder/vault should become searchable (search, graph, second brain, LLM wiki).
- Graphify should run locally with Ollama instead of cloud subagents.
- Someone asks whether a vector store is needed.

## Workflow, in this order

0. **Search what exists before building.** Before any graph run over 5 minutes, state the duration, benefit, and expected gain (≈0.3 documents/s) and make clear: search works without the graph.
1. Create/extend `.graphifyignore` before building anything (third-party code, copies, `node_modules`, `*.js`).
2. `./install.sh <target-folder>` (idempotent), then `wikitila.py --root <folder> build` and test `search`.
3. Fill `authority_register.json` — only then do `kanonisch`/`überholt durch`/`veraltet` take effect.
4. Graph (optional): `wikitila_graph.py run --model maternion/ling-3.0-tiny:8b --workers 2`, then `build`, then `wikitila.py build`.
5. **Acceptance via a self-authored catalog** (JSONL, ~50 cases), measured with `validate_catalog.py` on three levels. Schema and procedure: `references/catalog-validation.md`.

## Lessons (measured)

- **No vector store as a service** for corpora up to several tens of thousands of sections: 26,000 vectors = 80 MB, brute force 25 ms. Embedding is optional and off.
- **Small models mis-assign relation types:** entities are usable; relations only as `related_to`, `INFERRED`, 0.5.
- **Exit code 2 means operator error, not an answer:** missing/empty index, broken `wikitila.toml`. Run `build` / fix the file; never report `nicht_belegt` in that case. Register problems arrive as `warnings` — mention them, canonical/superseded flags may be missing.
- **Ollama processes requests sequentially:** more than 2 workers speed nothing up. `think: false` + JSON schema (`format`).
- **Graphify skips files with `token`/`secret`/`password`/`credential` in the name.** Where sensitive material must stay findable, replace the check (see `wikitila_graph.py`).
- **`graph.json` is overwritten on build:** back it up first.
- **Graphify stores edges undirected:** check both directions on import.
- **Document IDs from shortened paths collide:** ID = shortened path + hash.
- **Failed documents (≈0.5%) need a second pass:** second run with larger `WIKITILA_NUM_PREDICT` (1600) and `WIKITILA_NUM_CTX` (8192), 1 worker. The cache makes runs resumable.
- **`graphify query` is not a file finder** (MRR 0.07): it returns subgraphs as context. For "where does it say that" use `wikitila.py search`; for connections use `graphify path`/`explain`.
- **File recall is not answer quality:** measure passages, authority, and abstention separately (`validate_catalog.py`).
- **`score` is RRF, not confidence.**
- **"Nothing found" ≠ "nothing exists":** status `nicht_belegt`, never "does not exist".
- **New own docs skew the catalog** (BM25 −0.03 MRR): only compare on the same corpus state. Never write negative-test keywords into indexed docs.
- **Eval with a decision model can hide regressions:** identical numbers mean HTTP errors + fallback. Check the error counters.
