#!/usr/bin/env bash
# LLM-Wikitila — Installer für einen Ziel-Ordner (idempotent, sicher mehrfach ausführbar)
#
#   ./install.sh [ziel-ordner]     ziel-ordner ist der Projekt-/Second-Brain-Ordner, Vorgabe: aktuelles Verzeichnis
#
# Was er tut: Python >= 3.11 prüfen, wikitila.toml und authority_register.json anlegen
# (falls nicht vorhanden), Suchindex bauen und den Index-/Quellstand-Abgleich ausführen.
set -euo pipefail

TARGET="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=python3

if ! "$PY" -c 'import sys; assert sys.version_info >= (3, 11)' 2>/dev/null; then
    echo "FEHLER: Python 3.11 oder neuer wird benötigt (tomllib)." >&2
    exit 1
fi

mkdir -p "$TARGET"
cd "$TARGET"

if [ ! -f wikitila.toml ]; then
    cp "$SCRIPT_DIR/config.example.toml" wikitila.toml
    echo "wikitila.toml angelegt (aus config.example.toml)"
fi
if [ ! -f authority_register.json ]; then
    cp "$SCRIPT_DIR/authority_register.example.json" authority_register.json
    echo "authority_register.json angelegt (aus der Vorlage — bitte mit den eigenen kanonischen Quellen befüllen)"
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
  3. Optional den Wissensgraphen bauen (benötigt Ollama + Graphify, siehe docs/installation.de.md)
  4. Validierung mit einem Fragenkatalog: docs/validation.de.md
EOF
