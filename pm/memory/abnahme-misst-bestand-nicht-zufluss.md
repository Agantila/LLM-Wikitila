---
name: abnahme-misst-bestand-nicht-zufluss
description: Katalog-Abnahme prüft den Bestand, nicht die Schreibseite — Schema-Drift entsteht trotz grüner Abnahme
type: learning
---
Die Katalog-Abnahme (validate_catalog.py) misst die Auffindbarkeit des **Bestands** zum Messzeitpunkt. Ob neue Dateien mit suchtragendem Frontmatter (title/description/status) angelegt werden, prüft sie nicht. **Warum:** Im Referenz-Vault drifteten 587 Dateien im Geltungsbereich aus dem Schema, obwohl die Abnahme gruen war — die Prompts (Setup/Upgrade) hatten keinen Schreib-Vertrag-Schritt. **Anwenden:** Bei jeder Einrichtung/Migration den Schreib-Vertrag-Schritt aus dem Review 2026-11-27 (Abschnitt 3) mitliefern; Frontmatter-Lint als Teil der Einrichtung betrachten, nicht als Vault-Sonderlocke. Verwandte Einträge: [[nie-auf-echtem-vault-testen]]
