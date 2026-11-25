# Agentic Setup and Operations (English)

This file is the working guide for **AI agents** (Hermes, Claude, Cursor, etc.) that set up, use, or maintain LLM-Wikitila in a project. (German version: [docs/agentic-setup.de.md](agentic-setup.de.md).)

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
