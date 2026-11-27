---
name: chunk-summe-verschlechtert-ranking
description: Mehrere Chunk-Treffer je Datei im Dateiscore zu summieren (oder Token-Abdeckung zu belohnen) senkt MRR deutlich — bester Chunk gewinnt
type: learning
---
Gemessen 2026-11-27 am Referenz-Vault (36 Recall-Fälle): 3 Chunks je Datei MRR 0,682 / R@10 0,94, 2 Chunks 0,713, abklingende Summe 0,715–0,719, **1 Chunk 0,764 / 1,00**; Token-Abdeckungs-Bonus auf 1 Chunk 0,704–0,741. **Warum:** Lange, allgemeine Dateien sammeln viele schwache Treffer und decken mehr Begriffe ab; die kurze präzise Zieldatei verliert. Am Demo-Korpus ist das unsichtbar (zu klein) — deshalb kam die Summe in 0.3.0 ungemessen durch. **Anwenden:** Ranking-Änderungen nie nur am Demo-Korpus abnehmen; vor dem Release den Owner-Katalog messen. `rank.chunks_per_file` existiert nur für Vergleichsmessungen. Verwandte Einträge: [[abnahme-misst-bestand-nicht-zufluss]], [[indexformat-hash-reicht-nicht]]
