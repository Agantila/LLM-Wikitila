# Agentic Setup and Operations (English)

This file is the working guide for **AI agents** (Hermes, Claude, Cursor, etc.) that set up, use, or maintain LLM-Wikitila in a project. (German version: [docs/agentic-setup.de.md](agentic-setup.de.md).)

## 0. Setup prompt — paste into any agent harness

For the optimal setup, **one** prompt is enough. Copy the block unchanged into Claude Code, Codex, Cursor, Hermes, or any other agent harness. The agent clarifies the open questions with you before it writes anything — the questions double as the requirements checklist for an optimal LLM wiki.

```text
Set up LLM-Wikitila optimally in this folder (local, evidence-backed search over Markdown).
Source of truth: https://github.com/Agantila/LLM-Wikitila (docs/ + skills/llm-wikitila/).
Answer contract: belegt · widersprüchlich · belegt_gueltigkeit_unbestaetigt · nicht_belegt.

Work in this order and ASK about every open point before writing anything:

1. ROOT & SCOPE
   - Which folder is the canonical vault? (Default: the current folder.)
   - Which file types? (Default .md/.txt; everything else counts as an exclusion in the manifest.)
   - What must be excluded? → create/maintain .graphifyignore (node_modules, third-party code, copies, *.js, archives).

2. TOOLING
   - git clone https://github.com/Agantila/LLM-Wikitila.git  (or ./install.sh <folder>).
   - Create wikitila.toml only for real deviations from config.example.toml.

3. AUTHORITY (the core)
   - Which files are authoritative (prices, decisions, metrics, definitions)?
   - Which sources are superseded, and which replace what?
   - Which facts are time-sensitive (stale_after / review date)?
   → fill authority_register.json. ONLY the human owner sets authority_confirmed: true.

4. INDEX & CHECKS
   - wikitila.py --root <folder> build
   - wikitila.py --root <folder> manifest   (coverage: what is excluded and why)
   - wikitila.py --root <folder> check      (drift 0)
   - add .wikitila/ to .gitignore.

5. ACCEPTANCE
   - Create a question catalog (JSONL, ~50 cases: positive/authority/coverage/negative) with the owner.
   - python3 validate_catalog.py --root . --catalog <catalog>
     Targets: R@10 ≥ 0.95 · MRR ≥ 0.80 · passage presence high · coverage grade < 1.0 on negative cases.
   - Analyze missed cases (register, scope, headings) and fix them.

6. GRAPH (optional, never as the evidence source)
   - Only on explicit approval; state the duration first (≈0.3 documents/s).
   - wikitila_graph.py run --model maternion/ling-3.0-tiny:8b --workers 2, then build.

REPORT AT THE END: index state (files/sections), drift, acceptance metrics, open points.
Rules: never evaluate/test on a real vault; never write negative-test keywords into indexed docs.
```

Tip: `coverage "question"` checks answer coverage up-front without ranking — useful when an agent classifies a question as unanswerable.

## 1. Installation by an agent

```bash
# Target folder = the customer's project/second-brain folder
./install.sh /path/to/project-folder        # idempotent: wikitila.toml, register template, index, check
python3 wikitila.py --root /path/to/project-folder search "Test question" -k 5
```

After that, mandatory:

1. Fill `authority_register.json` in the target folder (schema: `docs/authority-register.en.md`). Without entries, no `kanonisch`/`überholt durch` effect.
2. Check/create `.graphifyignore` in the target folder (third-party code, copies, `node_modules`, `*.js`).
3. Run `python3 wikitila.py --root . manifest` + `check` — check coverage and drift.

## 2. Usage

```bash
python3 wikitila.py --root <folder> search "question" -k 5 --json   # search (~20 ms)
python3 wikitila.py --root <folder> build                           # update index
python3 wikitila.py --root <folder> manifest                        # coverage report
python3 wikitila.py --root <folder> check                           # index/source consistency
python3 wikitila.py --root <folder> status                          # index state
```

Answer fields: `results` (file, `heading`, `passages` = original passages, `score`, `why`), `answer_status`, `unmatched_terms`, `top1_missing_terms`, `term_coverage`/`uncovered` (coverage grade), `trace` (register rules + answer-gate reason), `bm25_top`. Flags per hit: `canonical`, `stale`, `unverified`, `superseded_by`, `authority`, `verified_at`. Pre-flight without ranking: `wikitila.py --root <folder> coverage "question"`.

## 3. Answer contract (binding for agents)

- **Evidence-backed statement as the unit:** every factual core statement with file, heading, and original passage; copy numbers, dates, names, and IDs exactly. Separate evidence, inference, and recommendation.
- **Four answer statuses:** `belegt` · `widersprüchlich` (name both values with sources and resolution) · `belegt_gueltigkeit_unbestaetigt` · `nicht_belegt` ("not reliably evidenced in the repository" — never "does not exist").
- **Abstention:** `nicht_belegt` on an empty result. With `top1_missing_terms` (term missing from the top-1 result, e.g. "pinterest"), abstain yourself: the passage then does not support the question.
- **Flags:** `überholt durch …` → read the successor; `kanonisch` → authoritative source; `veraltet`/`Gültigkeit nicht bestätigt` → leave validity open.
- **`score` is an RRF rank value** — never present it as confidence or a percentage.
- **No write-back** of auto-generated answers as new knowledge without human review.

## 4. Maintaining the authority register

- **Propose:** new entry with `authority_confirmed: false`, `note` with evidence (id, scope, canonical, owner).
- **Only the human owner** sets `authority_confirmed: true`, `verified_at`, `authority`, `supersedes`.
- Also update the file frontmatter (`supersedes`/`superseded_by`) on supersession.
- Check `stale_after` dates monthly.

## 5. Validation

- Create a question catalog (JSONL, schema: `docs/validation.en.md`) and measure with `python3 validate_catalog.py --root . --catalog <catalog>` (file recall, passage presence, coverage/negatives).
- Reference values: R@10 1.00 · MRR 0.785 · passages 45% · abstention signal 8/8 · 18/18 tests at measurement time (currently 39/39). MRR is below the 0.80 target (backlog B-010).
- File recall is **not** proof of answer quality.

## 6. Knowledge graph (optional)

```bash
python3 wikitila_graph.py run --model maternion/ling-3.0-tiny:8b --workers 2   # resumable
python3 wikitila_graph.py build
python3 wikitila.py --root <folder> build
```

The graph is **navigation** (path/explain), never an evidence source. The first run takes time (≈0.3 documents/s); state the runtime up front and make clear that search works without the graph. `graph.json` is overwritten on build — back it up first.

## 7. Pitfalls

- No vector store for corpora up to several tens of thousands of sections (embeddings measurably unnecessary).
- Decision models are **not** rankers/answer gates (measured worse) — at most maintenance-lint candidates.
- Never write negative-test keywords ("Pinterest", "Snapchat" …) into indexed docs — afterwards they are "present" in the corpus and lexical abstention can no longer detect them.
- The index contains full text → `.wikitila/` stays in `.gitignore`.
