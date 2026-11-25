# Status

**Stand:** 2026-11-25 · **Version:** 0.3.0 (vor Release, Code fertig auf `main`) · **Repo:** <https://github.com/Agantila/LLM-Wikitila>

**Einsatz:** Erster Produktiveinsatz im Referenz-Vault des Owners über einen Release-Worktree (siehe [Einsatz](#einsatz))

## Gates

| Gate | Wert |
|---|---|
| Unit-Tests | ✅ 39/39 (lokal Python 3.14.8) |
| GitHub-CI | ⏳ läuft nach Push auf Python 3.11, 3.12, 3.13 |
| Demo-Katalog (`examples/demo-corpus`) | ✅ R@10 1,00 · MRR 1,000 |
| Referenz-Vault (Owner-Messung 2026-11-15, v0.2.0, 1.459 Dateien) | R@10 1,00 ✅ · MRR 0,776 ⚠️ (Ziel 0,80) · Abstention-Signal 8/8 |
| Build 10.000 Dateien (synthetisch) | ✅ 3,2 s (vorher 65,5 s) |

## Zuletzt erledigt

- Suchsicht und Qualität umgesetzt (Plan 2026-11-25): `term_coverage`/`uncovered`/`trace` in der Suche, neuer `coverage`-Befehl, Register-Metadaten, Authority-Wert-Chunks, Frontmatter-Status indexiert, Chunk-Aggregation im Ranking, kurze Abschnitte indexiert (B-018), ADR-005 (Coverage-Note bleibt Signal). 39 Unit-Tests grün, Demo-Katalog MRR 1,000.
- Repository veröffentlicht: `Agantila/LLM-Wikitila` ist öffentlich, `main` und Tag `v0.2.0` sind gepusht, CI auf Python 3.11 bis 3.13 grün (B-001 erledigt).
- Lokale Veröffentlichungsabnahme erneut bestätigt: Tests, Demo-Katalog und Installer-Rauchtest grün; `gh`-Konto Agantila vorhanden. Auf Owner-Entscheidung wurde keine externe Aktion ausgeführt.
- Review 2026-11-15 umgesetzt (F1 bis F13), siehe [plans/2026-11-15-review-fixes.md](plans/2026-11-15-review-fixes.md).
- PM-Struktur, Memory, CI und Repo-Vorlagen angelegt.
- Veröffentlichung vorbereitet: Historie auf die Noreply-Adresse von Agantila umgeschrieben, interne Vault-Details neutralisiert, Tag `v0.2.0` neu gesetzt, Skripte ausführbar.
- Produktiveinsatz umgestellt: alte Werkzeug-Kopie archiviert, der Referenz-Vault läuft aus dem Release `v0.2.0` (B-002 erledigt).

## Offen / nächster Schritt

1. 🟡 **Release 0.3.0:** committen, Tag `v0.3.0` setzen, Release-Worktree umstellen, Vault `build`.
2. 🟡 **B-010/B-015/B-016:** Owner-Messung am Vault (MRR ≥ 0,80, Passagen-Präsenz, Coverage-Note auf den 8 Negativ-Fällen) steht aus — ADR-005: Antwort-Tor bleibt Signal-only.
3. ⏳ **B-011:** Link-Graph inkrementell bauen (inkrementeller Build bei 10.000 Dateien: 1,9 s, dominiert vom kompletten Link-Neuaufbau).
4. ⏳ **B-013:** Release-Signierung (signierte Tags) prüfen. Actions sind bereits auf Commit-SHA gepinnt und werden per Dependabot aktualisiert.

## Einsatz

| Instanz | Werkzeug | Konfiguration | Stand |
|---|---|---|---|
| Referenz-Vault des Owners | Release-Worktree (`v0.2.0`), Aufruf über Wrapper-Skript | `wikitila.toml`, Register und privater Katalog im Vault | ✅ 2026-11-15, Abnahme R@10 1,00 |

Release-Wechsel: `git -C <release-worktree> checkout vX.Y.Z`, dann im Vault `build`, `check` und die Katalogmessung (macht der Owner).

## Risiken

- ⚠️ Der Release-Worktree verweist mit absolutem Pfad auf dieses Repo. Wer das Repo verschiebt, muss `git worktree repair` ausführen.
