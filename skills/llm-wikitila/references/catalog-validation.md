# Katalog-Validierung mit LLM-Wikitila

Abnahmeeinheit ist die **belegte Aussage**, nicht die gefundene Datei. Der reine
Datei-Recall reicht nicht als Vertrauensnachweis.

## Drei Ebenen, ein Messwerkzeug

`validate_catalog.py` misst einen erweiterten Katalog auf drei Ebenen:

1. **Datei-Recall** — erwartete Datei unter den Top-k.
2. **Passagen-Präsenz** — enthält das Top-1-Ergebnis (volle Passagen) den antworttragenden
   Beleg (Feld `passage` = Liste exakter Teilstrings)?
3. **Negativ / Coverage** — wird bei fehlendem Wissen abgewiesen? Sind Nicht-Markdown-
   Dateien als Ausschluss geführt?

## Katalog-Schema (JSONL, eine Frage je Zeile)

```json
{"q":"…", "type":"stichwort|paraphrase|aktueller-stand",
 "kind":"positiv|authority|coverage|negativ",
 "expect":["relativer/pfad.md"], "passage":["exakter","Teilstring"],
 "answer":"belegt|widerspruechlich|belegt_gueltigkeit_unbestaetigt|nicht_belegt"}
```

- `kind=authority`: erwartete Datei ist die **aktuell gültige** Quelle; `passage`
  trägt den aktuellen Wert. Fehlschlag = Freshness-/Ablösungsproblem.
- `kind=coverage`: `expect` zeigt auf eine Nicht-Markdown-Datei. Sie ist erwartungsgemäß
  nicht im Index (Scope = Markdown) — der Befund dokumentiert den Ausschluss.
- `kind=negativ`: `expect` leer, `answer=nicht_belegt`. Ein nicht-leerer Top-1-
  Treffer ist ein Falsch-positiv; das Signal `unmatched_terms`/`top1_missing_terms`
  ist die Grundlage für die Abstention des Agenten.

## Aufruf

```bash
cd <ziel-ordner>
python3 <pfad>/validate_catalog.py --root . --catalog golden_catalog.jsonl
```

## Referenzwerte (AGANTILA-Vault, 50 Fälle)

| Ebene | Ergebnis |
|---|---|
| Datei-Recall (positiv+authority, n=36) | R@10 1,00, MRR 0,785 |
| Passagen-Präsenz (Top-1, volle Passagen) | 45 % |
| Abstention-Signal (Negativ) | 8/8 |

## Pflicht beim Erweitern

- Der Katalog ist die Abnahme und wächst bei neuen Erkenntnissen.
- Neue Fälle nur mit verifizierten, exakten Pfaden und Passage-Teilstrings.
- Ergebnisse in der Doku (README, Validierungsdokument) nachziehen.
- Datei-Recall ist kein Nachweis für Antwortqualität — Passagen und Status getrennt messen.
