# Sitzung 2026-11-27 — Release 0.4.0 und Vault-Umstellung (B-027)

**Anlass:** Owner-Auftrag „mache alles, du bist der Operator“: Merge, Release, Release-Worktree, Vault-Build, Katalogmessung, Ersatz des vault-eigenen Linters.

## Was getan wurde

- PR #1 (lint + Produktionsreife) nach grüner CI gemergt; PR #2 `release: 0.4.0` (Version, CHANGELOG, Roadmap) gemergt; Tag `v0.4.0` (annotiert) und GitHub-Release mit Upgrade-Hinweis veröffentlicht. Alle Aktionen als Konto Agantila (`GH_TOKEN` je Kommando).
- Release-Worktree auf `v0.4.0` umgestellt.
- Vault: Wrapper `./wikitila` auf `/usr/bin/python3` (das `python3` im PATH ist pyenv 3.10 ohne sqlite3), `PYTHON`-Override. `wikitila.toml` um `[lint]` ergänzt (Pflichtfelder `type/title/description`, `since = 2026-08-28`, Ausnahmeliste des alten Reports als Muster).
- Katalogmessung vor und nach dem Vollneubau: identisch (R@10 0,94 · MRR 0,682 · Passagen Top-1 42 % · Abstention-Signal 8/8 · Antwortstatus 27/44). Die erwarteten Dateien der 2 Fehltreffer existieren → Ranking-Thema (B-010).
- Vault-OKF-Linter ersetzt: alte Skripte nach `_Skills/_OKF-Frontmatter/_Python_Tools/_Archiv/` kopiert; `okf_vault_report.py` formatiert jetzt nur noch `lint --all --json` als Markdown (gleicher Pfad und gleiche Argumente, systemd-Unit unverändert); `okf_linter.py` ist eine Weiterleitung auf `wikitila lint` für alte Aufrufe. Verweise in Vault-AGENTS.md, Vault-Konventionen, OKF-README/Checkliste/Vorlage, Stack-Übersicht/Betrieb und zwei Hermes-Skills umgestellt. systemd-Lauf einmal manuell ausgelöst: erfolgreich.
- lint-Ergebnis Vault: 775 geprüft, 105 konform, 90 Hinweise, 580 Verstöße (alter Report: 749 / 96 / 66 / 587).

## Was offen ist

- Vault-Änderungen sind **nicht committet** (der Vault hatte bereits 37 offene Änderungen des Owners, u. a. die unversionierte OKF-Arbeit).
- B-010: Fehltreffer analysieren. B-015/B-016: Antwortstatus-Abweichungen im Owner-Katalog prüfen.
- Nicht mehr automatisch geprüft (früher Hinweise im Vault-Linter): Actor-Form `generated.by`, ISO-8601-Daten, `tags` als Liste.

## Was die nächste Sitzung wissen muss

- Der Report `STATUS_OKF_Frontmatter.md` liegt im Index und rankt bei Frontmatter-Fragen auf Platz 1 (er enthält viele Dateinamen und den lint-Aufruf).
- Sicherungen der geänderten Vault-/Skill-Dateien lagen nur im Sitzungs-Scratchpad; die alten Linter-Skripte liegen dauerhaft im `_Archiv`.
