# Plan: Produktionsreife (Härtung aller Befehle, CI-Gates, Demo-Korpus)

**Datum:** 2026-11-27 · **Backlog:** B-022 (Teil), B-023, B-024, B-025, B-026 · **Status:** ✅ · **Branch:** `feat/production-hardening`

## Ziel

Jeder Befehl endet bei Bedien-, Konfigurations-, Daten- und Umgebungsfehlern mit einer verständlichen Meldung (Exit 2) statt mit einem Traceback. Ein Upgrade von LLM-Wikitila baut den Index vollständig neu, wenn sich das Indexformat geändert hat. Die CI prüft zusätzlich die Schreibseite des Demo-Korpus und den Antwortvertrag des Beispielkatalogs.

**Abnahmekriterium:** alle Unit-Tests grün (neue Tests für jeden Befund), Demo-Katalog R@10 1,00 / MRR 1,000, `lint --all` auf dem Demo-Korpus ohne Verstoß, `validate_catalog.py --gate` mit Exit 0, CI-Matrix 3.11 bis 3.14.

## Kontext

Review des gesamten Codes am 2026-11-27 nach der lint-Umsetzung (Plan 2026-11-27-lint-schreibvertrag). Randbedingungen aus AGENTS.md Abschnitt 3: nur Standardbibliothek, kein Modell im Laufzeitpfad, Antwort-Tor bleibt signalbasiert (ADR-005, die Negativfälle des Demo-Katalogs bleiben deshalb ohne Abstention).

Befunde:

| # | Befund | Folge |
|---|---|---|
| P1 | Inkrementeller Build vergleicht nur den Datei-Hash. Änderungen an Parsing/Chunking (z. B. 0.3.0: kurze Abschnitte, Status-Feld) erreichen unveränderte Dateien nie | Owner-Messungen nach Upgrades messen einen Mischindex |
| P2 | Konfiguration ohne Typprüfung: `[lint] = "x"` → `TypeError`, `require = "title"` prüft einzelne Buchstaben | Traceback bzw. stilles Fehlverhalten |
| P3 | `embed` ohne Ollama/numpy, SQLite-Fehler (gesperrt, kein FTS5), Strg-C, Broken Pipe → Traceback | unklare Fehlerbilder für Agenten |
| P4 | `eval`: fehlende/kaputte Golden-Datei → Traceback; Negativfälle (`expect: []`) zählen als Fehltreffer; p95-Index falsch | falsche Recall-Werte |
| P5 | Frontmatter mit BOM, ohne Zeilenumbruch nach dem schließenden `---` oder leer wird nicht erkannt | Felder fehlen im Index, lint meldet falsch |
| P6 | `validate_catalog.py`: Katalogfehler → Traceback; Feld `answer` dokumentiert, aber nie geprüft; Label „fehlt im Top-1-Snippet“ bei Top-k-Bedingung; kein Exit-Code für CI | CI prüft nur per `grep` |
| P7 | Demo-Korpus verletzt den eigenen Schreib-Vertrag (4/4) | Vorbild widerspricht der Doku |
| P8 | `wikitila`-Wrapper und `install.sh` fest auf `python3`; Installer kopiert Beispiel-Register mit Demo-Pfaden in fremde Ordner | auf Rechnern mit altem `python3` nicht nutzbar; Register zeigt auf nicht vorhandene Dateien |
| P9 | `status` meldet nicht, wenn Register-Pfade nicht im Index sind | Tippfehler im Register bleiben unbemerkt |
| P10 | `-k 0`/negativ liefert „belegt“ ohne Ergebnis | widersprüchliche Ausgabe |
| P11 | `wikitila_graph.py`: fehlendes graphify → Traceback, Log-Datei nicht geschlossen, `None`-Tokenzahlen brechen `bench` | optionales Werkzeug bricht unschön |

## Schritte

- [x] 1. Plan, Backlog-IDs, ADR-006 (Indexformat-Version)
- [x] 2. `wikitila.py`: Indexformat-Version (P1), Konfig-Validierung (P2), Fehlerbehandlung in `main` und `embed` inkl. Python-Versionsprüfung und SQLite-Timeout (P3), `eval` (P4), Frontmatter (P5), Register-Prüfung in `status` (P9), `-k` (P10), lint-Strukturhinweis für Schlüssel mit Ziffern/Bindestrich
- [x] 3. `validate_catalog.py` (P6)
- [x] 4. Demo-Korpus lint-konform, Katalog unverändert (P7)
- [x] 5. Wrapper/Installer (P8), `wikitila_graph.py` (P11)
- [x] 6. CI: Python 3.14, `lint --all`, `validate_catalog.py --gate`
- [x] 7. Doku DE+EN, CHANGELOG, STATUS, BACKLOG, Sitzungsnotiz

## Tests

Neu in `test_wikitila.py`: Formatwechsel erzwingt Vollneubau; Konfig-Typfehler → `WikitilaError`; BOM/Frontmatter am Dateiende/leeres Frontmatter; `eval` überspringt Negativfälle und meldet kaputte Golden-Dateien; CLI-Subprozess-Tests für Exit-Codes (`-k 0`, fehlende Konfiguration, `embed` ohne Server); `status` meldet unbekannte Register-Pfade; `validate_catalog.py --gate` auf dem Demo-Korpus; Demo-Korpus lint-konform.

## Risiken / Rückweg

Formatwechsel löst beim ersten Build nach dem Upgrade einen Vollneubau aus (einmalig Sekunden bis wenige Minuten, Vektoren müssen neu erzeugt werden). Frontmatter im Demo-Korpus verändert das Titelfeld (Gewicht 6) — Katalog vor und nach messen. Rückweg: `git revert`.

## Ergebnis (nach Abschluss)

Umgesetzt am 2026-11-27. Gates: 79/79 Unit-Tests (23 neue in `TestHaertung`), auch mit `-W error::ResourceWarning`; Demo-Katalog R@10 1,00 / MRR 1,000 / Passagen Top-1 3/4 unverändert; `validate_catalog.py --gate` Exit 0; `lint --all` auf dem Demo-Korpus 4/4 konform; Installer-Rauchtest (leeres Register, Idempotenz, klare Meldung bei zu altem `python3`) lokal grün.

Abweichungen vom Plan:
- Die neue Antwortstatus-Ebene deckte auf, dass das Feld `answer` der zwei Authority-Fälle im Beispielkatalog falsch war (`belegt`); der Code folgt dem dokumentierten Vertrag (`widersprüchlich` = beide Werte mit Auflösung). Katalog korrigiert, nicht der Code.
- Zusätzlich gefunden und behoben: Datenbankverbindungen in `search`/`coverage`/`eval`/`embed` blieben offen; `connect` schloss bei kaputtem Index nicht; nicht vorhandener `--root` wurde angelegt; `[lint] status_values` kannte `superseded` nicht, obwohl der Index den Status abwertet.
- Versehentlich lief `wikitila_graph.py build` im Repo-Ordner (Graphify ist lokal installiert); das erzeugte `graphify-out/` (gitignored) wurde wieder gelöscht.

Folgearbeiten: B-027 (Owner-Messung nach Vollneubau), B-022 Rest (status-Katalogfall), Release 0.4.0.
