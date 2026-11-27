# Plan: lint-Befehl (Schreibseite) und Schreib-Vertrag in den Prompts

**Datum:** 2026-11-27 · **Backlog:** B-019, B-020 · **Status:** ✅ · **Branch:** main

## Ziel

1. `wikitila.py lint` prüft die Schreibseite: Einzeldatei (`lint <datei>`, Exit 1 bei Verstössen) und Gesamt-Report (`lint --all [--json]`) mit Ausnahmeliste und optionalem Geltungsbeginn aus `wikitila.toml` (`[lint]`).
2. Setup-Prompt (§0) und Upgrade-Prompt (§0b) in `docs/agentic-setup.de.md`/`.en.md` erhalten einen Schreib-Vertrag-Schritt, der das Frontmatter-Minimalprofil, die Verankerung in den Eintrittsdateien (AGENTS.md/CLAUDE.md des Zielordners, nur mit Owner-Freigabe), die Prüfung per `lint` und einen Katalogfall aus Frontmatter verlangt.

**Abnahmekriterium:** Neue Unit-Tests grün (gesamt-Suite grün), Demo-Katalog unverändert grün, `lint` auf einem synthetischen Korpus meldet Verstoss/Hinweis/Konform wie spezifiziert, Exit-Codes stimmen.

## Kontext

Review 2026-11-27 (F1, F2, F4, F6), Owner-Entscheid 2026-11-27: B-019 und B-020 umsetzen. Randbedingungen aus AGENTS.md Abschnitt 3: nur Standardbibliothek (kein PyYAML — die YAML-Heuristik ist bewusst zeilenbasiert), Maskierung aller Ausgabefelder über `mask()` bei `privacy.mask_secrets`, Verhalten dokumentiert (DE+EN), Tests mit synthetischem Korpus.

Design-Entscheid (aus dem Review): `lint` liest Pflichtfelder über dieselbe `parse_doc`-Logik wie der Build — *lint-konform = index-optimal* gilt konstruktionsbedingt, ein Abdriften wie beim vault-seitigen Linter (48 Falsch-Positive) ist ausgeschlossen. Zweistufigkeit: Verstoss (bricht Indexierbarkeit: kein Frontmatter, Pflichtfeld aus `require` fehlt/leer) vs. Hinweis (Konvention: unquotierter Doppelpunkt, status ausserhalb `status_values`, strukturlose Frontmatter-Zeilen).

## Schritte

- [x] 1. Plan anlegen (diese Datei)
- [x] 2. `wikitila.py`: DEFAULTS `[lint]`, `lint_text()`, `lint_excluded()`, `cmd_lint()`, Parser/Dispatch/Exit-Code in `main()`, Modul-Docstring
- [x] 3. `config.example.toml`: `[lint]`-Sektion dokumentiert
- [x] 4. `test_wikitila.py`: Testklasse für lint (synthetisch)
- [x] 5. Doku DE+EN: Schreib-Vertrag in §0 und §0b (agentic-setup), indexierte Frontmatter-Felder (architecture), Befehl in README-Übersicht, Wartungsbullet (operations), Skill-Werkzeugliste
- [x] 6. Gates: `python3 -m unittest test_wikitila`, Demo-Katalog `validate_catalog.py`
- [x] 7. PM: BACKLOG (B-019/B-020), STATUS, CHANGELOG, Sitzungsnotiz, Review-Umsetzungsstand

## Tests

Neu in `test_wikitila.py` (Klasse `TestLint`, eigener Mini-Korpus): kein Frontmatter → Verstoss; Pflichtfeld `description` fehlt → Verstoss; unquotierter Doppelpunkt in `description` → Hinweis, kein Verstoss (Felder bleiben indexlesbar); `status` ausserhalb der Werte → Hinweis; valide Datei → konform; `exclude`-Muster greift (z. B. `copy_*`); `since` lässt alte Dateien aussen vor; `require` aus `wikitila.toml` überschreibt den Default; `--all` zählt korrekt; Einzeldatei-Exit-Code.

## Risiken / Rückweg

Risiko: `main()` bekommt erstmals einen befehlsabhängigen Exit-Code — nur für `lint` verdrahten, `check` bleibt bewusst Exit 0 (dokumentiert). Risiko: YAML-Heuristik meldet Falsch-Hinweise bei exotischem, aber valide YAML — Hinweise haben keinen Exit-Effekt, daher unkritisch. Rückweg: `git revert` des Commits; Prompt-Änderungen sind reine Doku.

## Ergebnis (nach Abschluss)

Umgesetzt am 2026-11-27 wie geplant, ohne Abweichung. Gates: 49/49 Unit-Tests grün (10 neue in `TestLint`), Demo-Katalog unverändert R@10 1,00 / MRR 1,000, CLI-Rauchtest (Einzeldatei konform/Verstoß/Hinweis, `--all`, `--json`, Bedienfehler Exit 2) manuell verifiziert. Exit-Code-Semantik: `lint` ist der einzige Befehl mit Exit 1 bei Verstößen; `check` bleibt bewusst Exit 0. **Review-Nacharbeit (gleicher Tag):** vier Lücken behoben — `--all` prüfte auch `.txt` (immer falsche Verstöße), `exclude` war case-sensitiv (`TEMPLATE.md` nicht ausgenommen), `lint <datei>` ignorierte `exclude` (Hook auf `README.md` → Exit 1), nahm absolute Pfade nur zufällig an und las Pfade außerhalb des Ordners; Meldung für nicht abgeschlossenes Frontmatter präzisiert. `since`-Test prüfte den Filter nicht wirklich, jetzt per JSON-Ausgabe. Gates danach: 56/56 grün, Demo-Katalog R@10 1,00 / MRR 1,000. Folgearbeiten: B-021 Rest (tags/type-Indexierung, Messung + ADR), B-022 (Katalogfälle aus Frontmatter), Release-Tag mit diesem Stand (Kandidat 0.4.0), danach Umstellung des Referenz-Vault auf `wikitila.py lint` (ersetzt den vault-seitigen Linter).
