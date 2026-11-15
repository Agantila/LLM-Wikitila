---
name: workspace-einsatz-release-worktree
description: Produktive Vaults nutzen einen git worktree dieses Repos auf einem Release-Tag; nie dort entwickeln
type: decision
---
Ein produktiver Vault ruft einen git worktree dieses Repos (detached auf dem Release-Tag) über ein kleines Wrapper-Skript auf. Entwickelt wird nur in diesem Repo.
**Warum:** Der Vault soll nur getestete Releases nutzen. Eine eigene Kopie des Werkzeugs im Vault ist früher auseinandergedriftet und hatte 13 offene Befunde.
**Anwenden:** Neues Release = Tag setzen, dann `git -C <release-worktree> checkout <tag>`. Der Owner baut den Index im Vault neu und misst den Katalog. Dieses Repo darf nie innerhalb eines indexierten Ordners liegen, sonst landen seine Docs (mit Negativ-Stichwörtern) im Vault-Index. Verwandt: [[negativ-stichwoerter-nicht-indexieren]], [[nie-auf-echtem-vault-testen]]
