# ADR-003: Index-Ort `.wikitila/` und Lesebefehle verlangen einen Index

**Status:** angenommen · **Datum:** 2026-11-15 · **Bezug:** F1, F6, B-100, B-104

## Kontext
Die Vorlage `config.example.toml` nannte `.sbs/index.db` (Altlast aus `second_brain_stack`), Code und Doku dagegen `.wikitila/`. `install.sh` kopiert die Vorlage, deshalb landete der Volltext-Index außerhalb des dokumentierten `.gitignore`-Schutzes. Außerdem legte jeder Lesebefehl über `connect()` einen leeren Index an, und `search` antwortete darauf mit `nicht_belegt`, ohne dass ein Index existierte.

## Entscheidung
1. Einziger dokumentierter Index-Ort ist `.wikitila/` (Vorgabe, Vorlage und Doku). Ein Test hält Vorlage und Vorgabe gleich.
2. `install.sh` trägt `.wikitila/` in die `.gitignore` des Ziel-Ordners ein, wenn dieser ein Git-Repo ist (idempotent).
3. Nur `build` (und `manifest` für seine Ausgabedatei) legen Verzeichnisse an. `search`, `eval` und `embed` brechen bei fehlendem oder leerem Index mit `WikitilaError` (Exit-Code 2) ab. `status` bricht bei fehlendem Index ab, `check` meldet ihn als Drift.

## Alternativen
- Fünfter Antwortstatus „kein_index“: würde den Vier-Status-Vertrag (ADR-001) ändern. Ein Bedienfehler ist kein Antwortstatus.
- Automatisch bauen beim ersten `search`: versteckte Laufzeit und Seiteneffekt in fremden Ordnern.

## Folgen
Skripte müssen Exit-Code 2 behandeln. Bestehende `.sbs/`-Installationen funktionieren weiter (der Pfad ist konfigurierbar), sollten aber geprüft werden (B-002).
