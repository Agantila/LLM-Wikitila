# Plan: Veröffentlichung auf GitHub

**Datum:** 2026-11-16 · **Backlog:** B-001 · **Status:** ✅ · **Branch:** `main`

## Ziel
Das Repository ist als öffentliches Repo `Agantila/LLM-Wikitila` auf GitHub sichtbar, `main` und der Tag `v0.2.0` sind gepusht und die CI-Matrix auf Python 3.11 bis 3.13 ist grün. Abnahme: `gh repo view` zeigt `visibility: PUBLIC`, der Tag ist über `git ls-remote --tags` erreichbar, alle drei CI-Jobs sind erfolgreich.

## Kontext
Der Owner hat die Veröffentlichung freigegeben. Die lokale Vorbereitung (Historienbereinigung auf die Noreply-Adresse von Agantila, Neutralisierung interner Vault-Details, ausführbare Skripte, Tag `v0.2.0`) ist in [../sessions/2026-11-15-veroeffentlichung.md](../sessions/2026-11-15-veroeffentlichung.md) und [2026-11-15-veroeffentlichung-lokal.md](2026-11-15-veroeffentlichung-lokal.md) dokumentiert. Es gibt keine Code- oder Verhaltensänderung und daher keinen ADR.

Randbedingungen: Das global aktive `gh`-Konto bleibt unverändert. Authentifiziert wird ausschließlich kommandobezogen über `GH_TOKEN=$(gh auth token --user Agantila)`. `mask_secrets` und der lokale Index bleiben unberührt, es werden keine Vault-Inhalte übertragen.

## Schritte
- [x] 1. Gates prüfen: Unit-Tests, Demo-Build, Katalogvalidierung.
- [x] 2. Veröffentlichungs-Check: Secret-Scan der versionierten Dateien und der Historie, keine privaten Pfade, keine großen Blobs.
- [x] 3. Offene PM-Änderungen aus der Abnahme-Sitzung committen.
- [x] 4. Öffentliches Repo `Agantila/LLM-Wikitila` anlegen, `main` pushen.
- [x] 5. Tag `v0.2.0` pushen, Topics setzen, Sichtbarkeit prüfen.
- [x] 6. CI-Matrix 3.11 bis 3.13 abwarten und Ergebnis prüfen.
- [x] 7. PM-Stand, Backlog, Changelog und Sitzungsnotiz aktualisieren.

## Tests
Keine neuen Tests, da sich das Verhalten nicht ändert. Ausgeführt wurden `python3 -m unittest test_wikitila` (32/32), `wikitila.py --root examples/demo-corpus build` und `validate_catalog.py` (R@10 1,00 · MRR 1,000) vor dem Push sowie die GitHub-CI-Matrix auf Python 3.11, 3.12 und 3.13.

## Risiken / Rückweg
Ein Push auf ein öffentliches Repo ist nicht Rückgängig zu machen, Vertraulichkeit kann nur durch Löschen des Repositories wiederhergestellt werden. Deshalb Vorprüfung: keine echten Secrets (einziger Treffer ist das synthetische Test-Fixture `sk-abcdefghijklmnopqrstuvwxyz123456`), keine privaten Pfade in Dateien oder Historie, keine Blobs über 500 KB. Rückweg bei inhaltlichem Fehler: Repository löschen, `main` neu aus dem lokalen Stand pushen. Der Tag `v0.2.0` zeigt bewusst auf den Release-Commit `2ab4270`; die danach folgenden Commits sind laut CHANGELOG `[Unreleased]` und bleiben außerhalb des Tags.

## Ergebnis (nach Abschluss)
`Agantila/LLM-Wikitila` ist öffentlich (erstellt 2026-11-16, Default-Branch `main`), `main` und Tag `v0.2.0` sind gepusht, CI grün auf 3/3 Python-Versionen (Run 43933622720). Zehn Topics gesetzt. B-001 ist erledigt. Offen bleiben B-010 (MRR ≥ 0,80), B-011 (inkrementeller Link-Graph), B-012, B-013 (signierte Tags) und B-014 (englische PM-Dokumente).
