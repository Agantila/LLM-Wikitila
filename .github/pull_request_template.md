## Was und warum

<!-- Kurzbeschreibung. Bezug: B-NNN / F<n> / ADR-NNN / Issue -->

## Checkliste

- [ ] Plan in `pm/plans/` (bei nicht-trivialen Änderungen)
- [ ] ADR in `pm/adr/` + `INDEX.md` (bei strukturellen Entscheidungen)
- [ ] Test für jede Verhaltensänderung, `python3 -m unittest test_wikitila` grün
- [ ] Demo-Katalog: `validate_catalog.py` auf `examples/demo-corpus` R@10 1.00
- [ ] Doku DE **und** EN synchron
- [ ] `CHANGELOG.md` (`[Unreleased]`), `pm/BACKLOG.md`, `pm/STATUS.md` aktualisiert
- [ ] Keine Secrets, keine Vault-Inhalte, nichts aus `.wikitila/`
- [ ] Verbindliche Designentscheidungen (ADR-001) eingehalten oder per neuem ADR geändert
