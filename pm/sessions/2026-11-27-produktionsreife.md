# Sitzung 2026-11-27 — Produktionsreife (B-023 bis B-026)

**Anlass:** Owner-Auftrag nach dem Review der lint-Umsetzung: „Probleme für productive-grade Qualität des Repos und aller Funktionalitäten beheben“. Plan: `pm/plans/2026-11-27-produktionsreife.md`. Branch: `feat/production-hardening` (nicht committet).

## Was getan wurde

- Gesamten Code gelesen (`wikitila.py`, `validate_catalog.py`, `wikitila_graph.py`, `install.sh`, Wrapper, CI) und elf Befunde (P1–P11) im Plan festgehalten.
- **ADR-006** Indexformat-Version: `INDEX_FORMAT` in `meta.format`, Vollneubau bei Abweichung, `check`/`status` melden es.
- **Konfiguration:** `check_cfg` prüft Typen gegen `DEFAULTS`, warnt bei unbekannten Sektionen/Schlüsseln.
- **Fehlerpfade:** `main` fängt `sqlite3.Error` (mit Hinweisen zu FTS5/beschädigtem Index), Strg-C, Broken Pipe; Python-Version und fehlendes sqlite3 werden vor allem anderen geprüft; `embed` meldet fehlendes numpy und Netzfehler; `--root` muss existieren; `-k ≥ 1`; alle Lesebefehle schließen die Verbindung.
- **Frontmatter:** gemeinsamer Helfer `frontmatter()` (BOM, leerer Block, Block am Dateiende) für build und lint; Schlüssel mit Ziffern/Bindestrich.
- **eval/validate_catalog:** gemeinsamer `load_jsonl` mit Zeilennummern, `pct` (Nearest-Rank), `--gate`, Antwortstatus-Ebene.
- **Demo-Korpus** mit Frontmatter, Katalog korrigiert und um einen description-Fall ergänzt; **CI** 3.14, Gate, lint, Installer-Idempotenz.
- **Installer/Wrapper:** `PYTHON`-Override, FTS5-Prüfung, leeres Register.
- Doku DE+EN (validation, installation, operations, agentic-setup-Zahlen), AGENTS.md (Gates, INDEX_FORMAT-Regel, Konfig-Regel), CHANGELOG, BACKLOG (B-023–B-027), STATUS.

## Was offen ist

- Release 0.4.0 (Owner): Commit/PR/Merge, `__version__`, Tag, Release-Worktree. Danach im Vault Vollneubau + Katalogmessung (B-027), vault-seitigen Linter durch `lint --all` ersetzen.
- B-022 Rest: Katalogfall nur über `status`.

## Was die nächste Sitzung wissen muss

- Die Negativfälle des Demo-Katalogs liefern weiterhin `belegt` (2/2 Falsch-Positive). Das ist ADR-005-konform und kein Gate-Kriterium; das Gate verlangt nur ein Abstention-Signal.
- `widersprüchlich` ist bei Authority-Fragen mit abgelöster Fassung im Ergebnis der **richtige** Status. Kataloge, die dort `belegt` erwarten, sind falsch.
- Lokal Gates mit `/usr/bin/python3` ausführen (siehe Memory `python3-im-path-ohne-sqlite`).
- `wikitila_graph.py build` nicht im Repo-Ordner „zum Testen“ starten: Graphify ist installiert und schreibt `graphify-out/`.
