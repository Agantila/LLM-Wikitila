# Plan: Qualitätslücken ganzheitlich beheben — MRR, Passagen-Präsenz, Abstention und die Suchsicht als semantische Schicht

**Datum:** 2026-11-25 (Revision 2 nach Vergleich mit NVIDIA Auto Ontology) · **Backlog:** B-010 (MRR), neu: B-015 (Passagen-Präsenz), B-016 (Abstention), B-017 (Suchsicht/Trace) · **Status:** 🟡 · **Branch:** `feat/qualitaet-suchsicht`

## Ziel

Die drei dokumentierten Produkt-Lücken aus der Hermes-Session `local-cf6dd96c…1919a` (2026-11-24) werden über **einen gemeinsamen Umbau der Suchsicht** (nicht des Vaults) behoben. Maßstab ist das Suchsicht-Versprechen von NVIDIA Auto Ontology — *deterministische Query-Erzeugung, bessere Kontext-Auslieferung, erklärbare Ergebnisse* — übertragen auf eine **modellfreie, stdlib-only** Architektur. Danach gilt, gemessen am Owner-Vault (50-Fälle-Katalog):

| Kennzahl | Ist (2026-11-24) | Ziel |
|---|---|---|
| MRR (Datei-Recall, n=36) | 0,778 | ≥ 0,80 |
| Passagen-Präsenz (Top-1, volle Passagen) | 42 % | deutlich höher, Zielwert nach erster Messung festlegen |
| Falsch-positive bei Nahe-am-Thema-Negativen | 7/8 (88 %) | 0–2/8 über eine Coverage-Note (deterministisches `check_answerable`-Analogon) |
| Coverage-Note (`term_coverage` + `uncovered`) | fehlt | für jeden `search` vorhanden, für Negativ-Fälle < 1,0 |

**Abnahmekriterium:** Alle Gates grün (Unit-Tests, Demo-Katalog), dazu ein neuer synthetischer Qualitäts-Korpus im Repo, der die Lücken reproduziert und die Verbesserung belegt. Die endgültigen Zahlen misst der Owner am echten Vault (Vorgabe: nie im Repo auf dem Vault messen).

## Kontext

### Prüfergebnis der Aussage aus der Session

Die Aussage ist **korrekt und vollständig belegt**:

- **MRR 0,778 vs. Ziel 0,80 (B-010)** — stimmt. `B-010` im Backlog, `pm/STATUS.md`, `docs/validation.de.md:46`. Der Wert driftet leicht (0,785 → 0,776 → 0,778), bleibt aber dauerhaft unter 0,80.
- **Passagen-Präsenz 42 %** — stimmt. Messung: „Top-1-Datei, volle Passagen: 14/33 (42 %)“. Doku nennt den älteren Wert 45 %.
- **Semantische Abstention 7/8 Falsch-positive** — stimmt. Messung: „Falsch-positive (keine Abstention): 7/8 (88 %)“. Als bekannte Grenze dokumentiert (`docs/architecture.de.md:59`, `docs/validation.de.md:58`, `docs/benefits.de.md:26`).
- **„brauchen Code-Arbeit, keinen Vault-Fix“** — stimmt. Alle drei sitzen in `wikitila.py` (`search`), nicht im Vault-Inhalt.

### Vergleich: NVIDIA Auto Ontology als Qualitätsvorlage

[github.com/NVIDIA/auto-ontology](https://github.com/NVIDIA/auto-ontology) (Apache-2.0) löst dasselbe Kernproblem auf Datenbanken: *Begriffe → Ort → Verbindungen → Berechnung → Herkunft → Zertifizierung* als Ontologie, plus eine Suchsicht für Agenten. Vier Elemente sind die Vorlage für LLM-Wikitila:

1. **`check_answerable`** (`POST /api/question-entity-coverage`): ein billiger Pre-Flight, der *nicht* die eigentliche Abfrage ausführt, sondern eine **Coverage-Note** vergibt: `coverage` ∈ [0,1] = Anteil der Frage-Entitäten mit Treffer, dazu `uncovered_entities` („no term covers ‚ad spend‘“). Der Agent fragt bei niedriger Coverage nach oder bietet den nächstgelegenen abgedeckten Sachverhalt an. **Das ist exakt das fehlende Stück für die 7/8 Nahe-am-Thema-Falsch-Positiven.** Wichtig: Der finale Coverage-Schritt ist dort deterministisch (Schwellwert über Embedding-Distanz); Modelle extrahieren nur Entitäten.
2. **Erklärbarkeit als Antwort-Bestandteil:** jede Antwort liefert Schritte mit („Resolved terms: … · Joined: … · Validated: …“). LLM-Wikitila hat heute nur `why` (pro Treffer, auf 4 Labels gekappt) und Warnungen — kein Query-Ebenen-Protokoll.
3. **Zwei Suchachsen:** `retrieve` sucht *nach Bedeutung* (Embeddings) **und** *nach Name* (Substring). ADR-001 schließt Embeddings aus; das deterministische Gegenstück ist: exakte Namen/Stichwörter (BM25) **plus** kuratierte Begriffskarte — genau die Rolle des Authority-Registers.
4. **Zertifizierungs-Marken in Treffern:** zertifizierte Elemente erscheinen in Suchergebnissen als *reviewed*. LLM-Wikitila hat das bereits (`canonical`/`stale`/`unverified`) — die Marken werden um Register-Metadaten ergänzt.

**Bewusst NICHT übernommen (ADR-001):** Reasoning-Modelle im Laufzeitpfad (ReAct-Schleife), Embedding-/Rerank-Modelle, Postgres/pgvector-Servicestack, MCP-Server. Auto Ontology ist ein Mehrmodell-Cloud-Stack; LLM-Wikitila liefert dieselben Suchsicht-Garantien deterministisch: *Entitäten-Extraktion → `tokens()`, Embedding-Distanz → Ko-Vorkommen im selben Chunk, Agent-Schritte → deterministischer Trace.* Auto Ontology sagt selbst: „With one well-modeled source and a fixed set of questions, direct SQL may be enough“ — LLM-Wikitila ist dieser Fall, der Wert liegt in der Coverage-Note und im Trace, nicht im Servicestack.

### Randbedingungen (ADR-001, nicht ohne neues ADR ändern)

Kein Vector-Store-Dienst, kein Modell im Laufzeitpfad, nur Standardbibliothek, deterministisch, `score` bleibt ein RRF-Rangwert, vier Antwortstatus. Die Nahe-am-Thema-Abstention bleibt Aufgabe des Agenten — der Stack liefert die Diskriminanz. Wo das Antwort-Tor selbst verschärft wird, nur über ein neues ADR mit Messung.

### Gemeinsame Wurzel

Die Suche (`wikitila.py:487-671`) ist rein lexikalisch: BM25 über Chunk-Bodies, Datei-Ranking über RRF, Chunk-Auswahl über die BM25-Reihenfolge, Abstention nur bei „gar kein Treffer“. Daraus folgen alle Lücken:

1. **MRR** — `file_scores` (`:420-428`) bewertet eine Datei nur über ihren *besten* Chunk-Rang; Token-Abdeckung und Chunk-Aggregation fehlen. Tokenisierung (`:409-410`) und Stemming (`:415-416`) sind grob.
2. **Passagen-Präsenz** — (a) Datei nicht auf Rang 1 (~30 %), (b) Antwort-Chunk nicht unter den Top-3: `best_chunks` (`:514-523`) folgt nur BM25; antworttragende Daten („549“, „1200 × 675“, Status „proposed“) sind oft **keine Query-Token**. Verifiziert: Frontmatter-`status`/`superseded_by` werden in `files` gespeichert, aber **nicht** in FTS5 indexiert (`cmd_build:325-330`).
3. **Semantische Abstention** — das Antwort-Tor (`:657-664`) setzt `nicht_belegt` nur bei leerem `ranked`. Nahe-am-Thema-Negative („Safe Zones für Pinterest“) treffen die Thema-Begriffe verstreut im Korpus; `unmatched_terms`/`top1_missing_terms` feuern nicht. Es fehlt die Coverage-Note (Ko-Vorkommen), nicht nur ein weiteres Einzelsignal.

## Ziel-Suchsicht (Ausgabevertrag, Woran sich alles misst)

```jsonc
// wikitila.py search "Frage" --json  (neue Felder fett)
{
  "results": [{
    "path", "score", "title", "heading", "snippet", "passages", "why",
    "superseded_by", "canonical", "stale", "unverified",
    "authority": "canonical",            // NEU: Register-Metadaten je Treffer (Analog "reviewed")
    "verified_at": "2026-11-14"
  }],
  "answer_status": "belegt | widersprüchlich | belegt_gueltigkeit_unbestaetigt | nicht_belegt",
  "unmatched_terms": [], "top1_missing_terms": [],
  "term_coverage": 0.33,                 // NEU: Coverage-Note (check_answerable-Analogon)
  "uncovered": ["pinterest"],            // NEU: "kein Chunk deckt X zusammen mit …"
  "trace": {                             // NEU: deterministisches Auflösungs-Protokoll
    "query_tokens": ["safe","zones","pinterest"],
    "resolved": {"safe+zones": ["06_Marketing/anzeigen_instruktionen/02_instagram.md"]},
    "authority": ["preise → 01_Strategie/Preise_neu.md"],
    "graph": [], "gate": ["belegt: Top-1 unverifiziert"] },
  "bm25_top": -12.4, "warnings": [], "ms": 6
}
// NEU: pre-flight, billig, ohne Ranking:
// wikitila.py coverage "Frage"  →  {term_coverage, uncovered, candidates}
```

## Schritte

### P0 — Synthetischer Qualitäts-Korpus (Enabler, ohne Vault)

- [ ] 1. Test-Korpus in `test_wikitila.py` (bzw. `examples/quality-corpus/` + Katalog), der alle Lückentypen reproduziert: Nahe-am-Thema-Negative (Begriffe verstreut, nie ko-lokal), Authority-Werte als Daten („549/899/1.199“) in einem BM25-schwachen Chunk, Zahlen/Interpunktion („1200 × 675“, „1.199“, „instance.yaml“), Frontmatter-`status: proposed`.
- [ ] 2. `validate_catalog.py` darauf laufen lassen; Ist-Werte als Baseline festhalten (macht die Verbesserung im Repo messbar, ohne den echten Vault).

### P1 — Deterministische Query-Erzeugung (hebt MRR und Passage)

Das Gegenstück zu Auto Ontologys „deterministic query generation“: LLM-Wikitila erzeugt keine SQL, sondern eine FTS-Query. Die muss präzise werden.

- [ ] 3. `tokens()` (`wikitila.py:409-410`) und `fts_query()` (`:413-417`): Zahlen mit Trennern als Einheiten erhalten („1.199“, „10.794“), `×`/Punkt nicht still verwerfen, Identifier mit Punkt/Slash („X.com“, „instance.yaml“) nicht in wertlose Einzelzeichen zerlegen.
- [ ] 4. Stemming konservativer statt pauschal `t[:-2]*` ab 7 Zeichen (Über-Treffer „produkt*“ → „produktion“ vermeiden).
- [ ] 5. Tests: „1.199“, „1200 × 675“, „instance.yaml“, ein Über-Treffer-Fall.

### P2 — Datei-Ranking: Token-Abdeckung + Chunk-Aggregation (MRR)

- [ ] 6. `file_scores`/`search`: Datei-Score aus den Top-2–3 Chunks **und** der Anzahl abgedeckter, distinkter Query-Token (modellfrei, deterministisch) statt nur aus dem besten Chunk-Rang.
- [ ] 7. `filename_boost`/`graph_weight` mit dem Qualitäts-Korpus nachmessen; nur bei belegtem Gewinn anpassen, Defaults sonst unangetastet.
- [ ] 8. Tests: richtige Datei mit mehreren schwachen Chunks statt eines starken erreicht Rang 1.

### P3 — Chunk-Auswahl & Snippet (Passagen-Präsenz)

- [ ] 9. Frontmatter-`status` und `superseded_by` in einen durchsuchbaren Teil des Index aufnehmen (Titel-Feld, `cmd_build:325-330`) — behebt den verifizierten Befund („proposed“ auffindbar).
- [ ] 10. `best_chunks` für **alle** Authority-Einträge mit `value` auf die Chunks lenken, die die Register-Werte enthalten (bisher nur Supersede-Pfad, `search:559-568`); Rückfall auf BM25-Chunks.
- [ ] 11. Chunk-Auswahl zusätzlich um **Query-Token-Abdeckung im selben Chunk** gewichten; Snippet bevorzugt aus dem Chunk mit höchster Abdeckung (nicht starr `passages[0]`).
- [ ] 12. Tests: Authority-Wert in Chunk 3 kommt unter die Top-3-Passagen; „proposed“-Status auffindbar.

### P4 — Coverage-Note (deterministisches `check_answerable`-Analogon)

- [ ] 13. Neue Funktion `coverage_grade(c, cfg, q)`: signifikante Query-Token → je Token die Treffer-Chunks → **Ko-Vorkommens-Prüfung** (welche Token teilen sich mindestens einen Chunk). Rückgabe: `term_coverage` ∈ [0,1] (Anteil ko-lokal gedeckter Token), `uncovered` (Token ohne ko-lokalen Beleg, mit Hinweis, wo sie einzeln vorkommen), `candidates` (Chunks je gedecktem Token). Kein Modell, nur FTS5-Komponenten, billig genug als Pre-Flight.
- [ ] 14. `search` liefert `term_coverage`/`uncovered` in der Ausgabe mit; neuer Befehl `wikitila.py coverage "Frage"` als reiner Pre-Flight (Analog `check_answerable`: Agent fragt bei niedriger Coverage nach, schlägt den nächstgelegenen abgedeckten Sachverhalt vor — das ist der Top-1-Treffer).
- [ ] 15. `validate_catalog.py`: für `kind=negativ` zusätzlich die Coverage-Note messen (Ziel: alle Negativ-Fälle `term_coverage < 1,0`), damit der Fortschritt sichtbar wird, ohne den Antwortvertrag zu brechen.
- [ ] 16. **Entscheidungspunkt (neues ADR):** Ob das Antwort-Tor eine Coverage-Regel bekommt (kein Chunk trägt die signifikanten Token gemeinsam **und** Top-1-Abdeckung niedrig → `nicht_belegt`), ist eine Änderung an ADR-001 (Punkt 2/5). Nur über ADR-005 mit Messung am synthetischen Korpus **und** Owner-Messung am Vault; bis dahin Signal-only.
- [ ] 17. Tests: 7 synthetische Nahe-am-Thema-Negative bekommen `term_coverage < 1,0` und ein gefülltes `uncovered`; echte Treffer bekommen 1,0.

### P5 — Suchsicht: Trace, Register-Metadaten, Mini-Ontologie

Das Gegenstück zu „Resolved terms / Joined / Validated“ und zur Zertifizierungs-Marke:

- [ ] 18. Query-Ebenen-`trace` in `search`-Ausgabe: welche Token → welche Chunks/Dateien aufgelöst wurden, welche Authority-Einträge gezogen haben, welche Graph-Kanten beigetragen haben, welche Regel den `answer_status` gesetzt hat. Deterministisch aus den vorhandenen Zwischenschritten (`why`, `best_chunks`, Register-Maps); `why` pro Treffer bleibt.
- [ ] 19. Treffer-Metadaten aus dem Register ergänzen: `authority`, `verified_at` je Hit (Analog „reviewed“-Marke). Maskierung (`mk`) auch für neue Felder, Memory „Maskierung an der Ausgabe“ beachten.
- [ ] 20. Register als Mini-Ontologie dokumentieren und in der Suchsicht nutzen: Auto-Ontologys sechs Fragen ↔ Register/Index (`alias`+`note` = Bedeutung, `canonical` = Ort, Link-Graph = Verbindung, `value` = Wert/Beleg, `supersedes` = Herkunft, `authority_confirmed` = Zertifizierung). Optional `synonyms` je Register-Eintrag für Namens-Auflösung („Zweite Suchachse“ ohne Embeddings) — nur als abwärtskompatible Register-Erweiterung.
- [ ] 21. Tests: Trace enthält bei einer Supersede-Frage den Register-Eintrag; `authority`/`verified_at` erscheinen nur, wenn ein Register-Eintrag existiert; `synonyms` löst einen Alias-Namen auf.

### P6 — Doku, PM, Abschluss

- [ ] 22. `docs/agentic-setup.*.md` und `docs/operations.*.md`: Coverage-First-Ablauf (erst `coverage`, bei Lücke nachfragen/Alternativen anbieten, dann `search`), neue Felder im Antwortvertrag.
- [ ] 23. `docs/validation.*.md`, `docs/architecture.*.md`, `docs/benefits.*.md`: Referenzwerte, Coverage-Note, Trace, Auto-Ontology-Vergleich als Absatz (DE/EN synchron).
- [ ] 24. `pm/BACKLOG.md` (B-010 abschließen/aufteilen; B-015/B-016/B-017), `pm/STATUS.md`, `ROADMAP.md` (0.3.0 um Suchsicht ergänzen), `CHANGELOG.md` (`[Unreleased]`), Sitzungsnotiz `pm/sessions/2026-11-25-…md`, Memory-Eintrag (Coverage-Note ersetzt keine Semantik, ADR-001 bleibt).
- [ ] 25. Gates: `python3 -m unittest test_wikitila`, Demo-Korpus-Build + `validate_catalog.py` grün.

## Tests

- Erweiterung von `test_wikitila.py` um P0–P5-Fälle (synthetisch, kein Netz, kein Vault): Tokenisierung, Chunk-Aggregation, Authority-Wert-Chunks, Frontmatter-Status, Coverage-Note, Trace, Register-Metadaten.
- `validate_catalog.py`: Coverage-Zeile für `kind=negativ`.
- Bestehende 32 Tests und Demo-Katalog bleiben grün (keine Regression der F1–F13-Fixes).

## Risiken / Rückweg

- **Über-Anpassung an den einen Vault:** jede Ranking-/Signaländerung wird am synthetischen Qualitäts-Korpus belegt, nie am echten Vault; Referenzzahlen liefert nur der Owner. Ranking-Defaults nur bei belegtem Gewinn ändern.
- **Servicestack-Creep:** Auto Ontology inspiriert nur das Suchsicht-Konzept; Postgres/pgvector/Embeddings/MCP sind explizit ausgeschlossen (ADR-001, stdlib-only). Der Vergleich ist in der Doku als Konzeptverweis geführt, kein Code wird importiert.
- **Antwort-Tor bricht den Vier-Status-Vertrag:** die Coverage-Regel (Schritt 16) ist ADR-entscheidungspflichtig; Standard ist die rein additive Coverage-Note (Schritt 13/14), jederzeit rückstandsfrei entfernbar.
- **Stemming-Verschlechterung:** mit P0-Baseline vorher/nachher messen; bei Verschlechterung nur den Tokenizer-Teil übernehmen.
- **Trace-Overhead:** Trace wird aus ohnehin vorhandenen Zwischenergebnissen gebaut (keine Zusatz-IO); bei Bedarf hinter `--json`/Config-Schalter legen.
- **Rückweg:** jeder Schritt ist ein eigener Commit auf `feat/qualitaet-suchsicht`; die Suche bleibt über die `variants`-Schalter in `cmd_eval` isoliert vergleichbar.

## Ergebnis (nach Abschluss)

**Umgesetzt (2026-11-25):** P1 (mehrstellige Zahlen), P2 (Chunk-Aggregation), P3 (Frontmatter-Status, Authority-Wert-Chunks), P4 (Coverage-Note + `coverage`-Befehl + `validate_catalog.py`-Zeile), P5 (Trace, Register-Metadaten). Gates: 37 Unit-Tests grün, Demo-Katalog MRR 1,000, Coverage-Note 2/2 auf Beispiel-Negativen.

**Offen / Folgearbeiten:**
- Owner-Messung am Vault (MRR ≥ 0,80, Passagen-Präsenz, Coverage-Note auf den 8 Negativ-Fällen) — B-010/B-015/B-016.
- ADR-005: Antwort-Tor-Verschärfung um die Coverage-Regel (Entscheidung offen).
- B-018 (kurze Abschnitte < `min_chunk_chars`), B-011 (inkrementeller Link-Graph), B-013 (Release-Signierung).
- P2-Erweiterung „Token-Abdeckungs-Bonus“ im Ranking ist bewusst zurückgestellt (Risiko/Nutzen); mit Owner-Messung erneut prüfen.
