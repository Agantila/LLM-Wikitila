# Sitzung 2026-11-15: Erster Produktiveinsatz

**Agent:** Claude Code (Opus 5.5) · **Branch:** `pm/workspace-deployment`

## Getan
1. Im Referenz-Vault des Owners eine ältere Installation gefunden: eine eigene Kopie des Werkzeugs (inhaltlich v0.1.0) mit Konfiguration und Index unter `.sbs/` (gitignored).
2. Problem: Das Entwicklungs-Repo lag innerhalb des indexierten Ordners und war nicht ausgeschlossen. 18 Werkzeug-Dokumente waren im Vault-Index, darunter Doku mit den Negativ-Stichwörtern des Katalogs.
3. Neue Aufteilung: Entwicklung in diesem Repo, Laufzeit in einem git worktree auf dem Release-Tag `v0.2.0`, Instanzdaten im Vault (`wikitila.toml`, Register, privater Katalog, `.wikitila/`), Aufruf über ein kleines Wrapper-Skript.
4. Owner-freigegebene Abnahmemessung: R@10 1,00, MRR 0,776 (vorher 0,799). Das alte Werkzeug liefert auf dem neuen Index identisch 0,776, die Differenz ist also eine Korpusänderung, kein Code-Effekt.
5. Alte Kopie archiviert und die Vault-eigene Doku auf den Release-Worktree umgestellt.

## Offen
- Alte Kopie und `.sbs/` nach der nächsten erfolgreichen Messung entfernen (macht der Owner).
- B-001 Veröffentlichung.
