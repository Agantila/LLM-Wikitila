# Plan: Review-Befunde 2026-11-15 umsetzen

**Datum:** 2026-11-15 · **Backlog:** B-100 bis B-111 · **Status:** ✅ · **Branch:** `fix/review-2026-11-15`

## Ziel
Alle Befunde F1 bis F13 aus [review/report-2026-11-15.md](../../review/report-2026-11-15.md) beheben, ohne die verbindlichen Designentscheidungen (ADR-001) zu berühren. Dazu eine PM-, Memory- und CI-Struktur für agentische Weiterentwicklung und die Veröffentlichung auf GitHub vorbereiten.

**Abnahme:** Jeder Befund hat einen Regressionstest. Alle Tests sind grün. Der Demo-Katalog erreicht R@10 1,00. Der Build bei 10.000 Dateien ist nicht mehr quadratisch. Die Doku DE/EN ist synchron.

## Schritte
- [x] F1 `config.example.toml` → `.wikitila/`. `install.sh` trägt `.wikitila/` in die `.gitignore` von Git-Ziel-Ordnern ein (ADR-003)
- [x] F2 `mask()` auf `heading`, `title`, Entitäts-Labels in `why` und die Decision-Kandidaten anwenden
- [x] F3 Tabelle `chunks(cid, path)` mit Index, `delete_doc()` per rowid, Migration alter Indizes über `meta.schema` (ADR-002)
- [x] F4 `cpath` und `meta` nur für Kandidaten laden (`in_rows`)
- [x] F5 `load_register()` validiert Typen und liefert `warnings`, die `search` und `status` ausgeben
- [x] F6 `connect(create=False)` und `require_index()`, `WikitilaError` mit Exit-Code 2 (ADR-003)
- [x] F7 `inside_root()` filtert Symlinks nach außen (ADR-004)
- [x] F8 `manifest`: `stat()` abgesichert, Felder `symlink_outside_root`, `unreadable`
- [x] F9 TOML-Fehler als `WikitilaError`, kaputtes `graph.json` als Warnung
- [x] F10 `read_source()` prüft `MAX_FILE_BYTES` vor dem Lesen, gleiche Einheit in allen Befehlen
- [x] F11 `penalized`-Menge: Faktor höchstens einmal
- [x] F12 `wikitila_graph.py --root`, `mkdir graphify-out`
- [x] F13 `graphifyy==0.4.16`/`networkx==3.6.1` in der Doku, MRR-Ziel offen genannt, `examples/demo-corpus/`
- [x] Tests: 14 neue Regressionstests, Verbindungen und Sockets in Tests schließen
- [x] Doku DE/EN: installation, operations, validation, authority-register, architecture, agentic-setup, README
- [x] PM: `AGENTS.md`, `CLAUDE.md`, `pm/*`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/*`

## Tests
`test_f1_…` bis `test_f13_…` in `test_wikitila.py`, dazu der CI-Schritt „Demo-Katalog validieren“.

## Risiken / Rückweg
- Migration: Ältere Indizes bekommen beim ersten Öffnen die Tabelle `chunks`. Rückweg ist `rm -r .wikitila && build`.
- F10 ändert die Grenze von Zeichen auf Bytes: Dateien mit vielen Umlauten zwischen 300.000 und 600.000 Zeichen werden jetzt übersprungen und im Manifest als `oversized_skipped` geführt.
- F6 ändert das CLI-Verhalten: Skripte, die auf einem leeren Index `nicht_belegt` erwartet haben, bekommen jetzt Exit-Code 2.

## Ergebnis
| Messung (synthetisch, 5 Abschnitte/Datei) | vorher | nachher |
|---|---|---|
| Build 1.000 / 10.000 Dateien | 0,7 s / 65,5 s | 0,2 s / 3,2 s |
| Query p50 bei 10.000 Dateien | 32 ms | 3 ms |
| Query p95 bei 10.000 Dateien | 63 ms | 46 ms (eine Query mit sehr häufigen Termen, siehe B-012) |
| Tests | 18 | 32 |

Folgearbeiten: B-001 (Veröffentlichung), B-002, B-010, B-011, B-012.
