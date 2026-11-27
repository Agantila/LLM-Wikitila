# Validation (English)

Acceptance runs on a **self-authored question catalog** (JSONL), measured with `validate_catalog.py` on three levels. A separate external golden set is not required — the catalog is the acceptance test and grows with new insights.

## Catalog schema (one question per line)

```json
{"q":"What is the current price?","type":"aktueller-stand","kind":"authority",
 "expect":["docs/prices_current.md"],"passage":["549"],"answer":"belegt"}
```

| Field | Meaning |
|---|---|
| `q` | the question |
| `type` | `stichwort` · `paraphrase` · `aktueller-stand` |
| `kind` | `positiv` · `authority` · `coverage` · `negativ` |
| `expect` | expected answer files (paths relative to the folder) |
| `passage` | exact substrings that must appear in the returned passage |
| `answer` | expected status: `belegt` · `widersprüchlich` (ASCII `widerspruechlich` also accepted) · `belegt_gueltigkeit_unbestaetigt` · `nicht_belegt`. For `kind=authority` with a superseded version in the results, `widersprüchlich` is correct (both values, resolution visible) |

- `kind=authority`: `expect` is the **currently valid** source, `passage` carries the current value.
- `kind=coverage`: `expect` points to a non-Markdown file — expected to be listed as an exclusion (coverage decision).
- `kind=negativ`: `expect` empty, `answer=nicht_belegt`.

## Measurement

```bash
python3 validate_catalog.py --root . --catalog golden_catalog.jsonl [--gate]
```

Levels:

1. **File recall** — is an expected file among the top-k? (R@1/R@3/R@5/R@10, MRR, latency)
2. **Passage presence** — does the top-1 result (full passages) carry the answer-bearing evidence?
3. **Coverage & negatives** — are non-Markdown files listed as exclusions? Does the search abstain when knowledge is missing (abstention signal)?
4. **Answer status** — does the search return the status expected in the `answer` field?

**`--gate` (CI, acceptance):** exit 1 if a positiv/authority case is not among the top-k, a coverage file is missing, a positiv/authority case returns a different answer status, or a negative case has **no** abstention signal. Negative cases still returning a hit is not a gate criterion: the answer gate remains a signal and the agent makes the abstention decision (ADR-005). A malformed catalog (not JSON, required field missing, unknown `kind`) exits with code 2 and the line number.

`wikitila.py eval golden.jsonl` measures file recall only and skips cases without `expect` (negative cases); use `validate_catalog.py` for all levels.

Additionally, `validate_catalog.py` measures the **coverage grade** (`term_coverage < 1.0`) for `kind=negativ`. The same grade is returned by search, and a cheap pre-flight checks it without ranking:

```bash
python3 wikitila.py --root . coverage "What safe zones apply to Pinterest ads?"
# -> Term coverage: 0.60 · Not co-located: pinterest
```

The grade is deterministic (co-location of query terms in the same chunk) and does not replace semantics — it makes the agent's abstention verifiable.

## Reference measurements (AGANTILA vault, 50-question catalog)

| Level | Value |
|---|---|
| File recall | R@10 **1.00**, MRR 0.785, p95 ~35 ms |
| Passage presence (top-1, full passages) | 45% |
| Abstention signal on negative cases | 8/8 |
| Unit tests | 18/18 (at measurement time; currently 79/79) |

**Target check:** R@10 meets the target ≥ 0.95. MRR 0.785 is **below** the target 0.80 — open backlog item (`pm/BACKLOG.md`, B-010).

**Reproducibility:** The reference values come from the private vault and cannot be re-measured from the repo. The tool chain itself can be checked with the demo corpus (also runs in CI):

```bash
python3 wikitila.py --root examples/demo-corpus build
python3 validate_catalog.py --root examples/demo-corpus --catalog golden_catalog.example.jsonl --gate
python3 wikitila.py --root examples/demo-corpus lint --all      # demo corpus meets the write contract
```

## Measurement limits (honest)

- A self-authored catalog is biased by question selection and known content; it grows with new insights.
- Near-topic negatives ("safe zones for Pinterest") cannot be rejected lexically without semantics — their keywords often exist in the corpus themselves, and models measured worse. The signals `unmatched_terms`/`top1_missing_terms` give the agent the discriminator; the agent makes the abstention.
- File recall is **not** proof of answer quality — passage and status are measured separately.
- If you write negative-test keywords ("Pinterest", "Snapchat" …) into an indexed measurement doc, they are "present" in the corpus from then on, and lexical abstention can no longer detect them as missing.
