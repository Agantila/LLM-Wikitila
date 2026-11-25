# Agentische Installation und Betrieb (Deutsch)

Diese Datei ist die Arbeitsanleitung für **KI-Agenten** (Hermes, Claude, Cursor u. ä.), die LLM-Wikitila in einem Projekt einrichten, nutzen oder pflegen. (Englisch: [agentic-setup.en.md](agentic-setup.en.md). Kann bei Bedarf 1:1 als `AGENTS.md` im Repo aktiviert werden.)

## 0. Setup-Prompt — einfach in ein beliebiges Agent-Harness einfügen

Für die optimale Einrichtung reicht **ein** Prompt. Kopiere den Block unverändert in Claude Code, Codex, Cursor, Hermes oder ein anderes Agent-Harness. Der Agent klärt die offenen Fragen mit dir, bevor er etwas überschreibt — die Fragen sind zugleich die Anforderungs-Checkliste für ein optimales LLM-Wiki.

```text
Richte LLM-Wikitila in diesem Ordner optimal ein (lokale, belegte Suche über Markdown).
Wahrheitsquelle: https://github.com/Agantila/LLM-Wikitila (docs/ + skills/llm-wikitila/).
Antwortvertrag: belegt · widersprüchlich · belegt_gueltigkeit_unbestaetigt · nicht_belegt.

Arbeite in dieser Reihenfolge und FRAGE bei jedem offenen Punkt nach, bevor du schreibst:

1. ROOT & SCOPE
   - Welcher Ordner ist der kanonische Vault? (Vorgabe: aktueller Ordner.)
   - Welche Dateitypen? (Vorgabe .md/.txt; alles andere zählt als Ausschluss im Manifest.)
   - Was muss raus? → .graphifyignore anlegen/pflegen (node_modules, Fremdcode, Kopien, *.js, Archive).

2. WERKZEUG
   - git clone https://github.com/Agantila/LLM-Wikitila.git  (oder ./install.sh <ordner>).
   - wikitila.toml nur bei echten Abweichungen von config.example.toml anlegen.

3. AUTHORITY (Herzstück)
   - Welche Dateien sind maßgeblich (Preise, Entscheidungen, Kennzahlen, Definitionen)?
   - Welche Quellen sind überholt, welche lösen was ab?
   - Welche Fakten sind zeitabhängig (stale_after / Review-Termin)?
   → authority_register.json befüllen. NUR der menschliche Owner setzt authority_confirmed: true.

4. INDEX & PRÜFUNG
   - wikitila.py --root <ordner> build
   - wikitila.py --root <ordner> manifest   (Coverage: was ist ausgeschlossen und warum)
   - wikitila.py --root <ordner> check      (Drift 0)
   - .wikitila/ in .gitignore aufnehmen.

5. ABNAHME
   - Fragenkatalog (JSONL, ~50 Fälle: positiv/authority/coverage/negativ) mit dem Owner anlegen.
   - python3 validate_catalog.py --root . --catalog <katalog>
     Ziele: R@10 ≥ 0,95 · MRR ≥ 0,80 · Passagen-Präsenz hoch · Coverage-Note < 1,0 auf Negativ-Fällen.
   - Verfehlte Fälle analysieren (Register, Scope, Überschriften) und nachziehen.

6. GRAPH (optional, nie als Belegquelle)
   - Nur auf ausdrückliche Freigabe; Dauer vorher nennen (≈0,3 Dokumente/s).
   - wikitila_graph.py run --model maternion/ling-3.0-tiny:8b --workers 2, danach build.

MELDE AM ENDE: Index-Stand (Dateien/Abschnitte), Drift, Abnahme-Messwerte, offene Punkte.
Regeln: nie auf einem echten Vault evaluieren/testen; nie Negativ-Teststichwörter in indexierte Doku schreiben.
```

Tipp: `coverage "Frage"` prüft die Antwortabdeckung vorab ohne Ranking — nützlich, wenn ein Agent eine Frage als unbeantwortbar einstuft.

## 1. Installation durch einen Agenten

```bash
# Ziel-Ordner = der Projekt-/Second-Brain-Ordner des Kunden
./install.sh /pfad/zum/projekt-ordner        # idempotent: wikitila.toml, Register-Vorlage, Index, check
python3 wikitila.py --root /pfad/zum/projekt-ordner search "Testfrage" -k 5
```

Danach verpflichtend:

1. `authority_register.json` im Ziel-Ordner befüllen (Schema: `docs/authority-register.de.md`). Ohne Einträge keine `kanonisch`/`überholt durch`-Wirkung.
2. `.graphifyignore` im Ziel-Ordner prüfen/anlegen (Fremdcode, Kopien, `node_modules`, `*.js`).
3. `python3 wikitila.py --root . manifest` + `check` — Coverage und Drift kontrollieren.

## 2. Nutzung

```bash
python3 wikitila.py --root <ordner> search "Frage" -k 5 --json   # Suche (rund 20 ms)
python3 wikitila.py --root <ordner> build                        # Index aktualisieren
python3 wikitila.py --root <ordner> manifest                     # Coverage-Report
python3 wikitila.py --root <ordner> check                        # Index-/Quellstand-Abgleich
python3 wikitila.py --root <ordner> status                       # Index-Stand
```

Antwortfelder: `results` (Datei, `heading`, `passages` = Originalpassagen, `score`, `why`), `answer_status`, `unmatched_terms`, `top1_missing_terms`, `term_coverage`/`uncovered` (Coverage-Note), `trace` (Register-Regeln + Antwort-Tor-Begründung), `bm25_top`. Flags je Treffer: `canonical`, `stale`, `unverified`, `superseded_by`, `authority`, `verified_at`. Vorab ohne Ranking: `wikitila.py --root <ordner> coverage "Frage"`.

## 3. Antwortvertrag (verbindlich für Agenten)

- **Belegte Aussage als Einheit:** jede faktische Kernaussage mit Datei, Überschrift und Originalpassage; Zahlen, Daten, Namen und IDs exakt übernehmen. Beleg, Inferenz und Empfehlung trennen.
- **Vier Antwortstatus:** `belegt` · `widersprüchlich` (beide Werte mit Quellen und Auflösung nennen) · `belegt_gueltigkeit_unbestaetigt` · `nicht_belegt` („Im Repository nicht belastbar belegt“ — niemals „existiert nicht“).
- **Abstention:** `nicht_belegt` bei leerem Ergebnis. Bei `top1_missing_terms` (Begriff fehlt im Top-1-Ergebnis, z. B. „pinterest“) selbst abstimmen: die Passage belegt dann nicht die Frage.
- **Flags:** `überholt durch …` → Nachfolger lesen; `kanonisch` → maßgebliche Quelle; `veraltet`/`Gültigkeit nicht bestätigt` → Gültigkeit offen lassen.
- **`score` ist ein RRF-Rangwert** — niemals als Confidence oder Prozentzahl ausgeben.
- **Kein Zurückschreiben** automatisch erzeugter Antworten als neues Wissen, ohne menschliche Prüfung.

## 4. Authority-Register pflegen

- **Vorschlagen:** neuer Eintrag mit `authority_confirmed: false`, `note` mit Beleg (id, scope, canonical, owner).
- **Nur der menschliche Owner** setzt `authority_confirmed: true`, `verified_at`, `authority`, `supersedes`.
- Ablösung zusätzlich im Frontmatter der Dateien (`supersedes`/`superseded_by`) nachziehen.
- Monatlich `stale_after`-Termine prüfen.

## 5. Validierung

- Fragenkatalog (JSONL, Schema: `docs/validation.de.md`) anlegen und mit `python3 validate_catalog.py --root . --catalog <katalog>` messen (Datei-Recall, Passagen-Präsenz, Coverage/Negativ).
- Referenzwerte: R@10 1,00 · MRR 0,785 · Passagen 45 % · Abstention-Signal 8/8 · 18/18 Tests zum Messzeitpunkt (aktuell 39/39). MRR liegt unter dem Ziel 0,80 (Backlog B-010).
- Datei-Recall ist **kein** Nachweis für Antwortqualität.

## 6. Wissensgraph (optional)

```bash
python3 wikitila_graph.py run --model maternion/ling-3.0-tiny:8b --workers 2   # fortsetzbar
python3 wikitila_graph.py build
python3 wikitila.py --root <ordner> build
```

Der Graph ist **Navigation** (path/explain), nie Belegquelle. Erster Lauf dauert (≈0,3 Dokumente/s); vor dem Start Laufzeit nennen und klarstellen, dass die Suche ohne Graph trägt. `graph.json` wird beim Build überschrieben — vorher sichern.

## 7. Fallstricke

- Kein Vector Store für Korpora bis einige zehntausend Abschnitte (Embedding messbar unnötig).
- Decision-Modelle sind **keine** Ranker/Antwort-Tore (gemessen schlechter) — höchstens Pflege-Lint-Kandidaten.
- Negativ-Teststichwörter („Pinterest“, „Snapchat“ …) nie in indexierte Doku schreiben — danach sind sie im Korpus „vorhanden“ und die lexikalische Abstention erkennt sie nicht mehr.
- Der Index enthält Volltext → `.wikitila/` bleibt in `.gitignore`.
