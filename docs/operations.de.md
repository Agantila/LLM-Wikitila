# Betrieb und Pflege (Deutsch)

## Rhythmus

| Wann | Was | Dauer |
|---|---|---|
| nach jeder Arbeitssitzung mit neuen/geänderten Dateien | `python3 wikitila.py --root <ordner> build` (inkrementell) | Sekunden |
| monatlich | `python3 wikitila.py --root <ordner> manifest` — Coverage und Ausschlüsse prüfen | unter 1 Minute |
| vor belastbaren Antworten / in Hooks | `python3 wikitila.py --root <ordner> check` — Drift erkennen | unter 1 Minute |
| nach Arbeitssitzungen mit neuen Dateien | `python3 wikitila.py --root <ordner> lint --all` — Schreibseite: Frontmatter-Konvention (Verstöße nachziehen, Hinweise optional) | Sekunden |
| nach größeren Änderungen oder wöchentlich | Graph: `wikitila_graph.py run` (nur geänderte Dateien), dann `build`, dann `wikitila.py build` | Minuten |

**Nach einem Upgrade von LLM-Wikitila** baut der erste `build` den Index einmal vollständig neu, wenn sich das Indexformat geändert hat (Meldung `Indexformat … → …: Vollneubau`, ADR-006). `status` und `check` melden ein veraltetes Format vorher. Wer Embedding nutzt, führt danach `embed` erneut aus.

**Exit-Codes:** 0 = ok · 1 = `lint` hat Verstöße (bzw. `validate_catalog.py --gate` nicht bestanden) · 2 = Bedien-, Konfigurations- oder Umgebungsfehler (Meldung `FEHLER: …`, kein Traceback) · 130 = abgebrochen. `check` bleibt bei Drift bewusst 0 und meldet sie im Text.

Kein Dienst, kein Autostart nötig. Für Automation genügt ein Cron-Eintrag oder Git-Hook, der `build` aufruft; der Graph-Lauf gehört nicht in einen Hook (GPU, lange Laufzeit).

## Wie Agenten es nutzen

1. `python3 wikitila.py --root <ordner> search "<Frage>" -k 5 --json` liefert Datei, Überschrift, Passagen und Grund.
2. Nur die genannten Dateien öffnen — die Originalpassage ist das Zitat.
3. Zusammenhänge: `graphify path "A" "B"` und `graphify explain "X"` auf `graphify-out/graph.json` (nur wenn der Graph gebaut wurde).
4. Flags lesen: `überholt durch …` → neuere Datei lesen; `kanonisch` → maßgebliche Quelle; `veraltet`/`Gültigkeit nicht bestätigt` → fachliche Gültigkeit offen.
5. `Antwortstatus` lesen: `nicht_belegt` → keine belastbare Antwort; `widersprüchlich` → mehrere Werte mit Auflösung; `belegt_gueltigkeit_unbestaetigt` → Beleg da, Gültigkeit offen. Die Hinweise `Begriffe ohne Treffer …`, `Begriffe nicht im Top-1-Ergebnis …` und `Begriffe ohne ko-lokalen Beleg …` (`term_coverage`/`uncovered`) zeigen, wo der Agent selbst abstimmen muss. Vor der eigentlichen Suche kann `wikitila.py coverage "Frage"` die Abdeckung billig prüfen.

## Konflikt- und Freshness-Auflösung

**Freshness:** zeitabhängige Fakten (Preise, Rechtsstand, Kennzahlen) erhalten im Register `stale_after` + `verified_at`. Überschritten → Antwortstatus „belegt, aktuelle Gültigkeit nicht bestätigt“. Ein frischer Index beweist nur die Einlesung aktueller Dateien — nie die fachliche Gültigkeit.

**Konflikt:** beide Werte mit Quelle, Datum und Authority sichtbar machen; Auflösung über das Register (`supersedes`/`superseded_by` + `authority_confirmed` durch den Owner). Widersprüche werden nie still durch Mehrheit, Graph oder Modell aufgelöst.

## Fehlerkatalog

| Symptom | Ursache | Lösung |
|---|---|---|
| `no such module: fts5` / `kein sqlite3-Modul` | Python ohne SQLite/FTS5 (z. B. selbst gebautes pyenv) | anderes Python ≥ 3.11, z. B. `PYTHON=/usr/bin/python3` |
| `Konfiguration fehlerhaft: … erwartet …` | falscher Typ in `wikitila.toml` (z. B. `require = "title"` statt Liste) | Wert laut `config.example.toml` setzen |
| `Warnung: unbekannte Sektion/unbekannter Schlüssel` | Tippfehler in `wikitila.toml` | Schreibweise prüfen — der Wert wirkt sonst nicht |
| `SQLite: file is not a database` / `malformed` | Index beschädigt | `.wikitila/` löschen, `build` |
| `database is locked` nach 30 s | ein anderer `build` läuft noch | warten, dann erneut |
| `Register-Pfad nicht im Index` (status) | Tippfehler, Datei verschoben oder ignoriert | Pfad im Register korrigieren |
| `build` findet 0 Dateien | `--root` falsch / `.graphifyignore` schließt alles aus | Pfade prüfen |
| Treffer aus gelöschten Dateien | Index veraltet | `build` |
| Fundstellen zeigen Passwörter | `mask_secrets` aus | `[privacy] mask_secrets = true` |
| Entitäts-Zuordnungen 0 | `graph.json` nicht neu gebaut | erst `wikitila_graph.py build`, dann `wikitila.py build` |
| Graph-Lauf bricht ab | Ollama gestoppt oder Modell fehlt | `ollama list`, Lauf neu starten (setzt fort) |

## Sicherheit

- Der Index (`.wikitila/index.db`) enthält Volltext (unmaskiert) — wer ihn weitergibt, gibt Inhalte weiter. `.wikitila/` gehört in die `.gitignore` des Ziel-Ordners; `install.sh` trägt es dort ein, wenn der Ordner ein Git-Repo ist.
- Maskiert werden alle Textfelder der Ausgabe: Passagen, Überschriften, Titel, Entitäts-Labels in `why`.
- Symlinks, die aus dem Ordner herausführen (oder ins Leere zeigen), werden nicht indexiert und im Manifest als `symlink_outside_root` gezählt. Symlinks innerhalb des Ordners bleiben erlaubt.
- Dateien über 600.000 Bytes werden übersprungen (vor dem Lesen geprüft; `build`, `check` und `manifest` zählen gleich).
- Lesebefehle (`search`, `coverage`, `eval`, `embed`, `status`) legen keinen Index an, und ein nicht vorhandener `--root` wird nicht angelegt: Fehlt er oder ist er leer, endet der Aufruf mit Exit-Code 2 statt mit einem scheinbaren `nicht_belegt`.
- Fundstellen maskieren Schlüssel und Passwörter (`mask_secrets`, Vorgabe an); die Dateien selbst bleiben auffindbar.
- Alles läuft lokal, nichts geht an eine Cloud.
