---
name: maskierung-an-der-ausgabe
description: Secrets werden beim Ausgeben maskiert, nicht im Index; jedes neue Textfeld muss durch mk()
type: decision
---
Der Index speichert Volltext unmaskiert (Dateien bleiben über Begriffe auffindbar). Maskiert wird in `search()` über `mk = mask if mask_secrets`. Das gilt für `heading`, `body`, `title`, die Entitäts-Labels in `why` (beim Erzeugen) und die Decision-Kandidaten. Dateinamen in `why` werden bewusst nicht maskiert, weil die 40-Zeichen-Regel lange Dateinamen sonst unlesbar macht.
**Warum:** Im Review 2026-11-15 (F2) lief `heading` an der Maskierung vorbei. Bei Abschnitten ohne Überschrift ist das die erste Textzeile, und die kann ein Secret enthalten.
**Anwenden:** Neue Ausgabefelder immer durch `mk()` schicken und in `test_f2_secret_in_first_line_masked_everywhere` abdecken (der Test prüft das gesamte JSON).
