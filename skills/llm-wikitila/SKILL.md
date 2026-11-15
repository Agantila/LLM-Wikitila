---
name: llm-wikitila
description: Use when setting up or operating LLM-Wikitila search and graph on any project folder.
license: MIT
---

# LLM-Wikitila: schnelle, belegte Suche und lokaler Graph

Werkzeug: `wikitila.py` (Suche/Build/Status/Manifest/Check/Eval/Embed), `wikitila_graph.py` (lokale Graphify-Extraktion), `validate_catalog.py` (Validierung). Doku: `docs/` (deutsch + englisch). Agentenregeln: `AGENTS.md`.

## Wann laden

- Ein Ordner/Vault soll durchsuchbar werden (Suche, Graph, Second Brain, LLM Wiki).
- Graphify soll lokal mit Ollama laufen statt mit Cloud-Subagenten.
- Jemand fragt, ob ein Vector Store nötig ist.

## Ablauf in dieser Reihenfolge

0. **Erst nach Vorhandenem suchen, dann bauen.** Vor jedem Graph-Lauf über 5 Minuten Dauer, Nutzen und erwarteten Gewinn nennen (≈0,3 Dokumente/s) und klarstellen: die Suche trägt auch ohne Graph.
1. `.graphifyignore` anlegen/erweitern, bevor irgendetwas gebaut wird (Fremdcode, Kopien, `node_modules`, `*.js`).
2. `./install.sh <ziel-ordner>` (idempotent), dann `wikitila.py --root <ordner> build` und `search` testen.
3. `authority_register.json` befüllen — erst danach greifen `kanonisch`/`überholt durch`/`veraltet`.
4. Graph (optional): `wikitila_graph.py run --model maternion/ling-3.0-tiny:8b --workers 2`, dann `build`, dann `wikitila.py build`.
5. **Abnahme über einen selbst angelegten Katalog** (JSONL, ~50 Fälle), gemessen mit `validate_catalog.py` auf drei Ebenen. Schema und Ablauf: `references/catalog-validation.md`.

## Lehren (belegt)

- **Kein Vector Store als Dienst** für Korpora bis einige zehntausend Abschnitte: 26.000 Vektoren = 80 MB, Brute-Force 25 ms. Embedding optional und aus.
- **Kleine Modelle vergeben Relationsarten falsch:** Entitäten sind brauchbar, Relationen nur als `related_to`, `INFERRED`, 0,5.
- **Ollama arbeitet Anfragen nacheinander ab:** mehr als 2 Worker beschleunigen nichts. `think: false` + JSON-Schema (`format`).
- **Graphify überspringt Dateien mit `token`/`secret`/`password`/`credential` im Namen.** Wo Sensibles auffindbar bleiben soll, Prüfung ersetzen (siehe `wikitila_graph.py`).
- **`graph.json` wird beim Build überschrieben:** vorher sichern.
- **Graphify speichert Kanten ungerichtet:** beim Import beide Richtungen prüfen.
- **Dokument-IDs aus gekürztem Pfad kollidieren:** ID = gekürzter Pfad + Hash.
- **Gescheiterte Dokumente (≈0,5 %) nachholen:** zweiter Lauf mit größerem `WIKITILA_NUM_PREDICT` (1600) und `WIKITILA_NUM_CTX` (8192), 1 Worker. Cache macht Läufe fortsetzbar.
- **`graphify query` ist kein Dateifinder** (MRR 0,07): liefert Teilgraphen als Kontext. Für „wo steht das“ `wikitila.py search`, für Zusammenhänge `graphify path`/`explain`.
- **Datei-Recall ist keine Antwortqualität:** Passagen, Authority und Abstention getrennt messen (`validate_catalog.py`).
- **`score` ist RRF, keine Confidence.**
- **„Nichts gefunden“ ≠ „nichts vorhanden“:** Status `nicht_belegt`, nie „existiert nicht“.
- **Eigene neue Doku verfälscht den Katalog** (BM25 −0,03 MRR): Vergleiche nur im selben Korpusstand. Negativ-Teststichwörter nie in indexierte Doku schreiben.
- **Eval mit Decision-Modell kann Rückfälle verbergen:** identische Zahlen heißen HTTP-Fehler + Fallback. Fehlerzähler prüfen.
