# AGENTS.md — Arbeitsanweisung für KI-Agenten

Gilt für jeden Agenten (Claude Code, Codex, Cursor, …), der **an diesem Repository entwickelt**.
Wer LLM-Wikitila in einem fremden Ordner **installieren oder betreiben** soll, liest [docs/agentic-setup.de.md](docs/agentic-setup.de.md) bzw. [docs/agentic-setup.en.md](docs/agentic-setup.en.md) und den Skill [skills/llm-wikitila/SKILL.md](skills/llm-wikitila/SKILL.md).

## 1. Projekt in einem Satz

Lokale, belegbare Suche plus Wissensgraph für Markdown-Ordner: SQLite FTS5/BM25, deterministischer Link-Graph, Authority-Register und ein modellfreier Antwortvertrag mit vier Status. Laufzeit nur Python-Standardbibliothek (≥ 3.11).

## 2. Sitzungsprotokoll (Pflicht)

**Start**
1. [pm/STATUS.md](pm/STATUS.md) lesen: aktueller Stand, offene Punkte, nächster Schritt.
2. [pm/memory/MEMORY.md](pm/memory/MEMORY.md) lesen: Index des Projektgedächtnisses. Relevante Einträge öffnen.
3. Zur Aufgabe passende Einträge in [pm/BACKLOG.md](pm/BACKLOG.md) und [pm/adr/INDEX.md](pm/adr/INDEX.md) suchen.
4. `python3 -m unittest test_wikitila` laufen lassen. Die Basis muss grün sein, bevor du etwas änderst.

**Arbeit**
5. Nicht-triviale Aufgabe (mehr als eine Datei oder Verhaltensänderung): zuerst einen Plan in `pm/plans/JJJJ-MM-TT-<thema>.md` nach [pm/plans/TEMPLATE.md](pm/plans/TEMPLATE.md) schreiben. Der Plan nennt Backlog-IDs, Schritte, Tests und das Abnahmekriterium.
6. Strukturelle Entscheidung (Datenmodell, Ausgabevertrag, Abhängigkeit, Sicherheitsverhalten): ADR in `pm/adr/` nach [pm/adr/TEMPLATE.md](pm/adr/TEMPLATE.md) anlegen und in `INDEX.md` eintragen. Für triviale Refactorings kein ADR.
7. Jede Verhaltensänderung bekommt einen Test in `test_wikitila.py` (synthetischer Korpus, kein Netz).

**Ende**
8. Gates grün (Abschnitt 4). `CHANGELOG.md` unter `[Unreleased]` ergänzen.
9. `pm/BACKLOG.md` (Status) und `pm/STATUS.md` (Stand, nächster Schritt) aktualisieren.
10. Sitzungsnotiz `pm/sessions/JJJJ-MM-TT-<thema>.md`: was getan, was offen, was die nächste Sitzung wissen muss.
11. Neue, nicht offensichtliche Erkenntnisse als Memory-Eintrag festhalten (Abschnitt 5).

## 3. Verbindliche Designentscheidungen (nicht ohne ADR ändern)

Begründung: [ADR-001](pm/adr/ADR-001-verbindliche-designentscheidungen.md) und [docs/architecture.de.md](docs/architecture.de.md).

- Kein Vector-Store-Dienst. Embedding ist optional und aus.
- Kein Modell im Laufzeitpfad (Decision-Modelle wurden gemessen schlechter).
- Scope = `.md`/`.txt`. Alles andere wird im Source-Manifest als Ausschluss geführt.
- Authority-Register: Nur der Mensch setzt `authority_confirmed: true`.
- `score` ist ein RRF-Rangwert, keine Konfidenz. Vier Antwortstatus; „nicht_belegt“ heißt nicht „existiert nicht“.
- `mask_secrets` ist standardmäßig an und gilt für **alle** Textfelder der Ausgabe. Der Index enthält Volltext und bleibt lokal (`.wikitila/`).
- Laufzeitcode nur mit der Standardbibliothek. Optionale Pakete nur in `wikitila_graph.py` oder hinter Schaltern.

## 4. Gates (vor jedem Commit)

```bash
python3 -m unittest test_wikitila                     # alle grün
python3 wikitila.py --root examples/demo-corpus build
python3 validate_catalog.py --root examples/demo-corpus --catalog golden_catalog.example.jsonl   # R@10 1.00
```

Die CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) führt dasselbe auf Python 3.11 bis 3.13 aus.

**Nie auf einem echten Vault evaluieren oder testen.** Das verzerrt die Katalogwerte und kann private Inhalte in Ausgaben bringen. Härtungstests nur in temporären Ordnern.

## 5. Projektgedächtnis (Memory)

Ort: [pm/memory/](pm/memory/). Pro Datei steht genau ein Fakt, mit Frontmatter:

```markdown
---
name: <kebab-case-slug>
description: <eine Zeile, entscheidet über Relevanz beim Lesen>
type: decision | learning | pitfall | reference
---
<Fakt>. **Warum:** … **Anwenden:** …  Verwandte Einträge: [[anderer-slug]]
```

- Nach dem Anlegen eine Zeile in `MEMORY.md` ergänzen: `- [Titel](datei.md) — Kurzbeschreibung`.
- In Memory gehört, was **nicht** aus Code, Git-Log oder Doku ablesbar ist: Messergebnisse, Fallstricke, verworfene Wege.
- Vor dem Anlegen prüfen, ob es schon einen Eintrag gibt. Dann den bestehenden aktualisieren. Falsche Einträge löschen.
- Keine Secrets, keine Vault-Inhalte, keine personenbezogenen Daten.

## 6. Konventionen

- Sprache: Code-Kommentare, Ausgaben und PM-Dokumente auf Deutsch. Nutzerdoku auf Deutsch **und** Englisch (`*.de.md`/`*.en.md`), beide synchron halten.
- Status-Symbole in PM-Dateien: ✅ erledigt · 🟡 in Arbeit · ⏳ offen · ⚠️ Risiko.
- Commits: `typ(bereich): kurz` (z. B. `fix(search): …`, `docs: …`, `pm: …`). Arbeit auf einem Branch, Merge per Pull Request.
- Versionen nach SemVer. Die Version steht in `wikitila.py` (`__version__`) und in `CHANGELOG.md`.
- Fehler für Nutzer: `WikitilaError` mit verständlicher Meldung (Exit-Code 2), kein Traceback.

## 7. Wichtige Dateien

| Datei | Zweck |
|---|---|
| `wikitila.py` | build · search · status · manifest · check · eval · embed |
| `wikitila_graph.py` | optionale lokale Graphify-Extraktion (Ollama) |
| `validate_catalog.py` | Messung auf drei Ebenen (Recall, Passage, Negativ/Coverage) |
| `test_wikitila.py` | Unit-Tests auf synthetischem Korpus |
| `examples/demo-corpus/` | Mini-Ordner zum Beispielkatalog (CI) |
| `review/` | Review-Metaprompt und Berichte |
| `pm/` | Status, Backlog, Roadmap, Pläne, ADRs, Memory, Sitzungen |
