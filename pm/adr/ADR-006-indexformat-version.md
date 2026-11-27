# ADR-006: Indexformat-Version erzwingt Vollneubau

**Status:** angenommen · **Datum:** 2026-11-27 · **Bezug:** B-023, Plan 2026-11-27-produktionsreife

## Kontext

`build` arbeitet inkrementell: Eine Datei wird nur neu verarbeitet, wenn sich der SHA-1 ihres Inhalts geändert hat. Ändert eine neue Version von LLM-Wikitila, *was* aus einer unveränderten Datei entsteht (Frontmatter-Parsing, Chunking, Titelfeld, z. B. 0.3.0: kurze Abschnitte und Status-Feld; nächstes Release: BOM, leerer Frontmatter-Block, Schlüssel mit Bindestrich), erreicht diese Änderung nur Dateien, die seit dem Upgrade bearbeitet wurden. Der Index ist dann ein Mischstand aus altem und neuem Format. Messungen am Referenz-Vault nach einem Upgrade (B-010, B-015) messen damit nicht die installierte Version.

## Entscheidung

- `wikitila.py` führt die Konstante `INDEX_FORMAT` (Stand: `"3"`). `build` speichert sie in `meta.format`, zusätzlich `meta.version` (`__version__`).
- Weicht `meta.format` ab oder fehlt (Index älter als dieses ADR), leert `build` die Tabellen `t`, `chunks`, `files`, `emb`, `links`, `ent` und baut vollständig neu. Meldung auf stderr: `Indexformat … → …: Vollneubau` (mit Hinweis auf `embed`, falls Vektoren vorhanden waren).
- `check` meldet ein veraltetes Format als Drift, `status` als Hinweis.
- `INDEX_FORMAT` wird erhöht, sobald sich die Ausgabe von `build` für eine unveränderte Datei ändert. Reine Ranking-Änderungen (Suche) brauchen keine Erhöhung.

## Alternativen

- **Version (`__version__`) statt Format vergleichen:** jedes Patch-Release würde einen Vollneubau auslösen, auch ohne Formatänderung. Verworfen.
- **Hash über Inhalt + Code-Hash:** erkennt auch unbeabsichtigte Änderungen, löst aber bei jeder Code-Zeile einen Vollneubau aus. Verworfen.
- **Dokumentierter Hinweis „nach Upgrade `.wikitila/` löschen“:** verlässt sich auf Menschen und Agenten; genau das ist bisher unterblieben. Verworfen.

## Folgen

- Der erste `build` nach einem Upgrade mit Formatwechsel dauert so lange wie ein Erstaufbau (Referenz-Vault: Sekunden bis wenige Minuten). Vektoren müssen danach mit `embed` neu erzeugt werden.
- Indizes aus Versionen vor diesem ADR haben kein `meta.format` und werden einmalig neu aufgebaut.
- Verbindlich: Wer `parse_doc`, `chunk_text` oder die in `files`/`t` geschriebenen Felder ändert, erhöht `INDEX_FORMAT` und ergänzt den CHANGELOG.
