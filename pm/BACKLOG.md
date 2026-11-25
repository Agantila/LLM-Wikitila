# Backlog

Priorität: P1 = als Nächstes · P2 = bald · P3 = bei Gelegenheit. Status: ✅ · 🟡 · ⏳ · ⚠️

## Offen

| ID | Prio | Status | Thema | Bezug |
|---|---|---|---|---|
| B-010 | P2 | 🟡 | MRR 0,776 (Owner-Messung 2026-11-15) → ≥ 0,80: Ranking aggregiert jetzt bis zu drei Chunks; verfehlte Ränge am Owner-Vault nachmessen | Plan 2026-11-25, validation.md |
| B-015 | P2 | 🟡 | Passagen-Präsenz 42 % → höher: Authority-Wert-Chunks, Frontmatter-Status, kurze Abschnitte indexiert; Owner-Messung offen | Plan 2026-11-25 |
| B-016 | P2 | 🟡 | Semantische Abstention 7/8 FP → Coverage-Note (`term_coverage`/`uncovered`) umgesetzt; Antwort-Tor bleibt Signal-only (ADR-005), Owner-Messung offen | Plan 2026-11-25 |
| B-011 | P2 | ⏳ | Link-Graph inkrementell statt komplett neu bauen (Regex über alle Texte bei jedem Build) | Review Phase C |
| B-012 | P3 | ⏳ | BM25-Kosten bei sehr häufigen Termen (Query mit ca. 1.500 Treffern: 50 ms): ggf. `limit` vor dem Ranking oder Ausschluss häufiger Terme messen | Review Phase C |
| B-013 | P3 | ⏳ | Release-Signierung (signierte Tags) prüfen. Actions sind bereits auf Commit-SHA gepinnt und werden per Dependabot aktualisiert | F13 |
| B-014 | P3 | ⏳ | Englische Übersetzung der PM-Dokumente, falls externe Beitragende dazukommen | — |

## Erledigt

| ID | Thema | Erledigt | Bezug |
|---|---|---|---|
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
