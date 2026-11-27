# Sitzung 2026-11-27 — Umsetzung lint-Befehl und Schreib-Vertrag (B-019, B-020)

**Anlass:** Owner-Entscheid zum Review `review/report-2026-11-27-schreibseite.md`: B-019 und B-020 umsetzen. Plan: `pm/plans/2026-11-27-lint-schreibvertrag.md`.

## Was getan wurde

- **`wikitila.py`:** neuer Befehl `lint`. `lint <datei>` (Exit 1 bei Verstößen), `lint --all [--json]` als Report über den Scope. Neue DEFAULTS-Sektion `[lint]` (`require`, `status_values`, `exclude`, `since`), dokumentiert in `config.example.toml`. `lint_text` liest Pflichtfelder über dieselbe `parse_doc`-Logik wie der Build (Prinzip: lint-konform = index-optimal). Zweistufig: Verstoß (kein Frontmatter, Pflichtfeld fehlt/leer) vs. Hinweis (unquotierter Doppelpunkt, status außerhalb `status_values`, strukturlose Frontmatter-Zeilen). Ausgaben laufen bei `privacy.mask_secrets` durch `mask()`. `main()` gibt erstmals einen befehlsabhängigen Exit-Code — nur für `lint`; `check` bleibt bewusst Exit 0.
- **Tests:** Klasse `TestLint` mit 10 Tests auf synthetischem Korpus (kein Frontmatter, fehlendes Pflichtfeld, Doppelpunkt-Hinweis, status-Hinweis, exclude-Muster, `require`-Override über wikitila.toml, `--all`-Zählung, `since`-Filter, Exit-Semantik). Suite: 49/49 grün.
- **Doku DE+EN:** Schreib-Vertrag-Schritt in Setup-Prompt (§0 Schritt 4) und Upgrade-Prompt (§0b Schritt 4) in `docs/agentic-setup.de.md`/`.en.md`; indexierte Frontmatter-Felder und die Schreibseiten-Komponente in `docs/architecture.de.md`/`.en.md`; `lint` in README (DE/EN), Betriebs-Rhythmus in `docs/operations.de.md`/`.en.md`, Werkzeugliste in `skills/llm-wikitila/SKILL.md`.
- **PM:** BACKLOG (B-019/B-020 erledigt, B-021 Doku-Teil erledigt), STATUS (Gate 49/49), CHANGELOG `[Unreleased]`, Review-Umsetzungsstand ergänzt.

## Review-Nacharbeit

- `lint --all` überspringt Nicht-`.md`-Dateien (`LINT_EXT`); `.txt` bleibt im Such-Scope.
- `lint_excluded` vergleicht ohne Groß-/Kleinschreibung.
- `lint <datei>`: absoluter Pfad wird auf den Ordner relativiert, Pfad außerhalb → `WikitilaError` (Exit 2), ausgenommene Datei → Exit 0 mit `AUSGENOMMEN` (bzw. `"excluded": true` in JSON).
- Eigene Meldung für Frontmatter ohne schließende `---`-Zeile.
- Tests: 7 neue, `since`- und `--all`-Test prüfen jetzt die JSON-Ausgabe statt nur den Rückgabewert; CLI-Ausgabe in Tests abgefangen. Suite 56/56.
- Befund: Der Demo-Korpus ist selbst nicht lint-konform (4/4 Verstöße) → unter B-022 vermerkt, nicht geändert (Katalog-Risiko).

## Was offen ist

- Release: Tag setzen (Kandidat 0.4.0), Release-Worktree umstellen, im Referenz-Vault `build` + Katalogmessung (Owner-Aufgabe nach Drei-Ebenen-Regel).
- B-021 Rest: tags/type-Indexierung entscheiden (Messung am Demo-Korpus und Referenz-Vault, dann ADR).
- B-022: Katalogfälle, deren Antwort nur über description/status erreichbar ist.
- Referenz-Vault: nach dem Release-Wechsel den vault-seitigen Linter/Report durch `wikitila.py lint --all` ersetzen (Ausnahmeliste in dessen `wikitila.toml` übernehmen).

## Was die nächste Sitzung wissen muss

- `lint` nutzt absichtlich **kein** PyYAML (Standardbibliothek nur); die YAML-Prüfung ist eine zeilenbasierte Heuristik auf Hinweis-Ebene. Wer strenge YAML-Validität erzwingen will, muss die Konvention anpassen, nicht den Parser.
- Die Prompt-Textbausteine (§0 Schritt 4, §0b Schritt 4) sind bewusst wörtlich in DE und EN gespiegelt; bei Änderungen beide Dateien synchron halten.
