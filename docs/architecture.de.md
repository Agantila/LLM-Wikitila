# Architektur (Deutsch)

LLM-Wikitila ist ein **lokaler, evidenzorientierter Hybrid**: deterministische Volltextsuche + Authority-/Freshness-Auflösung + optionaler Wissensgraph. Alle Komponenten laufen lokal, ohne Dienst und ohne Modell im Laufzeitpfad der Suche.

## Komponenten

| Baustein | Rolle | Technik |
|---|---|---|
| **Suchkern** | Volltext-Ranking | SQLite FTS5 / BM25, Wortstamm-Präfix, Gewichte Titel 6 · Überschrift 3 · Text 1 |
| **Dateiname** | Identifier auffindbar (ADR-Nummern u. ä.) | Dateinamen-Stamm wird mitindexiert + kleiner Booster |
| **Link-Graph** | deterministische Verknüpfungen | Dateinamen, Wikilinks, Markdown-Links, ADR-Nummern — ohne LLM |
| **Entitätsgraph** | kleiner Ranking-Booster | Graphify-Entitäten (Dokument → Entität), Gewicht 0,05 |
| **Authority-Register** | kanonische Quelle, Ablösung, Gültigkeit | `authority_register.json` (Owner-geführt) |
| **Antwort-Tor** | vier Antwortstatus + Abstention-Signale | modellfrei, deterministisch |
| **Source-Manifest** | Coverage-Report | `manifest` → `.wikitila/source_manifest.json` |
| **Index-/Quellstand-Abgleich** | Drift erkennen | `check` (neu/geändert/entfernt) |
| **Wissensgraph** (optional) | Navigation, Querbezüge, Lint-Kandidaten | Graphify + kleines lokales Modell, ohne Thinking |

## Datenfluss

```
Projekt-Ordner (Markdown, unverändert, kanonisch)
   │  .graphifyignore (eine Ausschlussliste für Suche und Graph)
   ▼
wikitila_graph.py (optional)        wikitila.py build
   Ollama ohne Thinking                 Abschnitte → FTS5/BM25
   Dokument → Entitäten                 Link-Graph + Entitäts-Graph
   ▼                                    ▼
graphify-out/graph.json            .wikitila/index.db (eine SQLite-Datei)
   (Navigation: path, explain)         + authority_register.json (Owner)
   ▼                                    ▼
wikitila.py search "Frage"
   BM25 → Dateiname → Graph-Booster → Authority-Register → Antwort-Tor
   Ausgabe: Datei, Überschrift, Originalpassagen, Flags, answer_status
```

## Design-Entscheidungen (mit Messbeleg)

1. **Kein Vector-Store-Dienst.** 26.000 Abschnitte als Vektoren sind 80 MB; Brute-Force braucht 25 ms. Ein Embedding brachte nur in einer frühen Messung mit großen Abschnitten bis +0,18 MRR; in der Endpipeline wurde es nicht gebraucht, um R@10 1,00 zu erreichen. Falls je nötig: Vektoren als Tabelle in derselben SQLite-Datei (optional, aus).
2. **Kein Modell im Laufzeitpfad.** Decision-Modelle (`laya:latest`, `tev1:0.8b`) verschlechterten Ranking (MRR 0,659/0,617 gegen 0,794) und Antwort-Tor (AUC 0,70/0,78 gegen 0,94). Modelle dienen nur dem Graph-Aufbau (einmalig) und optional einem Pflege-Lint.
3. **Authority ≠ Relevanz.** BM25, Linkzahl, Graphzentralität und Datum legen keine fachliche Geltung fest. Nur das Owner-geführte Register entscheidet `canonical`/Ablösung/Gültigkeit.
4. **RRF ≠ Confidence.** Der sichtbare `score` ist ein Rangwert (Reciprocal Rank Fusion), keine Wahrscheinlichkeit. Das Antwort-Tor nutzt `bm25_top` und Struktur-Signale, nie den RRF-Wert als Prozentzahl.
5. **„Nichts gefunden“ ≠ „nichts vorhanden“.** Fehlende Treffer erlauben keine Nichtexistenz-Aussage. Der Status ist `nicht_belegt`, nie „existiert nicht“.
6. **Belegte Aussage als Abnahmeeinheit.** Eine richtige Datei ohne antworttragende Passage ist kein Treffer. Deshalb werden bis zu drei Originalpassagen je Datei ausgeliefert.

## Antwortvertrag

| Status | Bedeutung |
|---|---|
| `belegt` | Datei, Überschrift und zitierte Originalpassage vorhanden |
| `widersprüchlich` | mehrere Werte gefunden; Auflösung sichtbar (`überholt durch`, `kanonisch`) |
| `belegt_gueltigkeit_unbestaetigt` | Beleg vorhanden, fachliche Gültigkeit offen (`proposed`, nicht bestätigt) |
| `nicht_belegt` | keine belastbare Antwort im Repository |

Signale für den Agenten: `unmatched_terms` (Begriff fehlt im gesamten Korpus), `top1_missing_terms` (Begriff fehlt im Top-1-Ergebnis), `bm25_top` (roher Relevanzwert). Nahe-am-Thema-Fragen („Safe Zones für Pinterest“) sind ohne Semantik nicht lexikalisch abweisbar — der Agent trifft die Abstention auf Basis dieser Signale.
