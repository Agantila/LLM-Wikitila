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
| `answer` | expected status: `belegt` · `widersprüchlich` · `belegt_gueltigkeit_unbestaetigt` · `nicht_belegt` |

- `kind=authority`: `expect` is the **currently valid** source, `passage` carries the current value.
- `kind=coverage`: `expect` points to a non-Markdown file — expected to be listed as an exclusion (coverage decision).
- `kind=negativ`: `expect` empty, `answer=nicht_belegt`.

## Measurement

```bash
python3 validate_catalog.py --root . --catalog golden_catalog.jsonl
```

Three levels:

1. **File recall** — is an expected file among the top-k? (R@1/R@3/R@5/R@10, MRR, latency)
2. **Passage presence** — does the top-1 result (full passages) carry the answer-bearing evidence?
3. **Coverage & negatives** — are non-Markdown files listed as exclusions? Does the search abstain when knowledge is missing (abstention signal)?

## Reference measurements (AGANTILA vault, 50-question catalog)

| Level | Value |
|---|---|
| File recall | R@10 **1.00**, MRR 0.785, p95 ~35 ms |
| Passage presence (top-1, full passages) | 45% |
| Abstention signal on negative cases | 8/8 |
| Unit tests | 18/18 (at measurement time; currently 32/32) |

**Target check:** R@10 meets the target ≥ 0.95. MRR 0.785 is **below** the target 0.80 — open backlog item (`pm/BACKLOG.md`, B-010).

**Reproducibility:** The reference values come from the private vault and cannot be re-measured from the repo. The tool chain itself can be checked with the demo corpus (also runs in CI):

```bash
python3 wikitila.py --root examples/demo-corpus build
python3 validate_catalog.py --root examples/demo-corpus --catalog golden_catalog.example.jsonl
```

## Measurement limits (honest)

- A self-authored catalog is biased by question selection and known content; it grows with new insights.
- Near-topic negatives ("safe zones for Pinterest") cannot be rejected lexically without semantics — their keywords often exist in the corpus themselves, and models measured worse. The signals `unmatched_terms`/`top1_missing_terms` give the agent the discriminator; the agent makes the abstention.
- File recall is **not** proof of answer quality — passage and status are measured separately.
- If you write negative-test keywords ("Pinterest", "Snapchat" …) into an indexed measurement doc, they are "present" in the corpus from then on, and lexical abstention can no longer detect them as missing.
