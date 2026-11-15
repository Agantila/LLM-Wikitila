# Operations and Maintenance (English)

## Rhythm

| When | What | Duration |
|---|---|---|
| after each work session with new/changed files | `python3 wikitila.py --root <folder> build` (incremental) | seconds |
| monthly | `python3 wikitila.py --root <folder> manifest` — check coverage and exclusions | under 1 minute |
| before reliable answers / in hooks | `python3 wikitila.py --root <folder> check` — detect drift | under 1 minute |
| after larger changes or weekly | Graph: `wikitila_graph.py run` (changed files only), then `build`, then `wikitila.py build` | minutes |

No service, no autostart needed. For automation, a cron entry or git hook that runs `build` suffices; the graph run does not belong in a hook (GPU, long runtime).

## How agents use it

1. `python3 wikitila.py --root <folder> search "<question>" -k 5 --json` returns file, heading, passages, and reason.
2. Open only the named files — the original passage is the quote.
3. Connections: `graphify path "A" "B"` and `graphify explain "X"` on `graphify-out/graph.json` (only if the graph was built).
4. Read the flags: `überholt durch …` → read the newer file; `kanonisch` → authoritative source; `veraltet`/`Gültigkeit nicht bestätigt` → factual validity open.
5. Read `Antwortstatus`: `nicht_belegt` → no reliable answer; `widersprüchlich` → multiple values with resolution; `belegt_gueltigkeit_unbestaetigt` → evidence present, validity open. The notes `Begriffe ohne Treffer …` and `Begriffe nicht im Top-1-Ergebnis …` show where the agent must abstain itself.

## Conflict and freshness resolution

**Freshness:** time-dependent facts (prices, legal status, metrics) get `stale_after` + `verified_at` in the register. Exceeded → answer status "evidence found, current validity not confirmed". A fresh index only proves that current files were read in — never factual validity.

**Conflict:** show both values with source, date, and authority; resolve via the register (`supersedes`/`superseded_by` + owner's `authority_confirmed`). Conflicts are never silently resolved by majority, graph, or model.

## Error catalog

| Symptom | Cause | Fix |
|---|---|---|
| `no such module: fts5` | Python without FTS5 | Python ≥ 3.11 |
| `build` finds 0 files | Wrong `--root` / `.graphifyignore` excludes everything | Check paths |
| Hits from deleted files | Stale index | `build` |
| Snippets show passwords | `mask_secrets` off | `[privacy] mask_secrets = true` |
| Entity mappings are 0 | `graph.json` not rebuilt | Run `wikitila_graph.py build`, then `wikitila.py build` |
| Graph run aborts | Ollama stopped or model missing | `ollama list`, restart the run (resumes) |

## Security

- The index (`.wikitila/index.db`) contains full text — whoever receives it receives its contents. It is therefore in `.gitignore`.
- Snippets mask keys and passwords (`mask_secrets`, on by default); the files themselves remain findable.
- Everything runs locally, nothing goes to the cloud.
