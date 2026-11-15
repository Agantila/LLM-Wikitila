---
name: nie-auf-echtem-vault-testen
description: Evaluation, Benchmarks und Härtungstests nur auf synthetischen Korpora, nie auf dem Owner-Vault
type: decision
---
Tests, Benchmarks und Härtungsproben laufen ausschließlich in temporären Ordnern oder auf `examples/demo-corpus/`.
**Warum:** Läufe auf dem echten Vault verzerren die Katalogwerte (Negativ-Stichwörter landen in Doku) und können private Inhalte in Logs und Ausgaben bringen.
**Anwenden:** Referenzwerte des Vaults (R@10, MRR) misst nur der Owner. Agenten zitieren sie, messen sie aber nicht nach. Verwandt: [[negativ-stichwoerter-nicht-indexieren]]
