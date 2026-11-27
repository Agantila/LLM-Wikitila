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
| `answer` | erwarteter Status: `belegt` · `widersprüchlich` (auch ASCII `widerspruechlich`) · `belegt_gueltigkeit_unbestaetigt` · `nicht_belegt`. Bei `kind=authority` mit abgelöster Fassung im Ergebnis ist `widersprüchlich` richtig (beide Werte, Auflösung sichtbar) |

- `kind=authority`: `expect` ist die **aktuell gültige** Quelle, `passage` trägt den aktuellen Wert.
- `kind=coverage`: `expect` zeigt auf eine Nicht-Markdown-Datei — erwartet wird, dass sie als Ausschluss geführt wird (Coverage-Entscheidung).
- `kind=negativ`: `expect` leer, `answer=nicht_belegt`.

## Messung

```bash
python3 validate_catalog.py --root . --catalog golden_catalog.jsonl [--gate]
```

Ebenen:

1. **Datei-Recall** — steht eine erwartete Datei unter den Top-k? (R@1/R@3/R@5/R@10, MRR, Latenz)
2. **Passagen-Präsenz** — trägt das Top-1-Ergebnis (volle Passagen) den antworttragenden Beleg?
3. **Coverage & Negativ** — sind Nicht-Markdown-Dateien als Ausschluss geführt? Wird bei fehlendem Wissen abgewiesen (Abstention-Signal)?
4. **Antwortstatus** — liefert die Suche den im Feld `answer` erwarteten Status?

**`--gate` (CI, Abnahme):** Exit 1, wenn ein positiv/authority-Fall nicht unter den Top-k steht, eine coverage-Datei fehlt, ein positiv/authority-Fall einen anderen Antwortstatus liefert oder ein Negativfall **ohne** Abstention-Signal bleibt. Dass Negativfälle trotzdem einen Treffer liefern, ist kein Gate-Kriterium: Das Antwort-Tor bleibt ein Signal, die Abstention trifft der Agent (ADR-005). Ein fehlerhafter Katalog (kein JSON, Pflichtfeld fehlt, unbekanntes `kind`) endet mit Exit 2 und Zeilennummer.

`wikitila.py eval golden.jsonl` misst nur den Datei-Recall und überspringt Fälle ohne `expect` (Negativfälle); für alle Ebenen `validate_catalog.py` nutzen.

Zusätzlich misst `validate_catalog.py` für `kind=negativ` die **Coverage-Note** (`term_coverage < 1,0`). Dieselbe Note liefert die Suche direkt mit, und ein billiger Pre-Flight prüft sie ohne Ranking:

```bash
python3 wikitila.py --root . coverage "Welche Safe Zones gelten für Pinterest?"
# -> Term-Abdeckung: 0.60 · Ohne ko-lokalen Beleg: pinterest
```

Die Note ist deterministisch (Ko-Lokation der Query-Begriffe im selben Chunk) und ersetzt keine Semantik — sie macht die Abstention des Agenten belegbar.

## Referenz-Messwerte (AGANTILA-Vault, 50-Fälle-Katalog)

| Ebene | Wert |
|---|---|
| Datei-Recall | R@10 **1,00**, MRR 0,785, p95 ~35 ms |
| Passagen-Präsenz (Top-1, volle Passagen) | 45 % |
| Abstention-Signal auf Negativ-Fällen | 8/8 |
| Unit-Tests | 18/18 (Stand der Messung; aktuell 79/79) |

**Zielabgleich:** R@10 erfüllt das Ziel ≥ 0,95. MRR 0,785 liegt **unter** dem Ziel 0,80 — offener Punkt im Backlog (`pm/BACKLOG.md`, B-010).

**Reproduzierbarkeit:** Die Referenzwerte stammen aus dem privaten Vault und sind aus dem Repo nicht nachmessbar. Die Werkzeugkette selbst lässt sich mit dem Demo-Korpus prüfen (läuft auch in der CI):

```bash
python3 wikitila.py --root examples/demo-corpus build
python3 validate_catalog.py --root examples/demo-corpus --catalog golden_catalog.example.jsonl --gate
python3 wikitila.py --root examples/demo-corpus lint --all      # Demo-Korpus erfüllt den Schreib-Vertrag
```

## Messgrenzen (ehrlich)

- Ein selbst angelegter Katalog enthält Verzerrungen durch Fragenwahl und bekannte Inhalte; er wird bei neuen Erkenntnissen erweitert.
- Nahe-am-Thema-Negative („Safe Zones für Pinterest“) sind ohne Semantik nicht lexikalisch abweisbar — ihre Stichwörter stehen oft selbst im Korpus, und Modelle wurden gemessen schlechter. Die Signale `unmatched_terms`/`top1_missing_terms` liefern dem Agenten die Diskriminanz; die Abstention trifft der Agent.
- Datei-Recall ist **kein** Nachweis für Antwortqualität — deshalb werden Passage und Status getrennt gemessen.
- Schreibst du Negativ-Teststichwörter („Pinterest“, „Snapchat“ …) in eine indexierte Messdoku, sind sie fortan im Korpus „vorhanden“ und die lexikalische Abstention erkennt sie nicht mehr als fehlend.
