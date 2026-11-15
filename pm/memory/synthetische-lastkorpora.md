---
name: synthetische-lastkorpora
description: Skalierungswerte stammen aus Zufallskorpora mit 5 Abschnitten pro Datei; Referenz zum Nachmessen
type: reference
---
Lastkorpus: N Dateien in 50 Ordnern, je 5 Abschnitte mit 60 Zufallswörtern aus 4.000 Wörtern plus einem Wikilink. Messwerte am 2026-11-15 (nach ADR-002): Build für 100, 1.000 und 10.000 Dateien 0,0 s, 0,2 s und 3,2 s; Query p50 bei 10.000 Dateien 3 ms. Bei Termen mit ca. 1.500 Treffern liegt eine Query bei 50 ms (BM25 bewertet alle Treffer, B-012).
**Warum:** Echte Vault-Zahlen dürfen nicht im Repo erhoben werden ([[nie-auf-echtem-vault-testen]]).
**Anwenden:** Für Vorher-nachher-Vergleiche dieselbe Korpusform verwenden. Die Werte zeigen Größenordnungen, keine Vault-Latenz.
