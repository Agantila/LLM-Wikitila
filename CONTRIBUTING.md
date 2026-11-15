# Beitragen

Danke für dein Interesse. Kurzfassung (Details für Menschen und KI-Agenten in [AGENTS.md](AGENTS.md)):

1. Issue oder Backlog-Eintrag (`pm/BACKLOG.md`) als Ausgangspunkt. Bei größeren Änderungen zuerst einen Plan in `pm/plans/` schreiben.
2. Branch `typ/thema` anlegen, Änderung mit Test (`test_wikitila.py`, synthetischer Korpus, kein Netz).
3. Gates ausführen:
   ```bash
   python3 -m unittest test_wikitila
   python3 wikitila.py --root examples/demo-corpus build
   python3 validate_catalog.py --root examples/demo-corpus --catalog golden_catalog.example.jsonl
   ```
4. Doku auf Deutsch **und** Englisch nachziehen, `CHANGELOG.md` unter `[Unreleased]` ergänzen.
5. Pull Request nach Vorlage.

Die verbindlichen Designentscheidungen ([ADR-001](pm/adr/ADR-001-verbindliche-designentscheidungen.md)): kein Vector-Store-Dienst, kein Modell im Laufzeitpfad, Laufzeit nur mit der Standardbibliothek. Wer daran etwas ändern will, legt ein neues ADR mit Messung vor.

Niemals echte Vault-Inhalte, Indizes (`.wikitila/`) oder Secrets in Issues, Tests oder Commits.
