---
name: fts5-unindexed-ist-kein-index
description: Spalte path der FTS5-Tabelle t ist UNINDEXED, Filter darauf scannen die ganze Tabelle
type: pitfall
---
`select … from t where path=?` ergibt `SCAN t VIRTUAL TABLE` (12 ms pro Aufruf bei 50.000 Abschnitten). Das machte den Build quadratisch.
**Warum:** `UNINDEXED` heißt nur „nicht tokenisieren“, nicht „mit B-Baum-Index“.
**Anwenden:** Pfad-Lookups immer über die Tabelle `chunks` (`chunk_ids()`, `delete_doc()`) und dann `rowid in (…)` auf `t`. Siehe ADR-002. Verwandt: [[synthetische-lastkorpora]]
