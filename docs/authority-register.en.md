# Authority Register (English)

The register answers **"which file is authoritative for this topic"** and **"is it still valid"**. File: `authority_register.json` in the target folder. Without a register entry there is no canonical effect — the search only returns BM25 relevance.

## Schema (per entry)

| Field | Meaning | Required |
|---|---|---|
| `id` | stable key | yes |
| `scope` | Topic/term covered by the entry (also used as a search alias) | yes |
| `canonical` | authoritative file (path relative to the target folder) | yes |
| `authority` | `canonical` · `working` · `reference` | yes |
| `owner` | human responsible | yes |
| `verified_at` | last human confirmation (ISO date) | yes |
| `stale_after` | review date for time-dependent facts | if time-dependent |
| `supersedes` | superseded files (list) | if any |
| `superseded_by` | successor (path) | if any |
| `status` | frontmatter `status` of the canonical file | informational |
| `authority_confirmed` | `true` = owner confirmed; `false` = proposal | yes |
| `value` | exact substrings of the canonical value (to find the answer-bearing passage) | recommended on supersession |
| `note` | evidence, value, rationale | recommended |

## Example

```json
{
  "id": "product-prices",
  "scope": "Prices of the product line",
  "canonical": "docs/prices_current.md",
  "authority": "canonical",
  "owner": "Jane Doe",
  "verified_at": "2026-01-15",
  "stale_after": "2026-12-31",
  "supersedes": ["docs/prices_old.md"],
  "superseded_by": null,
  "status": "accepted",
  "authority_confirmed": true,
  "value": ["549"],
  "note": "Currently 549 EUR; old version superseded."
}
```

**Effect:** Queries that hit `prices_old.md` are redirected to `prices_current.md` ("überholt durch"), the successor gets `kanonisch` and the passage containing `549`. When a query matches a register topic (via `scope`), the canonical file is surfaced — this resolves terminology mismatches ("search architecture" vs. a file named "search layer").

## Agent rules

1. Before any reliable answer on a register topic, read the entry and use the `canonical` file as the source.
2. Never present a superseded file as the current state.
3. `stale_after` exceeded or `status: proposed` without confirmation → "evidence found, current validity not confirmed".
4. `authority_confirmed: false` → proposal, no canonical effect.
5. Conflict found → name both values with sources and add a proposal to the register.

## Learning and update procedure

1. **Recognize:** a recurring, decision-relevant question with several sources or no canonical source; or a conflict/outdated state is noticed.
2. **Propose:** add an entry with `authority_confirmed: false` and a `note` with evidence.
3. **Confirm:** **only the human owner** sets `authority_confirmed: true`, fills `verified_at`, and decides `authority`, `canonical`, `supersedes`.
4. **Resolve:** also update the file frontmatter (`supersedes`/`superseded_by`).
5. **Review:** monthly, check all `stale_after` dates, present unconfirmed entries to the owner, remove dead `canonical` paths.
