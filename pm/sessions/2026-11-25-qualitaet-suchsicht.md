# Sitzung 2026-11-25 — Suchsicht / Qualität (MRR, Passagen-Präsenz, Abstention)

**Anlass:** Prüfung der Aussage aus Hermes-Session `local-cf6dd96c…1919a` und Umsetzung des Plans `pm/plans/2026-11-25-qualitaet-mrr-passage-abstention.md` (Revision 2 nach Vergleich mit NVIDIA Auto Ontology).

## Was getan wurde

- **Prüfung:** Die Aussage (MRR 0,778 vs. 0,80, Passagen-Präsenz 42 %, semantische Abstention 7/8 FP, „Code-Arbeit, kein Vault-Fix“) ist korrekt und vollständig belegt.
- **Vergleich mit NVIDIA Auto Ontology:** `check_answerable` (Coverage-Note + `uncovered`), Antwort-Trace und Zertifizierungs-Marken als Qualitätsvorlage übernommen — deterministisch, ohne Modelle/Embeddings/Services (ADR-001).
- **Implementiert (wikitila.py, validate_catalog.py, test_wikitila.py):**
  - `tokens()` behält mehrstellige Zahlen; einzelne Ziffern entfallen weiter.
  - Frontmatter-`status`/`superseded_by` werden in den FTS-Titel indexiert („proposed“ auffindbar).
  - `file_scores` aggregiert bis zu drei Chunks je Datei (MRR).
  - Authority-Wert-Chunks werden für alle Register-Einträge bevorzugt (Passagen-Präsenz).
  - Neue `coverage_grade()`: `term_coverage`/`uncovered`/`uncovered_hint` (Ko-Lokation im selben Chunk); in `search` und im neuen Befehl `coverage` verfügbar.
  - Query-`trace` (`query_tokens`, `authority`, `gate`) und Register-Metadaten (`authority`, `verified_at`) je Treffer.
  - `validate_catalog.py`: neue Zeile „Coverage-Note < 1,0“ für `kind=negativ`.
- **Gates:** 37 Unit-Tests grün; Demo-Katalog MRR 1,000; Coverage-Note 2/2 (< 1,0) auf den Beispiel-Negativen.

## Was offen ist

- **Owner-Messung am Vault** (MRR ≥ 0,80, Passagen-Präsenz, Coverage-Note auf den 8 Negativ-Fällen) — nur der Owner misst das.
- **ADR-005 (Entscheidung):** deterministische Coverage-Regel im Antwort-Tor oder Signal-only. Bisher bewusst Signal-only.
- **B-011** (inkrementeller Link-Graph), **B-013** (Release-Signierung), **B-018** (kurze Abschnitte unter `min_chunk_chars`).

## Für die nächste Sitzung wichtig

- Beim Testen gefunden: `chunk_text` verwirft Abschnitte unter `min_chunk_chars`=40 komplett — auch mit Überschrift („## Schrift · Bai Jamjuree“ unauffindbar). Als B-018 festgehalten; betrifft die Passagen-Präsenz.
- Die Coverage-Note ist ein **Signal**, keine Semantik: sie ersetzt die Agenten-Abstention nicht (ADR-001), sie macht sie belegbar.
