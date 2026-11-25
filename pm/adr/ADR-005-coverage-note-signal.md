# ADR-005: Coverage-Note ist ein Signal, kein Antwort-Tor-Kriterium

**Status:** angenommen · **Datum:** 2026-11-25 · **Bezug:** B-016, Plan 2026-11-25

## Kontext
Nahe-am-Thema-Fragen („Welche Safe Zones gelten für Pinterest?“) lieferten bisher `answer_status = belegt`, obwohl die spezifische Frage nicht beantwortet ist (7/8 Falsch-positive im 50-Fälle-Katalog). Die Vorlage NVIDIA Auto Ontology löst das mit `check_answerable`: eine Coverage-Note (Anteil gedeckter Frage-Begriffe) plus „uncovered“-Begriffe, bevor überhaupt abgefragt wird. ADR-001 schließt ein Modell im Laufzeitpfad aus und legt fest, dass die Abstention der Agent trifft.

## Entscheidung
Der Stack berechnet eine **deterministische Coverage-Note** (`term_coverage` ∈ [0,1] plus `uncovered`, Ko-Lokation der Query-Begriffe im selben Chunk) und legt sie jedem `search`-Ergebnis bei; zusätzlich prüft der Befehl `wikitila.py coverage "Frage"` die Abdeckung ohne Ranking. Die Note **ändert `answer_status` nicht** — die vier Status bleiben unverändert, die Abstention bleibt Aufgabe des Agenten.

## Alternativen
- Coverage-Regel im Antwort-Tor (`nicht_belegt`, wenn kein Chunk die signifikanten Begriffe gemeinsam trägt): würde den Vier-Status-Vertrag (ADR-001 Punkt 5) ändern und bräuchte eine Messung am Owner-Vault, um Falsch-Abstentionen (Legitim-Fragen mit getrennten Begriffen) auszuschließen. Bis dahin verworfen, als Folgeoption offen.
- Embedding-/Modell-basierte Abdeckung (wie Auto Ontologys Entitäten-Extraktion): widerspricht ADR-001 (kein Modell, kein Vector-Store).

## Folgen
`term_coverage`/`uncovered` sind Teil des Ausgabevertrags; `validate_catalog.py` misst sie für `kind=negativ` (Ziel: alle Negativ-Fälle < 1,0). Die Ko-Lokation ist Chunk-Ebene und keine Semantik — sie ersetzt die Agenten-Abstention nicht, sondern macht sie belegbar. Eine spätere Verschärfung des Antwort-Tors ist nur über ein neues ADR mit Messung möglich.
