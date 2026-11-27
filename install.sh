#!/usr/bin/env bash
# LLM-Wikitila — Installer für einen Ziel-Ordner (idempotent, sicher mehrfach ausführbar)
#
#   ./install.sh [ziel-ordner]     ziel-ordner ist der Projekt-/Second-Brain-Ordner, Vorgabe: aktuelles Verzeichnis
#   PYTHON=/usr/bin/python3 ./install.sh …   anderer Interpreter (Python >= 3.11 mit sqlite3/FTS5)
#
# Was er tut: Python >= 3.11 prüfen, wikitila.toml und authority_register.json anlegen
# (falls nicht vorhanden), Suchindex bauen und den Index-/Quellstand-Abgleich ausführen.
set -euo pipefail

TARGET="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"

if ! command -v "$PY" >/dev/null 2>&1; then
    echo "FEHLER: Python-Interpreter '$PY' nicht gefunden (PYTHON=… setzen)." >&2
    exit 1
fi
if ! "$PY" -c 'import sys; assert sys.version_info >= (3, 11)' 2>/dev/null; then
    echo "FEHLER: $PY ist älter als Python 3.11 (tomllib). Mit PYTHON=/pfad/zu/python3.11+ erneut aufrufen." >&2
    exit 1
fi
if ! "$PY" -c 'import sqlite3; c = sqlite3.connect(":memory:"); c.execute("create virtual table t using fts5(x)")' 2>/dev/null; then
    echo "FEHLER: $PY hat kein sqlite3 mit FTS5. Mit PYTHON=/pfad/zu/anderem/python3 erneut aufrufen." >&2
    exit 1
fi

mkdir -p "$TARGET"
cd "$TARGET"

if [ ! -f wikitila.toml ]; then
    cp "$SCRIPT_DIR/config.example.toml" wikitila.toml
    echo "wikitila.toml angelegt (aus config.example.toml)"
fi
if [ ! -f authority_register.json ]; then
    # Leeres Register statt der Beispiel-Einträge: die zeigen auf Demo-Pfade, die es hier nicht gibt.
    cat > authority_register.json <<'JSON'
{
  "version": "1.0",
  "convention": "authority_confirmed=false heißt Vorschlag; nur der menschliche Owner setzt true und ändert authority/canonical/supersedes. Aufbau der Einträge: authority_register.example.json im LLM-Wikitila-Repo.",
  "entries": []
}
JSON
    echo "authority_register.json angelegt (leer — Aufbau siehe authority_register.example.json, docs/authority-register.de.md)"
fi

# Der Index enthält Volltext: in Git-Repos .wikitila/ in die .gitignore des Ziel-Ordners aufnehmen (ADR-003)
if [ -d .git ] && ! grep -qxF '.wikitila/' .gitignore 2>/dev/null; then
    printf '\n# LLM-Wikitila-Index (Volltext, nie committen)\n.wikitila/\n' >> .gitignore
    echo ".wikitila/ in .gitignore eingetragen"
fi

echo "== Index bauen =="
"$PY" "$SCRIPT_DIR/wikitila.py" --root . build
echo "== Index-/Quellstand-Abgleich =="
"$PY" "$SCRIPT_DIR/wikitila.py" --root . check
echo "== Status =="
"$PY" "$SCRIPT_DIR/wikitila.py" --root . status

cat <<'EOF'

LLM-Wikitila ist installiert. Nächste Schritte:
  1. authority_register.json befüllen (kanonische Quellen je Thema, siehe docs/authority-register.de.md)
  2. Suche testen:
       python3 <pfad-zu-wikitila.py> --root . search "Ihre Frage" -k 5
  3. Schreibseite prüfen (Frontmatter-Konvention, siehe [lint] in wikitila.toml):
       python3 <pfad-zu-wikitila.py> --root . lint --all
  4. Optional den Wissensgraphen bauen (benötigt Ollama + Graphify, siehe docs/installation.de.md)
  5. Validierung mit einem Fragenkatalog: docs/validation.de.md
EOF
