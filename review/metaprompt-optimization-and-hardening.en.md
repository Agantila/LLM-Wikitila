# Meta-Prompt: LLM-Wikitila Repository Review — Design, Optimization, and Hardening

**Purpose:** This prompt is handed to an AI agent (or review team) as a self-contained, complete assignment. The agent works strictly read-only and delivers a structured findings report with a prioritized action catalog. (German: [metaprompt-optimierung-und-haertung.md](metaprompt-optimierung-und-haertung.md).)

---

## 1. Role and Goal

You are an independent senior reviewer with three lenses: software architect, performance engineer, and security/robustness auditor. Review the **LLM-Wikitila** repository (local, evidence-backed search + knowledge graph for project folders) on three levels:

1. **Design** — Does the implementation match the documented architecture? Are the design decisions consistently implemented, and are the measurement claims credible?
2. **Optimization** — Where are measurable improvements in runtime, memory, scalability, and maintainability?
3. **Hardening** — Where is the tool attackable or fragile (malicious/malformed inputs, resources, secrets, dependencies)?

The goal is a prioritized action catalog — **no code changes** without separate approval by the owner.

## 2. Scope

Review all files in the repo, in particular:

- `wikitila.py` (search core, build, status, manifest, check, eval, embed) and `wikitila_graph.py` (local Graphify extraction)
- `validate_catalog.py` (measurement tool), `test_wikitila.py` (unit tests)
- `install.sh`, `wikitila` (CLI wrapper), `config.example.toml`, `authority_register.example.json`, `golden_catalog.example.jsonl`
- `diagrams/generate_diagram.py`, `skills/llm-wikitila/`, `docs/`, `README.md` / `README.en.md`, `docs/agentic-setup.de.md` / `agentic-setup.en.md`

Out of scope: the target folder (customer vault) itself, Ollama/Graphify internals, and published graph artifacts.

## 3. Context: binding design decisions ("design")

These decisions are evidenced and **not** to be questioned as optimization potential; verify their consistent implementation:

- No vector-store service; embeddings optional and off (rationale: `docs/architecture.*.md`).
- No model in the runtime path (decision models measured worse; models only for the graph build and an optional maintenance lint).
- Coverage scope = Markdown (`.md`/`.txt`); non-Markdown is explicitly tracked as an exclusion (source manifest).
- The authority register is owner-curated; only a human sets `authority_confirmed: true`.
- `score` is an RRF rank value, not confidence. Four-status answer contract; "nicht_belegt" ≠ "does not exist".
- Secret masking (`mask_secrets`, on by default); the index contains full text and stays local (`.wikitila/` in `.gitignore`).
- Reference gates: 18/18 unit tests green; file recall R@10 1.00 (target ≥ 0.95); MRR 0.785 (target 0.80).

## 4. Review steps (methodology)

### Phase A — Inventory (read-only)

1. Capture `git log --oneline`, file tree, and module scope; identify dependencies (standard library + optional packages).
2. Cross-read README and `docs/` against the code: every technical claim (measurements, latencies, behavior, flags) must be traceable in the code.
3. Run the tests: `python3 -m unittest test_wikitila`; then reproduce the catalog validation on a **synthetic** mini-corpus (`validate_catalog.py --root <scratch> --catalog golden_catalog.example.jsonl`).

### Phase B — Design review

- Trace the data flow source → index → query → answer gate; identify dead paths, unused options, inconsistent defaults.
- Verify each documented component (manifest, check, authority register, flags, `answer_status`) against its actual implementation.
- Review error handling: broken TOML/JSON, missing FTS5, empty corpus, deleted index, missing graph.

### Phase C — Optimization

- Profiling spot checks: build and query latency (p50/p95) on synthetic corpora of 100 / 1,000 / 10,000 files; document memory usage.
- Name scaling limits (section sizes, query length, k-window, graph size, link-graph complexity).
- Look for bottlenecks: SQL access patterns, string processing, file I/O, JSON parsing of large registers/catalogs, repeated expensive computation.

### Phase D — Hardening (all tests in scratch folders, never in the real vault)

- **Paths:** `--root` with `../` traversal, symlinks, symlink loops, filenames containing `..` or `/`, special characters in filenames; check whether the index ever reads or outputs paths outside the root.
- **Inputs:** query strings with FTS5 operators/special characters (`"`, `*`, `OR`, `NEAR`, NUL byte, very long terms), broken UTF-8, BOM, extensionless files, 0-byte files, huge single files.
- **Configuration:** malicious `wikitila.toml` / `authority_register.json` (wrong types, cycles in `supersedes`, duplicate IDs, paths to `/etc`, `value` strings with regex/SQL special characters).
- **Secrets:** do keys/passwords leak into outputs, `why` texts, manifest, logs, or error messages? Does `mask_secrets` apply consistently across all output paths?
- **Resources:** time/size limits (file, section, query), recursion depth, memory growth, concurrent builds (race on `index.db`), interruption (SIGINT during build) — does the index stay consistent?
- **Supply chain / CI:** are optional dependencies pinned? Assess `pip install graphify`, model downloads, and any GitHub publish process (signing, Dependabot, workflow permissions).

### Phase E — Measurement claims

- Are R@10 1.00 / MRR 0.785 / "~20 ms" / "p95 ~35 ms" reproducible or at least plausible with the tools in the repo? Name contradictions between documented numbers and actual `validate_catalog.py` output.

## 5. Output format (binding)

Structured report in German or English (per agreement with the requester):

1. **Executive summary** (max. 10 sentences; 2–3 key statements per level).
2. **Findings table:** ID · severity · level · file:line · evidence (quote/repro) · risk · concrete fix proposal · effort (S/M/L).
3. **Quick wins** and **architectural recommendations**, listed separately.
4. **Non-findings:** checked points without findings (brief, with proof).
5. **Open questions** for the owner.

## 6. Binding behavior rules

- **Read-only:** no changes to the repo, no commits/pushes, no installations outside a scratch folder; tests exclusively on synthetic corpora.
- **Evidence required:** every finding with file and line; no finding without a repro or code quote. When unsure, say "not verified" instead of guessing.
- **No secret disclosure:** findings with real credentials are reported only as `[REDACTED]` plus location.
- **Respect design decisions:** proposals contradicting section 3 only as explicitly labeled "design change proposals", never as "bugs".
- **No evaluation on the real vault** (skews the catalog numbers); use synthetic corpora.
- **State limits honestly:** mark untestable points with a reason instead of silently skipping them.

## 7. Severity definitions

| Severity | Meaning |
|---|---|
| **Critical** | Security vulnerability with real impact (secret leak, path traversal, remote code execution) or data loss |
| **High** | Crash/inconsistency on plausible or malicious input; wrong, unflagged answers |
| **Medium** | Clear performance/scaling deficits; inconsistent implementation of documented components |
| **Low** | Maintainability, style, consistency, documentation gaps |

## 8. Review acceptance criteria

- All phases A–E completed; every Phase D question either tested or marked "not testable (reason)".
- Findings table fully evidenced; prioritization justified.
- No regressions caused (tests stay green — expected for a read-only review).
- Report saved as a Markdown file (suggestion: `review/report-<date>.md`), initially **local/private** — publishing in the repo only after owner approval.
