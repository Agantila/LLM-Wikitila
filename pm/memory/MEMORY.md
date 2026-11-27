# Projektgedächtnis — Index

Eine Zeile pro Eintrag. Format und Regeln: `AGENTS.md` Abschnitt 5.

- [Nie auf dem echten Vault testen](nie-auf-echtem-vault-testen.md) — Evaluation und Härtung nur auf synthetischen Korpora
- [FTS5-UNINDEXED ist kein Index](fts5-unindexed-ist-kein-index.md) — `where path=?` auf `t` scannt alles, `chunks` verwenden
- [Graphify heißt auf PyPI graphifyy](graphify-pypi-name.md) — `pip install graphify` installiert ein fremdes Paket
- [read_text normalisiert CRLF](read-text-normalisiert-crlf.md) — Frontmatter in Windows-Dateien wird korrekt erkannt, kein Fix nötig
- [Negativ-Stichwörter nicht indexieren](negativ-stichwoerter-nicht-indexieren.md) — sie zerstören die lexikalische Abstention
- [Maskierung an der Ausgabe, nicht im Index](maskierung-an-der-ausgabe.md) — jedes neue Ausgabefeld durch `mk()` schicken
- [Synthetische Lastkorpora](synthetische-lastkorpora.md) — so wurden die Skalierungswerte gemessen
- [Workspace-Einsatz über Release-Worktree](workspace-einsatz-release-worktree.md) — produktive Vaults laufen auf einem Tag, Entwicklung nur hier; Repo nie in indexierten Ordner legen
- [Kurze Abschnitte werden verworfen](kurze-abschnitte-werden-verworfen.md) — `chunk_text` überspringt Abschnitte < `min_chunk_chars`, auch mit Überschrift (Passagen-Präsenz)
- [GitHub-Konto kommandobezogen wechseln](gh-konto-kommandobezogen-wechseln.md) — `GH_TOKEN` je Kommando statt `gh auth switch`, sonst pusht der Credential-Helper unter dem falschen Konto
- [Abnahme misst Bestand, nicht Zufluss](abnahme-misst-bestand-nicht-zufluss.md) — Schema-Drift entsteht trotz grüner Katalog-Abnahme, weil die Schreibseite nie geprüft wird
- [python3 im PATH ohne sqlite](python3-im-path-ohne-sqlite.md) — pyenv 3.10 ohne `_sqlite3`; Gates mit `/usr/bin/python3` laufen lassen
- [Indexformat: Hash reicht nicht](indexformat-hash-reicht-nicht.md) — Parser-Änderungen erreichen unveränderte Dateien nur über `INDEX_FORMAT` (ADR-006)
- [Katalog-Feld answer war ungeprüft](katalog-answer-feld-war-ungeprueft.md) — Authority-Fälle mit abgelöster Fassung sind `widersprüchlich`, nicht `belegt`
