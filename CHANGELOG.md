# Changelog

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionen nach [SemVer](https://semver.org/lang/de/).

## [Unreleased]

### Behoben
- `install.sh` und `wikitila` sind im Repository als ausführbar markiert. Vorher scheiterte `./install.sh` nach einem frischen Klon mit „Permission denied“.

### Doku und Projektmanagement
- Lokale Veröffentlichungsbereitschaft erneut geprüft. Status und Backlog weisen das vorhandene `gh`-Konto sowie die ausstehende ausdrückliche Freigabe für das öffentliche Anlegen aus.

## [0.2.0] — 2026-11-15

Umsetzung des Reviews [review/report-2026-11-15.md](review/report-2026-11-15.md), Plan: [pm/plans/2026-11-15-review-fixes.md](pm/plans/2026-11-15-review-fixes.md).

### Sicherheit
- **F1:** `config.example.toml` legt den Index unter `.wikitila/` statt `.sbs/` ab (wie dokumentiert). `install.sh` trägt `.wikitila/` in die `.gitignore` des Ziel-Ordners ein, wenn dieser ein Git-Repo ist.
- **F2:** `mask_secrets` maskiert alle Textfelder der Ausgabe (Überschrift, Titel, Entitäts-Labels in `why`, Decision-Kandidaten), nicht nur den Passagen-Text.
- **F7:** Symlinks, die aus dem Ordner herausführen oder ins Leere zeigen, werden nicht indexiert (ADR-004).

### Geändert
- **F3/F4:** Neue indexierte Tabelle `chunks(cid, path)` (ADR-002). Der Build ist nicht mehr quadratisch (10.000 Dateien: 65,5 s → 3,2 s), und die Suche lädt nur noch Kandidaten statt des ganzen Index (p50 32 ms → 3 ms bei 50.000 Abschnitten). Ältere Indizes werden beim Öffnen automatisch migriert.
- **F6:** `search`, `eval`, `embed` und `status` legen keinen Index an. Fehlt er oder ist er leer, endet der Aufruf mit Exit-Code 2 und einer Meldung statt mit einem scheinbaren `nicht_belegt` (ADR-003).
- **F10:** Die Größengrenze (600.000 Bytes) wird vor dem Lesen geprüft. `build`, `check` und `manifest` zählen einheitlich in Bytes.
- **F11:** Der Abwertungsfaktor für abgelöste Dateien wird höchstens einmal angewendet, auch wenn Frontmatter und Register beide ablösen.
- **F12:** `wikitila_graph.py` versteht `--root` und legt `graphify-out/` bei Bedarf an.
- `validate_catalog.py`: Das p95 wird über alle Fälle nach Nearest-Rank berechnet, zuvor passte der Index nicht zur Listenlänge.
- `--version`.

### Behoben
- **F5:** Ein unlesbares oder ungültiges Authority-Register wird nicht mehr still ignoriert, sondern erzeugt `warnings`. Falsche Feldtypen (`[]`, `stale_after` als Zahl, `supersedes` als String) führen nicht mehr zum Absturz.
- **F8:** `manifest` bricht bei defekten Symlinks nicht mehr ab (Felder `symlink_outside_root`, `unreadable`).
- **F9:** Kaputtes `wikitila.toml` erzeugt eine klare Fehlermeldung. Bei kaputtem `graph.json` gibt es eine Warnung, und der Build läuft ohne Entitäten weiter.
- Offene SQLite-Verbindungen und Sockets in Befehlen und Tests werden geschlossen (keine `ResourceWarning` mehr).

### Doku und Projektmanagement
- **F13:** Der PyPI-Name des Graph-Pakets ist korrigiert: `graphifyy` statt `graphify` (zuvor Verwechslungsgefahr), Versionen gepinnt. Dass MRR 0,785 unter dem Ziel 0,80 liegt, steht jetzt in der Doku. Neues Demo-Korpus macht den Beispielkatalog reproduzierbar.
- Neu: `AGENTS.md`, `CLAUDE.md`, `pm/` (Status, Backlog, Roadmap, Pläne, ADRs, Memory, Sitzungen), CI-Workflow, Dependabot, Issue- und PR-Vorlagen, `CONTRIBUTING.md`, `SECURITY.md`.
- Tests: von 18 auf 32.

## [0.1.0] — 2026-11-14

Erstveröffentlichung: Suche (FTS5/BM25, Link-Graph, Authority-Register, Antwortvertrag), lokale Graphify-Extraktion, Katalog-Validierung, Doku DE/EN.
