# Status

**Stand:** 2026-11-15 · **Version:** 0.2.0 (Branch `fix/review-2026-11-15`, noch nicht veröffentlicht)

## Gates

| Gate | Wert |
|---|---|
| Unit-Tests | ✅ 32/32 |
| Demo-Katalog (`examples/demo-corpus`) | ✅ R@10 1,00 · MRR 1,000 |
| Referenz-Vault (Messung 2026-11-14) | R@10 1,00 ✅ · MRR 0,785 ⚠️ (Ziel 0,80) |
| Build 10.000 Dateien (synthetisch) | ✅ 3,2 s (vorher 65,5 s) |

## Zuletzt erledigt

- Review 2026-11-15 umgesetzt (F1 bis F13), siehe [plans/2026-11-15-review-fixes.md](plans/2026-11-15-review-fixes.md).
- PM-Struktur, Memory, CI und Repo-Vorlagen angelegt.

## Offen / nächster Schritt

1. ⏳ **B-001:** Veröffentlichung auf GitHub (Repo anlegen, Sichtbarkeit klären, Branch pushen, PR, Merge). Freigabe durch den Owner nötig.
2. ⏳ **B-010:** MRR auf ≥ 0,80 heben (Messung nur am Owner-Vault, Analyse der verfehlten Ränge).
3. ⏳ **B-011:** Link-Graph inkrementell bauen (inkrementeller Build bei 10.000 Dateien: 1,9 s, dominiert vom kompletten Link-Neuaufbau).

## Risiken

- ⚠️ Bestehende Installationen mit `.sbs/index.db` (aus der alten Vorlage): Prüfen, ob `.sbs/` dort in der `.gitignore` steht, oder auf `.wikitila/` umstellen (B-002).
