# Changelog

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionen nach [SemVer](https://semver.org/lang/de/).

## [Unreleased]

Schreibseite (B-019, B-020), Plan: [pm/plans/2026-11-27-lint-schreibvertrag.md](pm/plans/2026-11-27-lint-schreibvertrag.md), Review: [review/report-2026-11-27-schreibseite.md](review/report-2026-11-27-schreibseite.md).

### Hinzugefügt
- **Neuer Befehl `lint`:** prüft die Schreibseite (Frontmatter-Konvention). `lint <datei>` (Exit 1 bei Verstößen), `lint --all [--json]` als Soll-Ist-Report über den Scope. Zweistufig: Verstoß (kein Frontmatter, Pflichtfeld aus `require` fehlt/leer — gelesen mit derselben `parse_doc`-Logik wie der Build) vs. Hinweis (unquotierter Doppelpunkt, `status` außerhalb der konfigurierten Werte). Neue Konfigurationssektion `[lint]` (`require`, `status_values`, `exclude`, `since`) in `wikitila.toml`. Geprüft werden nur `.md`-Dateien; `exclude`-Muster gelten ohne Groß-/Kleinschreibung. `lint <datei>` nimmt auch absolute Pfade (Hooks), meldet ausgenommene Dateien mit Exit 0 und lehnt Pfade außerhalb des Ordners als Bedienfehler (Exit 2) ab.
- **Schreib-Vertrag-Schritt** in Setup-Prompt (§0 Schritt 4) und Upgrade-Prompt (§0b Schritt 4), deutsch und englisch: Frontmatter-Minimalprofil, Verankerung in den Eintrittsdateien des Zielordners (nur mit Owner-Freigabe), Prüfung per `lint`, Katalogfall aus Frontmatter.
- Doku: welche Frontmatter-Felder der Index liest (`title`, `description`, `status`, `superseded_by`, flach), in architecture.de/en; `lint` in README (DE/EN), operations (DE/EN) und der Produkt-Skill-Datei.

Produktionsreife (B-022 Teil, B-023 bis B-026), Plan: [pm/plans/2026-11-27-produktionsreife.md](pm/plans/2026-11-27-produktionsreife.md), ADR-006.

### Geändert
- **Indexformat-Version (ADR-006):** `build` speichert `INDEX_FORMAT` und baut bei abweichendem oder fehlendem Format vollständig neu. Bisher erreichten Änderungen an Parsing/Chunking nach einem Upgrade nur Dateien, die seitdem bearbeitet wurden. **Der erste `build` nach diesem Update baut einmal komplett neu**, Vektoren danach mit `embed` neu erzeugen. `check` meldet ein veraltetes Format als Drift, `status` als Hinweis.
- **Frontmatter:** erkannt werden jetzt auch Dateien mit BOM, ein leerer Block (`---`/`---`) und ein Block ohne Zeilenumbruch am Dateiende; Schlüssel dürfen Ziffern und Bindestriche enthalten (`created-at`). Build und `lint` nutzen dieselbe Erkennung.
- `[lint] status_values` enthält standardmäßig `superseded` (der Index wertet diesen Status ab).
- `eval` zählt nur Fälle mit `expect`; Negativfälle werden übersprungen und gezählt (vorher drückten sie den Recall). p95 nach Nearest-Rank wie in `validate_catalog.py`.
- `install.sh` legt ein leeres `authority_register.json` an statt der Beispiel-Einträge mit Demo-Pfaden; prüft sqlite3/FTS5; `PYTHON=…` wählt den Interpreter (ebenso im Wrapper `wikitila`).
- Demo-Korpus erfüllt den Schreib-Vertrag (`title`/`description`/`status`); Beispielkatalog: `answer` der Authority-Fälle auf `widersprüchlich` korrigiert (Vertrag: beide Werte mit Auflösung sichtbar), neuer Fall nur über `description` erreichbar (B-022).

### Hinzugefügt
- **Konfigurationsprüfung:** falsche Typen in `wikitila.toml` (z. B. `require = "title"`, negative Zahlen, `max_chunk_chars = 0`) enden mit `FEHLER` (Exit 2); unbekannte Sektionen/Schlüssel erzeugen eine Warnung. `WIKITILA_CONFIG` auf eine fehlende Datei ist ein Fehler.
- **`validate_catalog.py --gate`:** Exit 1 bei verfehltem Recall, fehlender coverage-Datei, falschem Antwortstatus (positiv/authority) oder Negativfall ohne Abstention-Signal. Neue Ebene „Antwortstatus“ wertet das bisher ungeprüfte Feld `answer` aus; fehlerhafte Kataloge enden mit Exit 2 und Zeilennummer.
- `status` meldet Register-Pfade, die nicht im Index stehen.
- CI: Python 3.14, `validate_catalog.py --gate`, `lint --all` auf dem Demo-Korpus, Installer-Idempotenz.

### Behoben
- Kein Traceback mehr bei: fehlendem/kaputtem Index, gesperrter Datenbank (jetzt 30 s Wartezeit), SQLite ohne FTS5, Python ohne sqlite3 oder < 3.11, `embed` ohne numpy oder ohne erreichbaren Dienst, kaputtem Golden Set, Strg-C (Exit 130), Ausgabe in `head` (Broken Pipe).
- Nicht vorhandener `--root` wird nicht mehr stillschweigend angelegt (Exit 2).
- `-k` muss ≥ 1 sein (vorher `-k 0`: Status „belegt“ ohne Ergebnis).
- Datenbankverbindungen werden in allen Lesebefehlen geschlossen (ResourceWarning).
- `validate_catalog.py`: Liste „Beleg fehlt“ war als Top-1 beschriftet, prüfte aber alle Top-k.
- `wikitila_graph.py`: verständliche Meldung ohne Graphify/networkx oder Ollama, Log-Datei wird geschlossen, fehlende Tokenzahlen brechen `bench` nicht mehr.

### Dokumentation
- Review-Bericht zur Schreibseite (`review/report-2026-11-27-schreibseite.md`): Setup- und Upgrade-Prompt hatten keinen Schreib-Vertrag; Schema-Drift im Referenz-Vault des Owners als Beleg.

## [0.3.0] — 2026-11-25

Suchsicht und Qualität (MRR, Passagen-Präsenz, Abstention), Plan: [pm/plans/2026-11-25-qualitaet-mrr-passage-abstention.md](pm/plans/2026-11-25-qualitaet-mrr-passage-abstention.md), ADR-005.

### Hinzugefügt
- **Suchsicht:** `search --json` liefert `term_coverage`/`uncovered` (deterministische Coverage-Note, Analog zu NVIDIA Auto Ontologys `check_answerable`) und einen Query-`trace` (aufgelöste Register-Regeln, Antwort-Tor-Begründung). Treffer tragen zusätzlich `authority`/`verified_at` aus dem Authority-Register.
- **Neuer Befehl `coverage`:** Pre-Flight ohne Ranking, der meldet, wie gut der Index eine Frage abdeckt (Ko-Lokation der Query-Begriffe im selben Chunk).
- `validate_catalog.py`: neue Zeile „Coverage-Note < 1,0“ für `kind=negativ`.

### Geändert
- Datei-Ranking aggregiert bis zu drei Chunks je Datei statt nur des besten Chunk-Rangs (MRR, B-010).
- Frontmatter-`status`/`superseded_by` werden in den durchsuchbaren Titel aufgenommen („verbindlich beschlossen?“ → `proposed` auffindbar).
- Chunks, die einen Authority-Register-Wert enthalten, werden bei allen Register-Einträgen bevorzugt; kompakte Werte („549/899/1.199“) werden in Atome zerlegt (Passagen-Präsenz).
- Tokenisierung behält mehrstellige Zahlen („1.199“, „10.794“); einzelne Ziffern entfallen. Häufige Verben (`gelten`, `gibt`, …) sind Stoppwörter.
- Kurze Abschnitte mit Überschrift und Inhalt werden indexiert statt verworfen (B-018; „## Schrift · Bai Jamjuree“ auffindbar).

### Behoben
- `install.sh` und `wikitila` sind im Repository als ausführbar markiert. Vorher scheiterte `./install.sh` nach einem frischen Klon mit „Permission denied“.

### Doku und Projektmanagement
- Repository veröffentlicht: `Agantila/LLM-Wikitila` ist öffentlich, `main` und Tag `v0.2.0` sind gepusht, CI auf Python 3.11 bis 3.13 grün.
- ADR-005: Coverage-Note ist ein Signal, kein Antwort-Tor-Kriterium.

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
