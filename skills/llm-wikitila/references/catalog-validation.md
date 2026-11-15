# Catalog validation with LLM-Wikitila

The unit of acceptance is the **evidence-backed statement**, not the found file. File recall
alone is not enough as proof of trust.

## Three levels, one measurement tool

`validate_catalog.py` measures an extended catalog on three levels:

1. **File recall** — is the expected file among the top-k?
2. **Passage presence** — does the top-1 result (full passages) carry the answer-bearing
   evidence (field `passage` = list of exact substrings)?
3. **Negatives / coverage** — does the search abstain when knowledge is missing? Are
   non-Markdown files listed as exclusions?

## Catalog schema (JSONL, one question per line)

```json
{"q":"…", "type":"stichwort|paraphrase|aktueller-stand",
 "kind":"positiv|authority|coverage|negativ",
 "expect":["relative/path.md"], "passage":["exact","substring"],
 "answer":"belegt|widerspruechlich|belegt_gueltigkeit_unbestaetigt|nicht_belegt"}
```

- `kind=authority`: the expected file is the **currently valid** source; `passage`
  carries the current value. Failure = freshness/supersession problem.
- `kind=coverage`: `expect` points to a non-Markdown file. It is expected to be absent
  from the index (scope = Markdown) — the finding documents the exclusion.
- `kind=negativ`: `expect` empty, `answer=nicht_belegt`. A non-empty top-1 hit is a
  false positive; the signals `unmatched_terms`/`top1_missing_terms` are the basis for
  the agent's abstention.

## Invocation

```bash
cd <target-folder>
python3 <path>/validate_catalog.py --root . --catalog golden_catalog.jsonl
```

## Reference values (AGANTILA vault, 50 cases)

| Level | Result |
|---|---|
| File recall (positive+authority, n=36) | R@10 1.00, MRR 0.785 |
| Passage presence (top-1, full passages) | 45% |
| Abstention signal (negatives) | 8/8 |

## Rules when extending

- The catalog is the acceptance test and grows with new insights.
- Add new cases only with verified, exact paths and passage substrings.
- Update the results in the docs (README, validation document).
- File recall is not proof of answer quality — measure passages and status separately.
