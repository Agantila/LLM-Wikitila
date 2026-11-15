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
  python3 validate_catalog.py --root <vault> --catalog <golden_catalog.jsonl> [-k 10]
"""

from __future__ import annotations

import argparse, json, math, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikitila as W


def rank_of(res: list[dict], expect: set[str]) -> int | None:
    for i, h in enumerate(res, 1):
        if h["path"] in expect:
            return i
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("-k", type=int, default=10)
    a = ap.parse_args()

    root = Path(a.root).resolve()
    try:
        cfg = W.load_cfg(root)
        c = W.require_index(root, cfg)
    except W.WikitilaError as e:
        sys.exit(f"FEHLER: {e}")
    indexed = {p for (p,) in c.execute("select path from files")}

    gold = [json.loads(l) for l in Path(a.catalog).read_text(encoding="utf-8").splitlines() if l.strip()]
    if not gold:
        sys.exit(f"FEHLER: Katalog {a.catalog} enthält keine Fälle.")

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
    neg_detail = []

    for g in gold:
        t0 = time.time()
        full = W.search(c, cfg, g["q"], a.k)
        res = full["results"]
        lat.append(time.time() - t0)

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
            if full.get("unmatched_terms") or full.get("top1_missing_terms"):
                neg_signal += 1

    # --- Auswertung ---
    n = len(ranks)
    rec = lambda k: sum(1 for x in ranks if x and x <= k) / n if n else 0.0
    mrr = sum(1 / x for x in ranks if x) / n if n else 0.0
    # Latenz über alle Katalogfälle (nicht nur die Recall-Teilmenge), Index nach Nearest-Rank
    sl = sorted(lat)
    ms = lambda p: sl[max(0, math.ceil(len(sl) * p) - 1)] * 1000 if sl else 0

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
        print("  Beleg fehlt im Top-1-Snippet:")
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
    if neg_detail:
        print("  Beispiele (Frage -> gelieferter Treffer):")
        for q, p, s in neg_detail:
            print(f"    - {q[:60]} -> {p}  «{s}»")

    print("\n== Einordnung ==")
    print("Datei-Recall ist KEIN Nachweis für Antwortqualität. Passagen-Präsenz, "
          "Negativ-Abstention und Coverage sind die eigentlichen Vertrauensmetriken.")


if __name__ == "__main__":
    main()
