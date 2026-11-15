# ADR-004: Symlinks nur innerhalb des Ordners

**Status:** angenommen · **Datum:** 2026-11-15 · **Bezug:** F7, F8, B-105

## Kontext
`os.walk` folgt Verzeichnis-Symlinks nicht, liefert aber Datei-Symlinks, und `read_text` folgt ihnen. Eine Datei `link.md → ../anderswo/x.md` brachte so Inhalte von außerhalb von `--root` in Index und Ausgaben. Defekte Symlinks ließen `manifest` abbrechen.

## Entscheidung
Eine Datei wird nur indexiert, wenn sie kein Symlink ist oder ihr aufgelöstes Ziel existiert und unter `root` liegt (`inside_root()`). Das Manifest zählt die übrigen als `symlink_outside_root` und unlesbare Dateien als `unreadable`. Verzeichnis-Symlinks werden weiterhin nicht verfolgt.

## Alternativen
- Alle Symlinks ignorieren: würde legitime interne Verweise (z. B. Alias-Dateien) ausschließen.
- Symlinks folgen und das Ziel melden: widerspricht dem Scope „dieser Ordner“.

## Folgen
Wer bewusst externe Inhalte durchsuchbar machen will, kopiert sie in den Ordner oder setzt `--root` höher.
