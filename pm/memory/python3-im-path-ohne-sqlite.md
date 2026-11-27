---
name: python3-im-path-ohne-sqlite
description: Auf dem Owner-Rechner ist `python3` im PATH ein pyenv-3.10 ohne `_sqlite3` — Gates mit `/usr/bin/python3` laufen lassen
type: pitfall
---
`python3` löst auf dem Entwicklungsrechner auf pyenv 3.10.15 auf; dort fehlt `_sqlite3`, `python3 -m unittest test_wikitila` endet mit „Ran 1 test … ImportError“ statt mit einem echten Testergebnis. Zudem verlangt das Projekt ≥ 3.11. **Warum:** Ein solcher Lauf sieht wie ein Testfehler aus, ist aber ein Umgebungsfehler, und umgekehrt kann eine Erfolgsmeldung aus einer anderen Shell stammen. **Anwenden:** Gates mit `/usr/bin/python3` (3.14) ausführen und die Zeile `Ran N tests` prüfen. Der Vault-Wrapper `./wikitila` nutzt deshalb seit 2026-11-27 `/usr/bin/python3` (vorher `python3` — er konnte so nicht laufen; der nächtliche systemd-Build nutzte schon `/usr/bin/python3`). Verwandte Einträge: [[abnahme-misst-bestand-nicht-zufluss]]
