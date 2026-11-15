# Sicherheit

## Melden

Sicherheitslücken bitte **nicht** als öffentliches Issue melden, sondern über [GitHub Security Advisories](../../security/advisories/new) („Report a vulnerability“) dieses Repositorys. Wir antworten in der Regel innerhalb von 7 Tagen.

## Sicherheitsmodell

- LLM-Wikitila läuft lokal. Netzwerkzugriffe gibt es nur bei eingeschaltetem Embedding oder Decision-Modell (aus in der Vorgabe) und beim optionalen Graph-Build (Ollama).
- **Der Index `.wikitila/index.db` enthält Volltext, unmaskiert.** Er darf nie committet oder weitergegeben werden. `install.sh` trägt `.wikitila/` in Git-Ziel-Ordnern in die `.gitignore` ein.
- `mask_secrets` (Vorgabe an) maskiert Schlüssel und Passwörter in allen Textfeldern der Suchausgabe. Das ist eine Heuristik (Muster), keine Garantie, deshalb Secrets nicht in Markdown ablegen.
- Indexiert werden nur Dateien innerhalb von `--root`. Symlinks nach außen werden übersprungen (ADR-004).
- Konfiguration (`wikitila.toml`, `authority_register.json`) gilt als vertrauenswürdige Eingabe des Owners. Fehlerhafte Dateien werden gemeldet, aber nicht als Angriffsfläche behandelt.

## Unterstützte Versionen

Sicherheitskorrekturen gibt es für die jeweils neueste Minor-Version.
