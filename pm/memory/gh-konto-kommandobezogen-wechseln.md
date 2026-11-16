---
name: gh-konto-kommandobezogen-wechseln
description: Für Aktionen unter einem anderen GitHub-Konto GH_TOKEN kommandobezogen setzen, nie das global aktive gh-Konto umschalten
type: pitfall
---

Wenn eine Aktion (Repo anlegen, pushen, PR) unter einem anderen GitHub-Konto laufen soll, das nicht dem global aktiven `gh`-Konto entspricht, setzt man das Token kommandobezogen: `export GH_TOKEN=$(gh auth token --user <konto>)`. Das gilt auch für `git push`, weil der Credential-Helper `gh auth git-credential` die Umgebungsvariable `GH_TOKEN` vor dem Konfigurationskonto auswertet. `gh auth switch` bleibt unangetastet, damit das globale Konto des Owners unverändert bleibt.

**Warum:** `gh auth switch` verändert globalen Zustand und wirkt auf alle weiteren Kommandos des Rechners. Der Credential-Helper nutzt ohne `GH_TOKEN` stillschweigend das aktive Konto, sodass ein Push unter der falschen Identität landen kann — bei einer Veröffentlichung ist das ein Herkunftsfehler in der Historie, der nur durch Löschen des Repositories rückgängig zu machen ist.

**Anwenden:** Vor dem Anlegen oder Pushen prüfen, wer authentifiziert ist (`gh api user --jq .login` mit gesetztem `GH_TOKEN`), das Zielkonto vorher explizit benennen und den Ertrag danach gegenprüfen. Verwandte Einträge: [[workspace-einsatz-release-worktree]].
