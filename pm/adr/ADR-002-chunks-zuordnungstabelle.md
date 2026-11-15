# ADR-002: Zuordnungstabelle `chunks` statt Pfadsuche in FTS5

**Status:** angenommen · **Datum:** 2026-11-15 · **Bezug:** F3, F4, B-102

## Kontext
Die Spalte `path` der FTS5-Tabelle `t` ist `UNINDEXED`. `where path=?` liefert `SCAN t VIRTUAL TABLE`, also einen vollständigen Scan (12,4 ms pro Aufruf bei 50.000 Abschnitten). Der Build löschte so pro geänderter Datei, was ihn quadratisch machte (10.000 Dateien: 65,5 s). Jede Suche lud außerdem die komplette Zuordnung rowid→Pfad (26,5 ms).

## Entscheidung
Normale Tabelle `chunks(cid integer primary key, path text)` mit Index `chunks_path`. Beim Einfügen in `t` wird `lastrowid` mit dem Pfad in `chunks` geschrieben. Löschen und Nachschlagen pro Datei laufen über `chunks` und dann per `rowid` in `t`. Die Suche holt Pfade nur für Kandidaten-rowids. `meta.schema = '2'` markiert das neue Schema. Fehlt der Eintrag, füllt `connect()` `chunks` einmalig aus `t` (Migration).

## Alternativen
- FTS5 mit `content=`-Tabelle (external content): größerer Umbau, Trigger-Pflege, kein zusätzlicher Nutzen für die Laufzeit.
- `path` indexiert in FTS5: macht Pfade zu durchsuchbaren Tokens und verändert das Ranking (verstößt gegen ADR-001, Ranking unverändert lassen).

## Folgen
Build 10.000 Dateien 3,2 s, Query p50 3 ms. Der Index wird etwa 7 % größer (59 → 63 MB). Ranking und Ergebnisse bleiben unverändert (alle bestehenden Tests grün). `t` und `chunks` müssen konsistent bleiben, das prüft `test_f3_chunks_mapping_stays_consistent`.
