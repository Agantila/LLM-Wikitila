# Operations and Maintenance (English)

## Rhythm

| When | What | Duration |
|---|---|---|
| after each work session with new/changed files | `python3 wikitila.py --root <folder> build` (incremental) | seconds |
| monthly | `python3 wikitila.py --root <folder> manifest` — check coverage and exclusions | under 1 minute |
| before reliable answers / in hooks | `python3 wikitila.py --root <folder> check` — detect drift | under 1 minute |
| after work sessions with new files | `python3 wikitila.py --root <folder> lint --all` — write side: frontmatter convention (fix violations, notes optional) | seconds |
| after larger changes or weekly | Graph: `wikitila_graph.py run` (changed files only), then `build`, then `wikitila.py build` | minutes |

**After upgrading LLM-Wikitila**, the first `build` rebuilds the index once from scratch if the index format changed (message `Indexformat … → …: Vollneubau`, ADR-006). `status` and `check` report an outdated format beforehand. If you use embeddings, run `embed` again afterwards.

**Exit codes:** 0 = ok · 1 = `lint` found violations (or `validate_catalog.py --gate` failed) · 2 = usage, configuration, or environment error (message `FEHLER: …`, no traceback) · 130 = interrupted. `check` deliberately stays 0 on drift and reports it in the text.

No service, no autostart needed. For automation, a cron entry or git hook that runs `build` suffices; the graph run does not belong in a hook (GPU, long runtime).

## How agents use it

1. `python3 wikitila.py --root <folder> search "<question>" -k 5 --json` returns file, heading, passages, and reason.
2. Open only the named files — the original passage is the quote.
3. Connections: `graphify path "A" "B"` and `graphify explain "X"` on `graphify-out/graph.json` (only if the graph was built).
4. Read the flags: `überholt durch …` → read the newer file; `kanonisch` → authoritative source; `veraltet`/`Gültigkeit nicht bestätigt` → factual validity open.
5. Read `Antwortstatus`: `nicht_belegt` → no reliable answer; `widersprüchlich` → multiple values with resolution; `belegt_gueltigkeit_unbestaetigt` → evidence present, validity open. The notes `Begriffe ohne Treffer …`, `Begriffe nicht im Top-1-Ergebnis …`, and `Begriffe ohne ko-lokalen Beleg …` (`term_coverage`/`uncovered`) show where the agent must abstain itself. Before the actual search, `wikitila.py coverage "question"` checks coverage cheaply.

## Conflict and freshness resolution

**Freshness:** time-dependent facts (prices, legal status, metrics) get `stale_after` + `verified_at` in the register. Exceeded → answer status "evidence found, current validity not confirmed". A fresh index only proves that current files were read in — never factual validity.

**Conflict:** show both values with source, date, and authority; resolve via the register (`supersedes`/`superseded_by` + owner's `authority_confirmed`). Conflicts are never silently resolved by majority, graph, or model.

## Error catalog

| Symptom | Cause | Fix |
|---|---|---|
| `no such module: fts5` / `kein sqlite3-Modul` | Python without SQLite/FTS5 (e.g. self-built pyenv) | another Python ≥ 3.11, e.g. `PYTHON=/usr/bin/python3` |
| `Konfiguration fehlerhaft: … erwartet …` | wrong type in `wikitila.toml` (e.g. `require = "title"` instead of a list) | set the value as in `config.example.toml` |
| `Warnung: unbekannte Sektion/unbekannter Schlüssel` | typo in `wikitila.toml` | check spelling — otherwise the value has no effect |
| `SQLite: file is not a database` / `malformed` | index corrupted | delete `.wikitila/`, `build` |
| `database is locked` after 30 s | another `build` is still running | wait, then retry |
| `Register-Pfad nicht im Index` (status) | typo, file moved or ignored | fix the path in the register |
| `build` finds 0 files | Wrong `--root` / `.graphifyignore` excludes everything | Check paths |
| Hits from deleted files | Stale index | `build` |
| Snippets show passwords | `mask_secrets` off | `[privacy] mask_secrets = true` |
| Entity mappings are 0 | `graph.json` not rebuilt | Run `wikitila_graph.py build`, then `wikitila.py build` |
| Graph run aborts | Ollama stopped or model missing | `ollama list`, restart the run (resumes) |

## Security

- The index (`.wikitila/index.db`) contains full text (unmasked) — whoever receives it receives its contents. `.wikitila/` belongs in the target folder's `.gitignore`; `install.sh` adds it there if the folder is a Git repo.
- Masking applies to all text fields of the output: passages, headings, titles, entity labels in `why`.
- Symlinks pointing outside the folder (or nowhere) are not indexed and are counted as `symlink_outside_root` in the manifest. Symlinks inside the folder remain allowed.
- Files over 600,000 bytes are skipped (checked before reading; `build`, `check`, and `manifest` count the same way).
- Read commands (`search`, `coverage`, `eval`, `embed`, `status`) never create an index, and a non-existent `--root` is never created: if it is missing or empty, the call exits with code 2 instead of a seemingly valid `nicht_belegt`.
- Snippets mask keys and passwords (`mask_secrets`, on by default); the files themselves remain findable.
- Everything runs locally, nothing goes to the cloud.
