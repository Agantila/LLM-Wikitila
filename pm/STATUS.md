# Status

**Stand:** 2026-11-27 · **Version:** 0.3.0 getaggt; Unreleased (Kandidat 0.4.0) in PR #1 (`feat/production-hardening`), wartet auf Merge · **Repo:** <https://github.com/Agantila/LLM-Wikitila>

**Einsatz:** Erster Produktiveinsatz im Referenz-Vault des Owners über einen Release-Worktree (siehe [Einsatz](#einsatz))

## Gates

| Gate | Wert |
|---|---|
| Unit-Tests | ✅ 79/79 (lokal Python 3.14.10) |
| GitHub-CI | ✅ PR #1 grün auf Python 3.11, 3.12, 3.13, 3.14 (Tests, Katalog-Gate, lint, Installer) |
| Demo-Katalog (`examples/demo-corpus`) | ✅ R@10 1,00 · MRR 1,000 · `--gate` bestanden · `lint --all` 0 Verstöße |
| Referenz-Vault (Owner-Messung 2026-11-15, v0.2.0, 1.459 Dateien) | R@10 1,00 ✅ · MRR 0,776 ⚠️ (Ziel 0,80) · Abstention-Signal 8/8 |
| Build 10.000 Dateien (synthetisch) | ✅ 3,2 s (vorher 65,5 s) |

## Zuletzt erledigt

- Produktionsreife (Plan 2026-11-27-produktionsreife, B-023 bis B-026, ADR-006): Indexformat-Version mit Vollneubau nach Upgrade, Konfigurationsprüfung, alle Fehlerpfade ohne Traceback, `validate_catalog.py --gate` mit Antwortstatus-Ebene, Frontmatter-Randfälle, Demo-Korpus lint-konform, Installer/Wrapper mit `PYTHON`, CI 3.11–3.14 mit lint und Gate. 79 Unit-Tests grün, Demo-Katalog R@10 1,00 / MRR 1,000, Gate bestanden.
- Schreibseite umgesetzt (Plan 2026-11-27, B-019/B-020): neuer Befehl `lint` (Einzeldatei, `--all`, `--json`, `[lint]`-Konfiguration, zweistufig Verstoß/Hinweis, gleiche `parse_doc`-Sicht wie der Index), Schreib-Vertrag-Schritt in Setup- und Upgrade-Prompt (DE+EN), Doku der indexierten Frontmatter-Felder (architecture/README/operations, DE+EN). Review-Nacharbeit: nur `.md`, `exclude` ohne Groß-/Kleinschreibung, Einzeldatei mit absolutem Pfad/Ausnahme/Pfad-Grenze, Meldung für nicht abgeschlossenes Frontmatter. 56 Unit-Tests grün, Demo-Katalog unverändert R@10 1,00 / MRR 1,000.
- Review Schreibseite (2026-11-27): Setup-/Upgrade-Prompt haben keinen Schreib-Vertrag — Schema-Drift im Referenz-Vault als Beleg, Backlog B-019 bis B-022 angelegt, siehe [review/report-2026-11-27-schreibseite.md](review/report-2026-11-27-schreibseite.md).
- Suchsicht und Qualität umgesetzt (Plan 2026-11-25): `term_coverage`/`uncovered`/`trace` in der Suche, neuer `coverage`-Befehl, Register-Metadaten, Authority-Wert-Chunks, Frontmatter-Status indexiert, Chunk-Aggregation im Ranking, kurze Abschnitte indexiert (B-018), ADR-005 (Coverage-Note bleibt Signal). 39 Unit-Tests grün, Demo-Katalog MRR 1,000.
- Repository veröffentlicht: `Agantila/LLM-Wikitila` ist öffentlich, `main` und Tag `v0.2.0` sind gepusht, CI auf Python 3.11 bis 3.13 grün (B-001 erledigt).
- Lokale Veröffentlichungsabnahme erneut bestätigt: Tests, Demo-Katalog und Installer-Rauchtest grün; `gh`-Konto Agantila vorhanden. Auf Owner-Entscheidung wurde keine externe Aktion ausgeführt.
- Review 2026-11-15 umgesetzt (F1 bis F13), siehe [plans/2026-11-15-review-fixes.md](plans/2026-11-15-review-fixes.md).
- PM-Struktur, Memory, CI und Repo-Vorlagen angelegt.
- Veröffentlichung vorbereitet: Historie auf die Noreply-Adresse von Agantila umgeschrieben, interne Vault-Details neutralisiert, Tag `v0.2.0` neu gesetzt, Skripte ausführbar.
- Produktiveinsatz umgestellt: alte Werkzeug-Kopie archiviert, der Referenz-Vault läuft aus dem Release `v0.2.0` (B-002 erledigt).

## Offen / nächster Schritt

1. 🟡 **Release 0.4.0 (Owner):** Branch `feat/production-hardening` committen, PR, Merge, `__version__` auf 0.4.0, Tag `v0.4.0`, Release-Worktree umstellen. Im Vault baut der erste `build` vollständig neu (ADR-006), danach Katalog messen (B-027) und den vault-seitigen Linter durch `lint --all` ersetzen.
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
