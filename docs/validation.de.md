# Validierung (Deutsch)

Die Abnahme läuft über einen **selbst angelegten Fragenkatalog** (JSONL), gemessen mit `validate_catalog.py` auf drei Ebenen. Ein separates externes Golden Set ist nicht nötig — der Katalog ist die Abnahme und wächst bei neuen Erkenntnissen.

## Katalog-Schema (eine Frage je Zeile)

```json
{"q":"Wie hoch ist der aktuelle Preis?","type":"aktueller-stand","kind":"authority",
 "expect":["doku/preise_aktuell.md"],"passage":["549"],"answer":"belegt"}
```

| Feld | Bedeutung |
|---|---|
| `q` | die Frage |
| `type` | `stichwort` · `paraphrase` · `aktueller-stand` |
| `kind` | `positiv` · `authority` · `coverage` · `negativ` |
| `expect` | erwartete Antwortdateien (Pfade relativ zum Ordner) |
| `passage` | exakte Teilstrings, die in der ausgelieferten Passage stehen müssen |
| `answer` | erwarteter Status: `belegt` · `widersprüchlich` · `belegt_gueltigkeit_unbestaetigt` · `nicht_belegt` |

- `kind=authority`: `expect` ist die **aktuell gültige** Quelle, `passage` trägt den aktuellen Wert.
- `kind=coverage`: `expect` zeigt auf eine Nicht-Markdown-Datei — erwartet wird, dass sie als Ausschluss geführt wird (Coverage-Entscheidung).
- `kind=negativ`: `expect` leer, `answer=nicht_belegt`.

## Messung

```bash
python3 validate_catalog.py --root . --catalog golden_catalog.jsonl
```

Drei Ebenen:

1. **Datei-Recall** — steht eine erwartete Datei unter den Top-k? (R@1/R@3/R@5/R@10, MRR, Latenz)
2. **Passagen-Präsenz** — trägt das Top-1-Ergebnis (volle Passagen) den antworttragenden Beleg?
3. **Coverage & Negativ** — sind Nicht-Markdown-Dateien als Ausschluss geführt? Wird bei fehlendem Wissen abgewiesen (Abstention-Signal)?

## Referenz-Messwerte (AGANTILA-Vault, 50-Fälle-Katalog)

| Ebene | Wert |
|---|---|
| Datei-Recall | R@10 **1,00**, MRR 0,785, p95 ~35 ms |
| Passagen-Präsenz (Top-1, volle Passagen) | 45 % |
| Abstention-Signal auf Negativ-Fällen | 8/8 |
| Unit-Tests | 18/18 |

## Messgrenzen (ehrlich)

- Ein selbst angelegter Katalog enthält Verzerrungen durch Fragenwahl und bekannte Inhalte; er wird bei neuen Erkenntnissen erweitert.
- Nahe-am-Thema-Negative („Safe Zones für Pinterest“) sind ohne Semantik nicht lexikalisch abweisbar — ihre Stichwörter stehen oft selbst im Korpus, und Modelle wurden gemessen schlechter. Die Signale `unmatched_terms`/`top1_missing_terms` liefern dem Agenten die Diskriminanz; die Abstention trifft der Agent.
- Datei-Recall ist **kein** Nachweis für Antwortqualität — deshalb werden Passage und Status getrennt gemessen.
- Schreibst du Negativ-Teststichwörter („Pinterest“, „Snapchat“ …) in eine indexierte Messdoku, sind sie fortan im Korpus „vorhanden“ und die lexikalische Abstention erkennt sie nicht mehr als fehlend.
