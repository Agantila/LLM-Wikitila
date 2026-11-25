---
name: kurze-abschnitte-werden-verworfen
description: chunk_text verwirft Abschnitte unter min_chunk_chars komplett, auch mit Überschrift — antworttragende Kurzabschnitte gehen verloren
type: pitfall
---
`chunk_text` überspringt Abschnitte mit `len(sec) < min_chunk_chars` (Default 40) vollständig — auch wenn sie eine Überschrift tragen. „## Schrift\n\nBai Jamjuree.“ ist damit nicht auffindbar, obwohl Überschrift und Wert antworttragend sind.
**Warum:** Die Schwelle soll Rauschen filtern, trifft aber kurze Werte-Abschnitte (Font, Preis, Kennzahl) genau dort, wo die Passagen-Präsenz hängt.
**Anwenden:** Bei der Chunk-Auswahl mitdenken (B-018); ein Abschnitt mit Überschrift sollte eher in den Nachbar-Chunk gemischt als verworfen werden. Verwandt: [[negativ-stichwoerter-nicht-indexieren]]
