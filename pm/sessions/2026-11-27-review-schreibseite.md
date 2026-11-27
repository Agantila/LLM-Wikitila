# Sitzung 2026-11-27 — Review Schreibseite (Frontmatter/Schema-Drift)

**Anlass:** Im Referenz-Vault des Owners fiel Schema-Drift auf: neue Markdown-Dateien ohne Frontmatter (`type`/`title`/`description`/`tags`), obwohl die Suche genau diese Felder nutzt. Auftrag: Review für das Produkt, damit Einrichtung (Setup-Prompt) und Migration (Upgrade-Prompt) die Schreibseite künftig absichern.

## Was getan wurde

- **Review geschrieben:** `review/report-2026-11-27-schreibseite.md` im Format des Berichts vom 2026-11-15 (Befundtabelle F1 bis F6, Quick Wins, Nicht-Befunde, Grenzen, offene Fragen). Kernbefund: Der Stack sichert die Leseseite vollständig ab (Antwortvertrag, Register, Katalog), sagt auf der Schreibseite aber nichts — weder §0 noch §0b enthalten einen Schreib-Vertrag-Schritt, und §0b verlangt „AGENTS.md/CLAUDE.md nur mit Freigabe ändern", ohne den Inhalt zu nennen.
- **Beleglage:** Vault-Messung 2026-11-27 (749 Dateien im Geltungsbereich: 96 konform, 66 Hinweise, 587 Verstösse; davon 48 ungültiges YAML durch unquotierte Doppelpunkte in `description`). Eintrittsdateien des Vaults hatten historisch nie einen Verweis auf die Frontmatter-Pflicht.
- **Backlog:** B-019 (P1, Textbaustein in beide Prompts, DE+EN), B-020 (P2, `wikitila.py lint` evaluieren, wartet auf Owner-Entscheid), B-021 (P2, Doku der indexierten Felder + tags/type-Entscheid), B-022 (P2, Katalogfälle mit Frontmatter-getragenen Antworten).
- **CHANGELOG:** Eintrag unter `[Unreleased]`.
- **Gates:** Keine Code-Änderung; `python3 -m unittest test_wikitila` → 39/39 grün auf Commit `1af4e01`.

## Was offen ist

- Owner-Entscheide zu den Review-Fragen 1 bis 4 (produktseitiger Lint-Befehl ja/nein; tags/type indexieren; OKF-Referenz im Baustein; Verstoß/Hinweis-Zweistufigkeit als Konvention).
- Umsetzung von B-019 ist die Voraussetzung dafür, dass die nächste Einrichtung/Migration (auch bei Partnern) den Schreib-Vertrag mitliefert.
- Der Referenz-Vault hat die Schreibseite vault-seitig bereits abgesichert (Linter, täglicher Report, Blöcke in den Eintrittsdateien); das Produkt soll nachziehen, damit andere Installationen das nicht selbst erfinden müssen.

## Was die nächste Sitzung wissen muss

- Der Textbaustein für die Prompts liegt fertig formuliert im Review, Abschnitt 3 — B-019 ist damit reines Einfügen plus EN-Übersetzung.
- Keine Release-Auswirkung: Der Bericht ändert keinen Code; eine Aufnahme von B-020/B-021 (tags-Index) wäre ranking-ändernd und braucht Messung + ADR vor dem nächsten Tag.
