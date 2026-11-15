---
name: negativ-stichwoerter-nicht-indexieren
description: Stichwörter aus Negativ-Testfällen nie in indexierte Dokumente schreiben
type: pitfall
---
Stehen Negativ-Stichwörter („Pinterest“, „Snapchat“, „Zimbabwe“) in einer indexierten Datei, gelten sie als „im Korpus vorhanden“, und `unmatched_terms` meldet sie nicht mehr.
**Warum:** Die Abstention ist rein lexikalisch (ADR-001, kein Modell im Laufzeitpfad).
**Anwenden:** Mess- und Review-Dokumente mit solchen Wörtern gehören nicht in den gemessenen Ordner. Im Demo-Korpus kommen die Negativ-Stichwörter des Beispielkatalogs nicht vor. Verwandt: [[nie-auf-echtem-vault-testen]]
