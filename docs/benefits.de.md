# Belegte Vorteile (Deutsch)

Gegenüberstellung von LLM-Wikitila mit einem **reinen Graph-Rack (GraphRAG)** und einer **reinen Link-Suche** — jeder Vorteil mit Messwert aus dem AGANTILA-Vault (50-Fragen-Katalog, Stand 2026-11-14).

## Vergleichsbasis

| Ansatz | Was es macht | Gemessen |
|---|---|---|
| Graph-Rack / GraphRAG (`graphify query`) | Teilgraph als Kontext, Nachbarschaften, Wiki-Zusammenfassungen | R@10 **0,25** (MRR 0,067); älterer Graph R@10 **0,00** |
| Reine Link-Suche | folgt nur Verweisen, kein Volltext-Ranking | im Stack nur als kleiner Booster (Gewicht 0,05) |
| **LLM-Wikitila** | Volltext + deterministische Verknüpfungen + Authority/Freshness + Belegvertrag | R@10 **1,00**, MRR 0,785, p95 ~35 ms |

## Die sieben Vorteile

1. **Deutlich höhere Trefferquote.** R@10 1,00 gegenüber 0,25 beim Graph-Rack. Der Graph allein findet „welche Datei beantwortet das“ kaum; er ist Navigation, nicht Finder.
2. **Schnell und deterministisch.** ~20 ms, ohne Dienst, GPU oder Docker; BM25 und Link-Graph sind reproduzierbar.
3. **Beleg statt Behauptung.** Jede Antwort trägt Datei, Überschrift und Originalpassage. Graph-Zusammenfassungen allein sind kein Beleg — sie können Fehler verdichten.
4. **Gültigkeit statt nur Relevanz.** Graph-RAG kennt Relevanz, nicht Geltung. Das Authority-Register entscheidet, welche Quelle maßgeblich und noch aktuell ist (Preis 299/499/699 → 549/899/1.199 automatisch aufgelöst).
5. **Kontrolliertes „nicht belegt“.** Das Antwort-Tor weist fehlendes Wissen aus (Status + `unmatched_terms`/`top1_missing_terms`), statt eine plausible Falschantwort zu liefern.
6. **Kein Vector Store nötig.** Ein Embedding brachte nur in einer frühen Messung bis +0,18 MRR; die Endpipeline erreicht R@10 1,00 ohne Vektoren. Kein Dienst, keine 80-MB-Vektordatenbank.
7. **Kein Modell im Laufzeitpfad.** Decision-Modelle verschlechterten Ranking (MRR 0,659/0,617 gegen 0,794) und Antwort-Tor (AUC 0,70/0,78 gegen 0,94). Modelle bleiben dem einmaligen Graph-Aufbau und einem optionalen Pflege-Lint vorbehalten.

## Grenzen (ehrlich)

- Die Zahlen stammen aus einem 50-Fragen-Selbstkatalog mit bekannten Inhalten; sie belegen die **Suchqualität**, nicht jede fachliche Richtigkeit.
- Nahe-am-Thema-Abstention ist eine semantische Aufgabe des Agenten (Signale liefert der Stack).
- Authority-Aussagen wirken erst, wenn das Register vom Owner gepflegt wird.
