---
name: indexformat-hash-reicht-nicht
description: Inkrementeller build per Datei-Hash übernimmt Parser-/Chunking-Änderungen nicht — deshalb INDEX_FORMAT (ADR-006)
type: pitfall
---
Bis 0.3.0 verarbeitete `build` nur Dateien mit geändertem SHA-1. Änderungen an `parse_doc`/`chunk_text` (0.3.0: kurze Abschnitte, Status-Feld) kamen nach einem Upgrade nur bei seither bearbeiteten Dateien an; Owner-Messungen nach Upgrades liefen auf einem Mischindex. **Warum:** Der Hash beschreibt den Inhalt, nicht die Verarbeitung. **Anwenden:** Bei jeder Änderung an dem, was build aus einer unveränderten Datei erzeugt, `INDEX_FORMAT` erhöhen; Messwerte am Vault erst nach dem Vollneubau werten (B-027). Verwandte Einträge: [[abnahme-misst-bestand-nicht-zufluss]]
