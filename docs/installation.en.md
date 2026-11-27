# Installation (English)

## Prerequisites

| Component | Requirement | Needed for |
|---|---|---|
| Python | ≥ 3.11 (standard library) | Search — always |
| SQLite FTS5 | included in Python ≥ 3.11 | Search — always |
| Ollama | installed and running | Knowledge graph (optional) |
| `maternion/ling-3.0-tiny:8b` | `ollama pull maternion/ling-3.0-tiny:8b` | Knowledge graph (optional) |
| Graphify + networkx | `pip install graphifyy==0.4.16 networkx==3.6.1` (PyPI name **graphifyy**, import `graphify`) | Knowledge graph (optional) |
| `embeddinggemma:latest` + `numpy` | only for embeddings | Embedding (optional, off by default) |

## Step by step

**Step 1 — Provide the repo.** Clone/copy this directory. The target folder (project/second-brain folder) stays untouched — LLM-Wikitila only adds `.wikitila/` (index) and `wikitila.toml` inside it.

**Step 2 — Set up (one command):**

```bash
./install.sh /path/to/project-folder
```

The installer is idempotent: it checks Python ≥ 3.11 with sqlite3/FTS5, creates `wikitila.toml` and an **empty** `authority_register.json` if missing (entry layout: `authority_register.example.json`), builds the index, and runs the index/source consistency check. If `python3` is too old or lacks sqlite3, set the interpreter: `PYTHON=/usr/bin/python3 ./install.sh …` (also applies to the `./wikitila` wrapper).

**Step 3 — Define exclusions.** Create `.graphifyignore` in the target folder (gitignore-like patterns, e.g. `Archive/`, `*Template_*.md`). The same file applies to search and graph.

**Step 4 — Test the search:**

```bash
python3 wikitila.py --root /path/to/project-folder search "Your question" -k 5
```

**Step 5 — Fill the authority register.** Populate `authority_register.json` in the target folder with the canonical source for each recurring topic (guide: `docs/authority-register.en.md`). Only then do `kanonisch` / `überholt durch` / `veraltet` flags take effect.

**Step 6 — Optional: build the knowledge graph.** Only after steps 1–5; search works without the graph.

```bash
python3 wikitila_graph.py run --model maternion/ling-3.0-tiny:8b --workers 2
python3 wikitila_graph.py build
python3 wikitila.py --root /path/to/project-folder build
```

Note: The first graph run takes time (~0.3 documents per second, e.g. 1,250 documents ≈ 68 minutes) and is resumable (per-file cache). The graph is **navigation**, not an evidence source.

## Verification

```bash
python3 wikitila.py --root . status      # Index state
python3 wikitila.py --root . manifest    # Coverage report (scope, exclusions)
python3 wikitila.py --root . check       # Index/source consistency (no drift?)
python3 wikitila.py --root . coverage "question"  # answer coverage up-front (coverage grade)
python3 -m unittest test_wikitila        # self-tests (79)
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `no such module: fts5` | Python without FTS5 | Use Python ≥ 3.11 |
| `build` finds 0 files | Wrong `--root` or `.graphifyignore` excludes everything | Check path and ignore file |
| Hits from deleted files | Stale index | Run `build` |
| Graph run aborts | Ollama stopped or model missing | `ollama list`, restart the run (resumes) |
| Entity mappings are 0 | `graph.json` not rebuilt | Run `wikitila_graph.py build`, then `wikitila.py build` |
| `FEHLER: Kein Index …` / `Index ist leer` (exit code 2) | `build` not run yet or empty scope | run `build`, check `include_ext`/ignore patterns |
| `FEHLER: Konfiguration fehlerhaft` | `wikitila.toml` is not valid TOML | fix line/column from the message |
| `Hinweis: Authority-Register …` | register unreadable or entry invalid | check JSON and field types (see docs/authority-register.en.md) |
