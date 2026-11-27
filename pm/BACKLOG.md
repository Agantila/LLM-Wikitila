# Backlog

Priorität: P1 = als Nächstes · P2 = bald · P3 = bei Gelegenheit. Status: ✅ · 🟡 · ⏳ · ⚠️

## Offen

| ID | Prio | Status | Thema | Bezug |
|---|---|---|---|---|
| B-021 | P2 | 🟡 | Doku-Teil erledigt (indexierte Frontmatter-Felder in architecture.de/en, README, Prompts). Offen: Entscheidung tags/type indexieren (Messung, dann ADR) | Review 2026-11-27 (F3) |
| B-022 | P3 | 🟡 | Demo-Korpus lint-konform, ein description-Fall im Katalog, `lint --all` als CI-Gate ✅. Offen: Katalogfall nur über `status` erreichbar (Unit-Test deckt es ab) | Review 2026-11-27 (F5) |
| B-010 | P1 | ⚠️ | Referenz-Vault 2026-11-27 (v0.4.0, 1.549 Dateien): R@10 0,94, MRR 0,682 (2026-11-15: 1,00 / 0,776) → Ziel R@10 1,00, MRR ≥ 0,80. Zwei Fehltreffer durch Ranking-Konkurrenz im gewachsenen Vault analysieren | Plan 2026-11-25, B-027 |
| B-015 | P2 | 🟡 | Passagen-Präsenz 42 % → höher: Authority-Wert-Chunks, Frontmatter-Status, kurze Abschnitte indexiert; Owner-Messung offen | Plan 2026-11-25 |
| B-016 | P2 | 🟡 | Semantische Abstention 7/8 FP → Coverage-Note (`term_coverage`/`uncovered`) umgesetzt; Antwort-Tor bleibt Signal-only (ADR-005), Owner-Messung offen | Plan 2026-11-25 |
| B-011 | P2 | ⏳ | Link-Graph inkrementell statt komplett neu bauen (Regex über alle Texte bei jedem Build) | Review Phase C |
| B-012 | P3 | ⏳ | BM25-Kosten bei sehr häufigen Termen (Query mit ca. 1.500 Treffern: 50 ms): ggf. `limit` vor dem Ranking oder Ausschluss häufiger Terme messen | Review Phase C |
| B-013 | P3 | ⏳ | Release-Signierung (signierte Tags) prüfen. Actions sind bereits auf Commit-SHA gepinnt und werden per Dependabot aktualisiert | F13 |
| B-014 | P3 | ⏳ | Englische Übersetzung der PM-Dokumente, falls externe Beitragende dazukommen | — |

## Erledigt

| ID | Thema | Erledigt | Bezug |
|---|---|---|---|
| B-027 | Messung im Referenz-Vault nach Release 0.4.0: Vollneubau ohne Messwert-Effekt (Index war faktisch aktuell), R@10 0,94 · MRR 0,682 · Passagen 42 % · Abstention-Signal 8/8 · Antwortstatus 27/44; vault-eigener OKF-Linter durch `lint --all` ersetzt | 2026-11-27 | Sitzung 2026-11-27-vault-einsatz-0.4.0 |
| B-023 | Indexformat-Version erzwingt Vollneubau nach Upgrade, `check`/`status` melden veraltetes Format | 2026-11-27 | ADR-006, Plan 2026-11-27-produktionsreife |
| B-024 | Konfigurationsprüfung (Typen, Unbekanntes), Fehlerpfade ohne Traceback (SQLite, Netz, numpy, Python-Version, Strg-C, Broken Pipe), `--root`/`-k`-Validierung, Verbindungen geschlossen | 2026-11-27 | Plan 2026-11-27-produktionsreife |
| B-025 | `validate_catalog.py --gate`, Antwortstatus-Ebene, Katalogprüfung; `eval` ohne Negativfälle; CI 3.14 + lint + Gate | 2026-11-27 | Plan 2026-11-27-produktionsreife |
| B-026 | Frontmatter-Randfälle (BOM, leer, Dateiende, Schlüssel mit Bindestrich), Installer mit leerem Register und `PYTHON`, Wrapper, `wikitila_graph.py`-Fehlerpfade | 2026-11-27 | Plan 2026-11-27-produktionsreife |
| B-019 | Schreib-Vertrag-Schritt in Setup-Prompt (§0 Schritt 4) und Upgrade-Prompt (§0b Schritt 4), DE+EN synchron | 2026-11-27 | Plan 2026-11-27, Review 2026-11-27 (F1/F4/F6) |
| B-020 | `wikitila.py lint` (Einzeldatei + --all + --json, `[lint]`-Konfiguration, zweistufig Verstoß/Hinweis, gleiche parse_doc-Sicht wie der Index, Exit 1 bei Verstößen) | 2026-11-27 | Plan 2026-11-27, Review 2026-11-27 (F2) |
| B-017 | Suchsicht: Query-`trace`, Register-Metadaten (`authority`/`verified_at`), `coverage`-Befehl | 2026-11-25 | Plan 2026-11-25, ADR-005 |
| B-018 | Kurze Abschnitte mit Überschrift werden indexiert (vorher < `min_chunk_chars` verworfen) | 2026-11-25 | Plan 2026-11-25 |
| B-100 | F1 Index-Pfad der Vorlage `.wikitila/`, `.gitignore`-Eintrag durch `install.sh` | 2026-11-15 | ADR-003 |
| B-101 | F2 Maskierung aller Ausgabefelder | 2026-11-15 | — |
| B-102 | F3/F4 Tabelle `chunks`, linearer Build, kandidatenbasierte Suche | 2026-11-15 | ADR-002 |
| B-103 | F5 Register-Validierung mit Warnungen | 2026-11-15 | — |
| B-104 | F6 Lesebefehle verlangen einen Index (Exit 2) | 2026-11-15 | ADR-003 |
| B-105 | F7/F8 Symlink-Policy, `manifest` robust | 2026-11-15 | ADR-004 |
| B-106 | F9 klare Fehler bei kaputtem TOML, Warnung bei kaputtem `graph.json` | 2026-11-15 | — |
| B-107 | F10 Größengrenze in Bytes vor dem Lesen | 2026-11-15 | — |
| B-108 | F11 Abwertung höchstens einmal | 2026-11-15 | — |
| B-109 | F12 `wikitila_graph.py --root`, `mkdir` | 2026-11-15 | — |
| B-110 | F13 PyPI-Name `graphifyy` gepinnt, MRR-Ziel offen dokumentiert, Demo-Korpus | 2026-11-15 | — |
| B-111 | PM-Struktur, Memory, CI, Repo-Vorlagen | 2026-11-15 | — |
| B-002 | Installation im Referenz-Vault von der alten Kopie (`.sbs/`) auf Release-Worktree `v0.2.0` umgestellt, `.wikitila/` gitignored, Werkzeug-Repo aus Vault-Index entfernt | 2026-11-15 | Entscheidung im Vault |
| B-001 | Öffentliches Repo `Agantila/LLM-Wikitila` angelegt, `main` und Tag `v0.2.0` gepusht, CI auf Python 3.11 bis 3.13 grün | 2026-11-16 | Sitzung 2026-11-16-veroeffentlichung-github |
