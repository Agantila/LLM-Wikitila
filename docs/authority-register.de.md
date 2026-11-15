# Authority-Register (Deutsch)

Das Register beantwortet **„welche Datei ist für dieses Thema maßgeblich“** und **„ist das noch gültig“**. Datei: `authority_register.json` im Ziel-Ordner. Ohne Register-Eintrag gibt es keine kanonische Wirkung — die Suche liefert dann nur BM25-Relevanz.

## Schema (je Eintrag)

| Feld | Bedeutung | Pflicht |
|---|---|---|
| `id` | stabiler Schlüssel | ja |
| `scope` | Thema/Begriff, den der Eintrag abdeckt (wird als Such-Alias genutzt) | ja |
| `canonical` | maßgebliche Datei (Pfad relativ zum Ziel-Ordner) | ja |
| `authority` | `canonical` · `working` · `reference` | ja |
| `owner` | menschlicher Verantwortlicher | ja |
| `verified_at` | letzte menschliche Bestätigung (ISO-Datum) | ja |
| `stale_after` | Review-Termin bei zeitabhängigen Fakten | bei Zeitabhängigkeit |
| `supersedes` | abgelöste Dateien (Liste) | falls vorhanden |
| `superseded_by` | Nachfolger (Pfad) | falls vorhanden |
| `status` | Frontmatter-`status` der kanonischen Datei | informativ |
| `authority_confirmed` | `true` = Owner bestätigt; `false` = Vorschlag | ja |
| `value` | exakte Teilstrings des kanonischen Werts (für die antworttragende Passage) | empfohlen bei Ablösung |
| `note` | Beleg, Wert, Begründung | empfohlen |

## Beispiel

```json
{
  "id": "preise-produktlinie",
  "scope": "Preise der Produktlinie",
  "canonical": "doku/preise_aktuell.md",
  "authority": "canonical",
  "owner": "Max Mustermann",
  "verified_at": "2026-01-15",
  "stale_after": "2026-12-31",
  "supersedes": ["doku/preise_alt.md"],
  "superseded_by": null,
  "status": "accepted",
  "authority_confirmed": true,
  "value": ["549"],
  "note": "Aktuell 549 EUR; alte Fassung abgelöst."
}
```

**Wirkung:** Fragen mit Treffern in `preise_alt.md` werden auf `preise_aktuell.md` umgelenkt („überholt durch“), der Nachfolger erhält `kanonisch` und die Passage mit `549`. Trifft eine Frage ein Register-Thema (via `scope`), wird die kanonische Datei hochgezogen — das löst Terminologie-Mismatches („Such-Architektur“ ↔ Datei „Such-Schicht“).

## Validierung beim Laden

Das Register wird beim Laden geprüft. Unlesbares JSON, eine fehlende `entries`-Liste, Einträge ohne `canonical`, ein `stale_after` außerhalb von `JJJJ-MM-TT` oder ein `supersedes`, das keine Liste ist, erzeugen einen `Hinweis` in `search` (Feld `warnings`) und `status`. Ungültige Einträge oder Felder werden übersprungen; die Suche läuft weiter. Ein stillschweigend ignoriertes Register gibt es nicht mehr.

## Agentenregeln

1. Vor jeder belastbaren Antwort zu einem Register-Thema den Eintrag lesen und die `canonical`-Datei als Quelle verwenden.
2. Abgelöste Dateien nie als aktuellen Stand ausgeben.
3. `stale_after` überschritten oder `status: proposed` ohne Bestätigung → „belegt, aktuelle Gültigkeit nicht bestätigt“.
4. `authority_confirmed: false` → Vorschlag, keine kanonische Wirkung.
5. Widerspruch gefunden → beide Werte mit Quellen nennen und einen Vorschlag ins Register eintragen.

## Lern- und Update-Verfahren

1. **Erkennen:** wiederkehrende, entscheidungsrelevante Frage mit mehreren Quellen oder ohne kanonische Quelle; oder ein Widerspruch/überholter Stand fällt auf.
2. **Vorschlagen:** Eintrag mit `authority_confirmed: false` anlegen, `note` mit Beleg.
3. **Bestätigen:** **nur der menschliche Owner** setzt `authority_confirmed: true`, füllt `verified_at` und entscheidet über `authority`, `canonical`, `supersedes`.
4. **Auflösen:** Ablösung zusätzlich im Frontmatter der Dateien (`supersedes`/`superseded_by`) nachziehen.
5. **Review:** monatlich alle `stale_after`-Termine prüfen, unbestätigte Einträge dem Owner vorlegen, tote `canonical`-Pfade entfernen.
