# Plan: Lokale Veröffentlichungsabnahme

**Datum:** 2026-11-15 · **Backlog:** B-001 · **Status:** ✅ · **Branch:** `main`

## Ziel
Das Repository ist lokal für die spätere öffentliche Veröffentlichung als `Agantila/LLM-Wikitila` geprüft und der verbleibende externe Schritt ist eindeutig dokumentiert. Abnahme: Unit-Tests, Demo-Katalog und Installer-Rauchtest sind grün; Zielkonto und Ausführbarkeit sind bestätigt; ohne ausdrückliche Freigabe werden weder Remote noch GitHub-Repository angelegt.

## Kontext
Die eigentliche Vorbereitung einschließlich Historienbereinigung wurde in [../sessions/2026-11-15-veroeffentlichung.md](../sessions/2026-11-15-veroeffentlichung.md) abgeschlossen. Diese Sitzung bestätigt den aktuellen Stand. Der Owner hat sich in dieser Sitzung ausdrücklich für „nur lokal vorbereiten“ entschieden. Es gibt keine Code- oder Verhaltensänderung und daher keinen ADR.

## Schritte
- [x] 1. Projektstand, bestehende Veröffentlichungsvorbereitung und Git-Zustand prüfen.
- [x] 2. Verfügbarkeit des Kontos `Agantila` und Nichtvorhandensein des Zielrepositories lesend bestätigen.
- [x] 3. Projekt-Gates, Installer-Rauchtest und Ausführbarkeitsbits prüfen.
- [x] 4. Status, Backlog, Changelog und Sitzungsnotiz aktualisieren.

## Tests
Keine neuen Tests, da sich das Verhalten nicht ändert. Ausgeführt wurden `python3 -W error::ResourceWarning -m unittest -v test_wikitila`, Build und Katalogvalidierung auf `examples/demo-corpus` sowie der Installer-Ablauf mit echter Suche in einem temporären Ordner.

## Risiken / Rückweg
Die Prüfung erzeugte keine externen Änderungen. Temporäre Testdaten wurden gelöscht; die Gates erzeugten keine neuen unignorierten Laufzeitdateien. Die GitHub-CI auf Python 3.11 bis 3.13 kann erst nach dem späteren Push laufen.

## Ergebnis (nach Abschluss)
Alle lokalen Abnahmekriterien sind erfüllt: 32/32 Tests auf Python 3.14.8, R@10 1,00 und MRR 1,000 auf dem Demo-Katalog, erfolgreicher Installer-Rauchtest, Ausführbarkeitsbits `100755`. `Agantila` ist in `gh` verfügbar; das Zielrepository existiert noch nicht. Gemäß Owner-Entscheid fanden keine externen Schreibzugriffe statt. B-001 bleibt für das ausdrücklich freizugebende Anlegen, Pushen und die GitHub-CI offen.
