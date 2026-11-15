# Projektmanagement

Leichtgewichtiges, dateibasiertes Projektmanagement für Menschen und KI-Agenten. Alles ist Markdown im Repo: versioniert, reviewbar und ohne externes Werkzeug.

| Datei/Ordner | Zweck | Wer pflegt |
|---|---|---|
| [STATUS.md](STATUS.md) | Aktueller Stand in einer Seite: Version, Gates, offene Punkte, nächster Schritt | jede Sitzung am Ende |
| [BACKLOG.md](BACKLOG.md) | Alle Arbeitspakete mit ID, Priorität, Status und Bezug | bei neuer Erkenntnis bzw. Abschluss |
| [ROADMAP.md](ROADMAP.md) | Meilensteine (Versionen) und welche Backlog-IDs dazugehören | bei Release-Planung |
| [plans/](plans/) | Umsetzungspläne je nicht-trivialer Aufgabe (vorher schreiben, beim Arbeiten abhaken) | Agent oder Mensch, der umsetzt |
| [adr/](adr/) | Architecture Decision Records: warum etwas so ist | bei strukturellen Entscheidungen |
| [memory/](memory/) | Projektgedächtnis: nicht offensichtliche Fakten, Fallstricke, Messergebnisse | wer etwas lernt |
| [sessions/](sessions/) | Sitzungsnotizen zur Übergabe an die nächste Sitzung | jede Sitzung am Ende |

Der Ablauf (Sitzungsprotokoll, Gates, Memory-Format) steht in [../AGENTS.md](../AGENTS.md).

**IDs:** Backlog `B-NNN`, Review-Befunde `F<n>` (aus `review/report-*.md`), ADRs `ADR-NNN`.
