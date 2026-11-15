# Status

**Stand:** 2026-11-15 · **Version:** 0.2.0 (Tag `v0.2.0` auf `main`, lokal; noch nicht auf GitHub)

**Einsatz:** Erster Produktiveinsatz im Referenz-Vault des Owners über einen Release-Worktree (siehe [Einsatz](#einsatz))

## Gates

| Gate | Wert |
|---|---|
| Unit-Tests | ✅ 32/32 |
| Demo-Katalog (`examples/demo-corpus`) | ✅ R@10 1,00 · MRR 1,000 |
| Referenz-Vault (Owner-Messung 2026-11-15, v0.2.0, 1.459 Dateien) | R@10 1,00 ✅ · MRR 0,776 ⚠️ (Ziel 0,80) · Abstention-Signal 8/8 |
| Build 10.000 Dateien (synthetisch) | ✅ 3,2 s (vorher 65,5 s) |

## Zuletzt erledigt

- Review 2026-11-15 umgesetzt (F1 bis F13), siehe [plans/2026-11-15-review-fixes.md](plans/2026-11-15-review-fixes.md).
- PM-Struktur, Memory, CI und Repo-Vorlagen angelegt.
- Produktiveinsatz umgestellt: alte Werkzeug-Kopie archiviert, der Referenz-Vault läuft aus dem Release `v0.2.0` (B-002 erledigt).

## Offen / nächster Schritt

1. ⏳ **B-001:** Veröffentlichung auf GitHub (Repo anlegen, Sichtbarkeit klären, Branch pushen, PR, Merge). Freigabe durch den Owner nötig.
2. ⏳ **B-010:** MRR auf ≥ 0,80 heben (Messung nur am Owner-Vault, Analyse der verfehlten Ränge).
3. ⏳ **B-011:** Link-Graph inkrementell bauen (inkrementeller Build bei 10.000 Dateien: 1,9 s, dominiert vom kompletten Link-Neuaufbau).

## Einsatz

| Instanz | Werkzeug | Konfiguration | Stand |
|---|---|---|---|
| Referenz-Vault des Owners | Release-Worktree (`v0.2.0`), Aufruf über Wrapper-Skript | `wikitila.toml`, Register und privater Katalog im Vault | ✅ 2026-11-15, Abnahme R@10 1,00 |

Release-Wechsel: `git -C <release-worktree> checkout vX.Y.Z`, dann im Vault `build`, `check` und die Katalogmessung (macht der Owner).

## Risiken

- ⚠️ Der Release-Worktree verweist mit absolutem Pfad auf dieses Repo. Wer das Repo verschiebt, muss `git worktree repair` ausführen.
