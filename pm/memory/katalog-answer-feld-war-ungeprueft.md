---
name: katalog-answer-feld-war-ungeprueft
description: Das answer-Feld im Katalog wurde bis 2026-11-27 nie geprüft; der Beispielkatalog erwartete bei Authority-Fällen fälschlich belegt
type: learning
---
`validate_catalog.py` dokumentierte `answer`, wertete es aber nicht aus. Der erste Abgleich zeigte: Authority-Fälle mit abgelöster Fassung im Ergebnis liefern `widersprüchlich` — vertragsgemäß (beide Werte, Auflösung sichtbar) —, der Beispielkatalog erwartete `belegt`. **Warum:** Ungeprüfte Felder veralten unbemerkt. **Anwenden:** Bei Owner-Katalogen nach dem Upgrade die Ebene „Antwortstatus“ lesen; Abweichungen bei Authority-Fällen sind meist Katalogfehler, nicht Codefehler. Negativfälle mit `belegt` sind ADR-005-konform. Verwandte Einträge: [[abnahme-misst-bestand-nicht-zufluss]]
