# Installation (Deutsch)

## Voraussetzungen

| Komponente | Anforderung | Benötigt für |
|---|---|---|
| Python | ≥ 3.11 (Standardbibliothek) | Suche — immer |
| SQLite FTS5 | in Python ≥ 3.11 enthalten | Suche — immer |
| Ollama | installiert und laufend | Wissensgraph (optional) |
| `maternion/ling-3.0-tiny:8b` | `ollama pull maternion/ling-3.0-tiny:8b` | Wissensgraph (optional) |
| Graphify + networkx | `pip install graphifyy==0.4.16 networkx==3.6.1` (PyPI-Name **graphifyy**, Import `graphify`) | Wissensgraph (optional) |
| `embeddinggemma:latest` + `numpy` | nur bei Embedding | Embedding (optional, Vorgabe: aus) |

## Schritt für Schritt

**Schritt 1 — Repo bereitstellen.** Dieses Verzeichnis klonen/kopieren. Der Ziel-Ordner (Projekt-/Second-Brain-Ordner) bleibt unverändert — LLM-Wikitila legt nur `.wikitila/` (Index) und `wikitila.toml` darin an.

**Schritt 2 — Einrichten (ein Befehl):**

```bash
./install.sh /pfad/zum/projekt-ordner
```

Der Installer ist idempotent: er prüft Python ≥ 3.11 mit sqlite3/FTS5, legt `wikitila.toml` und ein **leeres** `authority_register.json` an (falls nicht vorhanden; Aufbau der Einträge in `authority_register.example.json`), baut den Index und führt den Index-/Quellstand-Abgleich aus. Ist `python3` zu alt oder ohne sqlite3, den Interpreter setzen: `PYTHON=/usr/bin/python3 ./install.sh …` (gilt ebenso für den Wrapper `./wikitila`).

**Schritt 3 — Ausschlüsse festlegen.** Im Ziel-Ordner `.graphifyignore` anlegen (gitignore-ähnliche Muster, z. B. `Archiv/`, `*Template_*.md`). Dieselbe Datei gilt für Suche und Graph.

**Schritt 4 — Suche testen:**

```bash
python3 wikitila.py --root /pfad/zum/projekt-ordner search "Ihre Frage" -k 5
```

**Schritt 5 — Authority-Register befüllen.** `authority_register.json` im Ziel-Ordner mit den maßgeblichen Quellen je wiederkehrendem Thema befüllen (Anleitung: `docs/authority-register.de.md`). Erst danach greifen `kanonisch`/`überholt durch`/`veraltet`.

**Schritt 6 — Optional: Wissensgraph bauen.** Erst nach Schritt 1–5; die Suche trägt auch ohne Graph.

```bash
python3 wikitila_graph.py run --model maternion/ling-3.0-tiny:8b --workers 2
python3 wikitila_graph.py build
python3 wikitila.py --root /pfad/zum/projekt-ordner build
```

Hinweis: Der erste Graph-Lauf dauert (rund 0,3 Dokumente je Sekunde, z. B. 1.250 Dokumente ≈ 68 Minuten) und ist fortsetzbar (Cache je Datei). Der Graph ist **Navigation**, nicht Belegquelle.

## Verifikation

```bash
python3 wikitila.py --root . status      # Index-Stand
python3 wikitila.py --root . manifest    # Coverage-Report (Scope, Ausschlüsse)
python3 wikitila.py --root . check       # Index-/Quellstand-Abgleich (kein Drift?)
python3 wikitila.py --root . coverage "Frage"   # Antwortabdeckung vorab (Coverage-Note)
python3 -m unittest test_wikitila        # Selbsttests (79)
```

## Fehlerbehebung

| Symptom | Ursache | Lösung |
|---|---|---|
| `no such module: fts5` | Python ohne FTS5 | Python ≥ 3.11 verwenden |
| `build` findet 0 Dateien | `--root` falsch oder `.graphifyignore` schließt alles aus | Pfad und Ignore-Datei prüfen |
| Treffer aus gelöschten Dateien | Index veraltet | `build` ausführen |
| Graph-Lauf bricht ab | Ollama gestoppt oder Modell fehlt | `ollama list`, Lauf neu starten (setzt fort) |
| Entitäts-Zuordnungen 0 | `graph.json` nicht neu gebaut | erst `wikitila_graph.py build`, dann `wikitila.py build` |
| `FEHLER: Kein Index …` / `Index ist leer` (Exit-Code 2) | `build` noch nicht gelaufen oder Scope leer | `build` ausführen, `include_ext`/Ignore-Muster prüfen |
| `FEHLER: Konfiguration fehlerhaft` | `wikitila.toml` ist kein gültiges TOML | Zeile/Spalte aus der Meldung korrigieren |
| `Hinweis: Authority-Register …` | Register unlesbar oder Eintrag ungültig | JSON und Feldtypen prüfen (siehe docs/authority-register.de.md) |
