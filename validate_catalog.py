#!/usr/bin/env python3
"""Katalog-Validierung für den Second-Brain-Stack (Messwerkzeug, kein Laufzeitcode).

Misst den golden_catalog_*.jsonl auf drei Ebenen, die der reine `wikitila.py eval`
nicht abdeckt:

  1. Datei-Recall     – steht eine erwartete Datei unter den Top-k? (wie `eval`)
  2. Passagen-Präsenz – enthält der ausgegebene Snippet den antworttragenden Beleg?
  3. Negativ/Coverage – wird bei fehlendem Wissen abgewiesen? Sind Nicht-Markdown-
                        Dateien überhaupt indexiert?

Der Katalog erweitert das Golden-Set-Schema um:
  kind     positiv | authority | coverage | negativ
  passage  Liste antworttragender Teilstrings (müssen im Snippet stehen)
  answer   erwarteter Antwortstatus: belegt | widerspruechlich |
           belegt_gueltigkeit_unbestaetigt | nicht_belegt

Aufruf:
  python3 validate_catalog.py --root <vault> --catalog <golden_catalog.jsonl> [-k 10] [--gate]

--gate (für CI): Exit 1, wenn ein positiv/authority-Fall nicht unter den Top-k steht,
eine coverage-Datei fehlt, ein positiv/authority-Fall einen anderen Antwortstatus als
`answer` liefert oder ein Negativfall ohne Abstention-Signal bleibt. Dass Negativfälle
trotzdem einen Treffer liefern, ist kein Gate-Kriterium (ADR-005: Antwort-Tor bleibt Signal).
Bedien- und Katalogfehler: Exit 2.
"""

from __future__ import annotations

import argparse, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikitila as W


def rank_of(res: list[dict], expect: set[str]) -> int | None:
    for i, h in enumerate(res, 1):
        if h["path"] in expect:
            return i
    return None


KINDS = ("positiv", "authority", "coverage", "negativ")
STATUS = {"belegt", "widersprüchlich", "belegt_gueltigkeit_unbestaetigt", "nicht_belegt"}


def norm_status(s: str) -> str:
    """Katalog darf ASCII schreiben (widerspruechlich); die Ausgabe nutzt widersprüchlich."""
    return "widersprüchlich" if s == "widerspruechlich" else s


def load_catalog(path: str) -> list[dict]:
    gold = W.load_jsonl(path, {"q": str, "kind": str, "expect": list})
    for i, g in enumerate(gold, 1):
        if g["kind"] not in KINDS:
            raise W.WikitilaError(f"{path}: Fall {i} ({g['q'][:40]!r}): kind {g['kind']!r} unbekannt "
                                  f"(erlaubt: {', '.join(KINDS)})")
        if "passage" in g and not (isinstance(g["passage"], list) and all(isinstance(x, str) for x in g["passage"])):
            raise W.WikitilaError(f"{path}: Fall {i}: passage muss eine Liste von Texten sein")
        if g.get("answer") is not None and norm_status(g["answer"]) not in STATUS:
            raise W.WikitilaError(f"{path}: Fall {i}: answer {g['answer']!r} unbekannt (erlaubt: {', '.join(sorted(STATUS))})")
    return gold


def main() -> None:
    ap = argparse.ArgumentParser(description="Katalog-Validierung (Recall, Passage, Coverage, Negativ, Antwortstatus)")
    ap.add_argument("--root", default=".")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("-k", type=W.positive_int, default=10)
    ap.add_argument("--gate", action="store_true", help="Exit 1 bei verletztem Abnahmekriterium (CI)")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    try:
        if not root.is_dir():
            raise W.WikitilaError(f"Ordner nicht gefunden: {root}")
        cfg = W.load_cfg(root)
        gold = load_catalog(a.catalog)
        c = W.require_index(root, cfg)
    except W.WikitilaError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        sys.exit(2)
    try:
        failed = run(c, cfg, gold, a)
    finally:
        c.close()
    if a.gate and failed:
        print(f"\nGATE: nicht bestanden ({'; '.join(failed)})")
        sys.exit(1)
    if a.gate:
        print("\nGATE: bestanden")


def run(c, cfg, gold: list[dict], a) -> list[str]:
    """Misst den Katalog und druckt den Bericht. Rückgabe: verletzte Gate-Kriterien."""
    indexed = {p for (p,) in c.execute("select path from files")}

    # --- Teilmenge für Datei-Recall: indexierbare Fälle mit erwarteter Datei ---
    indexable = [g for g in gold if g["kind"] in ("positiv", "authority") and g["expect"]]

    ranks, lat, miss_detail = [], [], []
    passage_total = passage_top1 = passage_full1 = passage_topk = 0
    passage_fail = []
    cov_total = cov_indexed = 0
    cov_missing = []
    neg_total = neg_nonempty = 0
    pos_false_abstain = 0
    neg_signal = 0
    neg_coverage_partial = 0
    neg_detail = []
    neg_nosignal = []
    ans_total = ans_ok = 0
    ans_fail = []

    for g in gold:
        t0 = time.time()
        full = W.search(c, cfg, g["q"], a.k)
        res = full["results"]
        lat.append(time.time() - t0)

        if g.get("answer") and g["kind"] != "coverage":
            ans_total += 1
            got = full.get("answer_status")
            if got == norm_status(g["answer"]):
                ans_ok += 1
            else:
                ans_fail.append((g["q"], g["kind"], norm_status(g["answer"]), got))

        if g["kind"] in ("positiv", "authority"):
            expect = set(g["expect"])
            rk = rank_of(res, expect)
            ranks.append(rk)
            if not rk:
                miss_detail.append((g["q"], g["expect"]))
            if full.get("answer_status") == "nicht_belegt":
                pos_false_abstain += 1
            # Passagen-Präsenz
            if g.get("passage"):
                passage_total += 1
                snip1 = res[0]["snippet"] if res else ""
                allsnip = " ".join(h["snippet"] for h in res)
                full1 = ""
                if res and res[0].get("passages"):
                    full1 = " ".join(p["heading"] + " " + p["body"] for p in res[0]["passages"])
                if any(kw in snip1 for kw in g["passage"]):
                    passage_top1 += 1
                if any(kw in full1 for kw in g["passage"]):
                    passage_full1 += 1
                if any(kw in allsnip for kw in g["passage"]):
                    passage_topk += 1
                else:
                    passage_fail.append((g["q"], g["passage"], res[0]["path"] if res else "-"))

        elif g["kind"] == "coverage":
            cov_total += 1
            for p in g["expect"]:
                if p in indexed:
                    cov_indexed += 1
                else:
                    cov_missing.append(p)

        elif g["kind"] == "negativ":
            neg_total += 1
            if full.get("answer_status") != "nicht_belegt":
                neg_nonempty += 1
                neg_detail.append((g["q"], res[0]["path"] if res else "-", (res[0]["snippet"][:70] if res else "")))
            sig = bool(full.get("unmatched_terms") or full.get("top1_missing_terms"))
            if sig:
                neg_signal += 1
            if full.get("term_coverage", 1.0) < 1.0:
                neg_coverage_partial += 1
            if not sig and full.get("term_coverage", 1.0) >= 1.0 and full.get("answer_status") != "nicht_belegt":
                neg_nosignal.append(g["q"])

    # --- Auswertung ---
    n = len(ranks)
    rec = lambda k: sum(1 for x in ranks if x and x <= k) / n if n else 0.0
    mrr = sum(1 / x for x in ranks if x) / n if n else 0.0
    # Latenz über alle Katalogfälle (nicht nur die Recall-Teilmenge), Index nach Nearest-Rank
    ms = lambda p: W.pct(lat, p) * 1000

    print(f"Katalog: {len(gold)} Fälle "
          f"({sum(1 for g in gold if g['kind']=='positiv')} positiv, "
          f"{sum(1 for g in gold if g['kind']=='authority')} authority, "
          f"{sum(1 for g in gold if g['kind']=='coverage')} coverage, "
          f"{sum(1 for g in gold if g['kind']=='negativ')} negativ)")
    print(f"Index: {len(indexed)} Dateien\n")

    print("== 1. Datei-Recall (positiv + authority, n=%d) ==" % n)
    print(f"R@1 {rec(1):.2f}  R@3 {rec(3):.2f}  R@5 {rec(5):.2f}  R@10 {rec(10):.2f}  "
          f"MRR {mrr:.3f}  p50 {ms(0.50):.0f}ms  p95 {ms(0.95):.0f}ms")
    if miss_detail:
        print("  verfehlt:")
        for q, ex in miss_detail:
            print(f"    - {q[:80]}  erwartet: {ex}")

    print("\n== 2. Passagen-Präsenz (positiv + authority, mit passage-Assertion) ==")
    print(f"Top-1-Snippet (260 Zeichen): {passage_top1}/{passage_total} "
          f"({passage_top1/max(1,passage_total):.0%})  |  Top-1-Datei, volle Passagen: "
          f"{passage_full1}/{passage_total} ({passage_full1/max(1,passage_total):.0%})  |  "
          f"irgendein Top-{a.k}-Snippet: {passage_topk}/{passage_total} ({passage_topk/max(1,passage_total):.0%})")
    if passage_fail:
        print(f"  Beleg fehlt in allen Top-{a.k}-Snippets:")
        for q, kw, top in passage_fail:
            print(f"    - {q[:70]}  benötigt {kw}  (top1={top})")

    print("\n== 3. Coverage (erwartete Nicht-Markdown-Datei indexiert?) ==")
    print(f"{cov_indexed}/{cov_total} erwartete Dateien im Index")
    if cov_missing:
        print("  nicht indexiert (Erweiterung fehlt in include_ext):")
        for p in cov_missing:
            print(f"    - {p}")

    print("\n== 4. Negativ (Abstention erwartet, answer_status = nicht_belegt) ==")
    fp = neg_nonempty / max(1, neg_total)
    print(f"Falsch-positive (keine Abstention): {neg_nonempty}/{neg_total} ({fp:.0%})")
    print(f"Abstention-Signal vorhanden (unmatched_terms/top1_missing_terms): {neg_signal}/{neg_total}")
    print(f"Coverage-Note < 1,0 (term_coverage/uncovered): {neg_coverage_partial}/{neg_total}")
    if neg_detail:
        print("  Beispiele (Frage -> gelieferter Treffer):")
        for q, p, s in neg_detail:
            print(f"    - {q[:60]} -> {p}  «{s}»")

    print("\n== 5. Antwortstatus (Feld answer, positiv/authority/negativ) ==")
    print(f"{ans_ok}/{ans_total} wie erwartet")
    for q, kind, exp, got in ans_fail:
        print(f"    - [{kind}] {q[:60]}  erwartet {exp}, geliefert {got}")

    failed = []
    if any(not r for r in ranks):
        failed.append(f"Datei-Recall@{a.k} < 1,00")
    if cov_missing:
        failed.append(f"{len(cov_missing)} coverage-Datei(en) nicht im Index")
    pos_ans_fail = [f for f in ans_fail if f[1] in ("positiv", "authority")]
    if pos_ans_fail:
        failed.append(f"{len(pos_ans_fail)} positiv/authority-Fall/Fälle mit falschem Antwortstatus")
    if neg_nosignal:
        failed.append(f"{len(neg_nosignal)} Negativfall/-fälle ohne Abstention-Signal")

    print("\n== Einordnung ==")
    print("Datei-Recall ist KEIN Nachweis für Antwortqualität. Passagen-Präsenz, "
          "Negativ-Abstention und Coverage sind die eigentlichen Vertrauensmetriken.")
    return failed


if __name__ == "__main__":
    main()
