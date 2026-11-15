# ADR-001: Verbindliche Designentscheidungen (Baseline)

**Status:** angenommen · **Datum:** 2026-11-14 (nachträglich dokumentiert am 2026-11-15) · **Bezug:** docs/architecture.de.md, Review-Metaprompt Abschnitt 3

## Kontext
Die Entscheidungen wurden vor der Erstveröffentlichung gemessen und in `docs/architecture.*.md` begründet. Dieses ADR fasst sie als Baseline zusammen, damit Agenten sie nicht als „Optimierungspotenzial“ behandeln.

## Entscheidung
1. Kein Vector-Store-Dienst. Embedding ist optional und aus (26.000 Vektoren = 80 MB, Brute-Force 25 ms, für R@10 1,00 nicht nötig).
2. Kein Modell im Laufzeitpfad. Decision-Modelle als Ranker oder Antwort-Tor wurden gemessen schlechter. Modelle nur für den Graph-Build und einen optionalen Pflege-Lint.
3. Scope = `.md`/`.txt`. Andere Dateitypen führt das Source-Manifest als Ausschluss.
4. Authority-Register wird vom Owner kuratiert. Nur ein Mensch setzt `authority_confirmed: true`.
5. `score` ist ein RRF-Rangwert, keine Konfidenz. Vier Antwortstatus. „nicht_belegt“ heißt nicht „existiert nicht“.
6. `mask_secrets` ist standardmäßig an. Der Index enthält Volltext und bleibt lokal.
7. Laufzeit nur mit der Standardbibliothek.

## Alternativen
Siehe `docs/architecture.de.md` und `docs/benefits.de.md` (Graph-RAG: R@10 0,25, Embedding-Varianten, Decision-Modelle).

## Folgen
Änderungen an diesen Punkten nur über ein neues ADR mit Messung am Golden Set, im Review nur als „Designänderungsvorschlag“.
