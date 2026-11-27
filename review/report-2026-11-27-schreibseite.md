# Review-Bericht LLM-Wikitila: Schreibseite — 2026-11-27

> **Umsetzungsstand (2026-11-27):** F1, F2, F4 und F6 umgesetzt (Plan `pm/plans/2026-11-27-lint-schreibvertrag.md`): `wikitila.py lint` (B-020) und der Schreib-Vertrag-Schritt in beiden Prompts, DE+EN (B-019). F3-Dokuteil erledigt; die tags/type-Indexierungs-Entscheidung (F3) und F5 (Katalogfälle) bleiben offen (B-021, B-022).

Auslöser: Im Referenz-Vault des Owners fiel auf, dass neu angelegte Markdown-Dateien zunehmend **ohne Frontmatter-Schema** entstehen (kein `type`/`title`/`description`, keine `tags`), obwohl die Suche genau diese Felder nutzt. Dieser Bericht prüft, was das **Produkt** (Setup-Prompt, Upgrade-Prompt, Doku, Werkzeug) dazu beiträgt und wie Einrichtung und Update künftig ein Second Brain mit garantierter Schreibqualität ausliefern. Read-only durchgeführt: keine Code-Änderung, Tests auf dem Bestand grün (39/39). Stand: Commit `1af4e01`.

Beleglage aus dem Referenz-Vault (Messung 2026-11-27, OKF-Geltungsbeginn 2026-08-28): von 749 geprüften Dateien im Geltungsbereich sind **96 konform, 66 mit Hinweisen, 587 mit Verstössen** (219 ganz ohne Frontmatter, 172 ohne `title`, 105 ohne `type`, 44 ohne `description`, 48 mit ungültigem YAML). Die Eintrittsdateien des Vaults (`AGENTS.md`/`CLAUDE.md`) enthielten in der gesamten Git-Historie **keinen** Verweis auf die Frontmatter-Pflicht; die Regel war nur über einen zufällig geladenen Skill erreichbar.

## 1. Executive Summary

- **Kernbefund:** Der Stack definiert und misst die **Lese**seite vollständig (Antwortvertrag, Authority-Register, Katalog-Abnahme), sagt aber auf der **Schreib**seite nichts. Setup-Prompt (§0) und Upgrade-Prompt (§0b) enthalten keinen Schritt, der festlegt, wie neue Dokumente beschaffen sein müssen, damit die Suche sie trägt. Ein Vault kann die Abnahme (§0 Schritt 5) bestehen und trotzdem wöchentlich an Suchqualität verlieren, weil Agenten neue Dateien schemafrei anlegen.
- **Verstärker:** Der Upgrade-Prompt §0b verlangt „AGENTS.md/CLAUDE.md nur mit Freigabe ändern", sagt aber nicht, **was** dort hineingehört. Im Referenz-Vault blieben die Eintrittsdateien ohne Frontmatter-Verweis — die Pflicht war für die meisten Agenten-Sitzungen unsichtbar.
- **Werkzeug-Lücke:** Die indexierten Felder (`title`, `description`, `status`, `superseded_by`) sind produktseitig definiert, aber das Produkt liefert weder Linter noch Vorlage noch Soll-Ist-Report. Der Referenz-Vault musste das vault-seitig nachbauen.
- **Doku-Lücke:** Nirgends steht, welche Frontmatter-Felder der Index liest und dass `parse_doc` nur flache `key: value`-Zeilen versteht. `tags`/`type`/`bezug` werden **nicht** indexiert — Installationen, die auf Tags setzen, investieren in ein Feld ohne Suchwirkung.
- Insgesamt **1 High-, 4 Medium-, 1 Low-Befund**. Alle Fixes sind klein (S bis M), der wirksamste ist reine Doku (Textbaustein in beide Prompts).

## 2. Befundtabelle

| ID | Schwere | Ebene | Ort | Beleg | Risiko | Fix | Aufwand |
|---|---|---|---|---|---|---|---|
| F1 | **High** | Design/Doku | `docs/agentic-setup.de.md` §0 (Zeilen 5-49) und §0b (Zeilen 53-93), analog `.en.md` | Beide Prompts decken Scope, Werkzeug, Authority, Index, Abnahme und Graph ab — kein Schritt adressiert die Schreibseite (Frontmatter-Minimalprofil, Verankerung in den Eintrittsdateien, wiederkehrende Prüfung) | Jede Einrichtung/Migration liefert einen Such-Index ohne Schreib-Vertrag; der Vault driftet schemafrei, und die Abnahme (Katalog) misst das nicht, weil sie den Bestand prüft, nicht den Zufluss. Im Referenz-Vault: 587 Verstösse im Geltungsbereich | Neuen Schritt „Schreib-Vertrag" in beide Prompts aufnehmen (Textbaustein in Abschnitt 3), DE+EN synchron | S |
| F2 | Medium | Feature-Lücke | `wikitila.py` (kein Lint-Befehl), Lieferumfang allgemein | Die suchtragenden Felder sind im Code definiert (`parse_doc` Zeile ~218, `cmd_build` Zeilen ~323-339), aber kein Produkt-Artefakt prüft sie. Referenz-Vault: Linter und Report wurden vault-seitig gebaut (`okf_linter.py`, `okf_vault_report.py`) | Jede Installation erfindet die Schreibqualitäts-Prüfung selbst oder lässt sie weg; die gemessene Drift ist der Normalfall, nicht die Ausnahme | Minimalen Befehl `wikitila.py lint [<datei> \| --all]` (nur Standardbibliothek): Frontmatter vorhanden, YAML valide, `title`/`description` flach und nicht leer, `status` als String. `--all` als Report mit Ausnahmeliste | M |
| F3 | Medium | Doku | `docs/architecture.de.md`/`.en.md`, `docs/agentic-setup.de.md` | `parse_doc` liest nur flache Zeilen (`^([A-Za-z_]+):\s*(.*)$`), keine Listen, keine verschachtelten Mappings; indexiert werden nur `title`, `description`, `status`, `superseded_by`. Das steht in keiner Nutzerdoku. `tags` und `type` haben keine Suchwirkung | Installationen dokumentieren falsch (z. B. Frontmatter mit `tags`/`created`, aber ohne `title`/`description`: im Referenz-Vault eine ganze Dokumentenserie) und wundern sich über schwache Treffer | Doku-Abschnitt „Welche Frontmatter-Felder der Index liest" (architektur + agentic-setup, DE+EN). Separat entscheiden, ob `tags`/`type` in das Titel-Feld aufgenommen werden (ranking-ändernd: Messung am Demo-Korpus und Referenz-Vault, dann ADR) | S (Doku) / M (Messung) |
| F4 | Medium | Doku | `docs/agentic-setup.de.md` §0b Schritt 3 (Zeile 83) | „AGENTS.md/CLAUDE.md nur mit Freigabe ändern" ohne Inhaltsangabe. Im Referenz-Vault hatten die Eintrittsdateien über die gesamte Historie null Verweise auf die Schreib-Konvention; die Pflicht griff nur, wenn zufällig ein bestimmter Skill geladen war | Der zentrale Hebel (Agenten sehen die Pflicht in jeder Sitzung) bleibt ungenutzt, obwohl der Prompt die Stelle sogar nennt | Konkreten Textbaustein für die Eintrittsdateien in die Prompts aufnehmen (Abschnitt 3), mit dem Hinweis „nur mit Owner-Freigabe" | S |
| F5 | Low | Abnahme | `golden_catalog.example.jsonl`, `examples/demo-corpus/` | Kein Katalogfall prüft eine Antwort, die **nur** über `description` oder `status` erreichbar ist (z. B. Frage nach dem Gültigkeitsstatus, Antwort steht im Frontmatter) | Eine Einrichtung kann grün abnehmen, obwohl Frontmatter-getragene Antworten im Ziel-Vault fehlen; der Katalog misst die Schreibseite gar nicht mit | 2-3 Fälle im Demo-Korpus ergänzen, deren Antwort nur über Frontmatter-Felder erreichbar ist (positiv: `description`; authority: `status`/`superseded_by`) | S |
| F6 | Low | Doku | Prompts/Doku allgemein | Häufigster YAML-Bruch im Referenz-Vault (48 Dateien): unquotierter Doppelpunkt in `description` („mapping values are not allowed here"). Obsidian-Properties brechen ebenfalls | Wiederkehrender, vorhersehbarer Defekt in genau dem Feld mit der höchsten Suchwirkung | Regel „`description` immer in Anführungszeichen" in den Schreib-Vertrag-Textbaustein (Teil von F1) | S |

## 3. Quick Wins und Architektur-Empfehlungen

**Quick Wins (je unter 1 h, nur Doku):** F1/F4/F6 über einen gemeinsamen Textbaustein, F3-Dokuteil. Vorschlag für den Baustein, in §0 als neuer Schritt zwischen 3 (Authority) und 4 (Index) und in §0b als neuer Schritt zwischen 3 und 4:

```text
SCHRITT x — SCHREIB-VERTRAG (Suchqualität entsteht beim Schreiben):
- Frontmatter-Minimalprofil für neue Dateien festlegen: Pflicht `title` und
  `description` als flache Zeilen (`description` in Anführungszeichen — ein
  unquotierter Doppelpunkt bricht YAML), empfohlen `type`, `status`, `tags`.
  Wikitila indexiert aus dem Frontmatter nur title/description/status/superseded_by.
- Die Konvention in den Eintrittsdateien des Ordners verankern
  (AGENTS.md/CLAUDE.md, nur mit Owner-Freigabe): Ohne diesen Verweis sehen
  Agenten die Pflicht nicht, und neue Dateien entstehen schemafrei.
- Prüfung einrichten: Frontmatter-Lint je neuer Datei und ein wiederkehrender
  Soll-Ist-Report (Ausnahmen: index.md/log.md/README.md, Templates, Fixtures).
- Abnahme: mindestens ein Katalogfall, dessen Antwort nur über description
  oder status erreichbar ist.
```

**Architektur-Empfehlung (nach Owner-Entscheid, Frage 2):** `wikitila.py lint` als vierter Prüfbaustein neben `check`/`manifest`/`coverage`. Begründung: Die Felddefinition liegt produktseitig (`parse_doc`), ein produktseitiger Linter kann nicht von der Indexlogik abdriften — ein vault-seitiger schon (im Referenz-Vault meldete der eigene Linter 48 valide Dateien fälschlich als „kein valides Frontmatter", weil er strenger parste als der Index). Zweistufigkeit empfehlen: Verstoß = bricht Suche/Auffindbarkeit (fehlendes/ungültiges Frontmatter, fehlende Pflichtfelder), Hinweis = Konvention (status-Werte, Datumsformate).

**Tags-Indexierung (F3, zweiter Teil):** Nur nach Messung. Aufnahme von `tags` (und evtl. `type`) in das Titel-Feld ist ranking-ändernd; Vorgehen wie gehabt: Demo-Korpus-Messung, dann Referenz-Vault-Messung durch den Owner, dann ADR. Keine Still-Schaltung.

Ausdrücklich **nicht** empfohlen: den Antwortvertrag oder das Ranking für diesen Befund umbauen; die Schreibseite ist ein Konventions- und Prüfproblem, kein Ranking-Problem.

## 4. Nicht-Befunde (geprüft, ohne Befund)

- **Quoting:** `parse_doc` strippt Anführungszeichen korrekt (`.strip("\"'")`); quotierte `description` ist indexseitig unproblematisch — die YAML-Falle (F6) entsteht beim Schreiben und in Fremd-Parsern, nicht im Index.
- **Status-Indexierung:** Die mit 0.3.0 eingeführte Aufnahme von `status`/`superseded_by` in den durchsuchbaren Titel funktioniert wie dokumentiert und hat den Wert von Frontmatter erhöht (kein Rückfall).
- **Upgrade-Prompt §0b:** Inventarisieren-vor-Löschen, graph.json-Sicherung und „nie auf echtem Vault evaluieren" sind korrekt verankert; die Lücke ist ausschliesslich die Schreibseite (F1/F4).
- **Tests:** `python3 -m unittest test_wikitila` → 39/39 grün auf dem geprüften Stand.

## 5. Grenzen der Prüfung

- Die Vault-Messung (587 Verstösse) nutzt den mtime-Proxy für den Geltungsbeginn 2026-08-28; Dateien, die vorher erstellt und seither nur bearbeitet wurden, werden mitgezählt. Die Größenordnung ist belastbar, die Einzelzuordnung nicht exakt.
- Die Wirkung des Schreib-Vertrag-Bausteins (F1) ist aus dem Referenz-Vault abgeleitet (Eintrittsdateien ohne Verweis ↔ schemafreie Zuflüsse), nicht kontrolliert gemessen.
- F2 (Lint-Befehl) wurde nicht implementiert; Aufwand M ist eine Schätzung aus der vorhandenen vault-seitigen Referenzimplementierung.

## 6. Offene Fragen an den Owner

1. Soll `wikitila.py lint` produktseitig kommen (Code-Oberfläche, Standardbibliothek-only), oder bleibt der Schreib-Vertrag reine Prompt-/Doku-Ebene mit Referenzimplementierung als Beispiel?
2. Sollen `tags` (und `type`) in den Index (Titel-Feld)? Wenn ja: Messung und ADR einplanen.
3. Soll der Baustein im Produkt neutral bleiben („Frontmatter-Minimalprofil") oder OKF (knowledge-catalog) als empfohlenes Profil referenzieren? Im Referenz-Vault ist OKF per ADR gesetzt; das MIT-Produkt muss das nicht vorschreiben.
4. Soll die Zweistufigkeit Verstoß/Hinweis Produktkonvention werden (betrifft F2 und die Abnahme-Texte)?
