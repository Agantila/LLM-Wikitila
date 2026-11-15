---
name: read-text-normalisiert-crlf
description: Path.read_text wandelt CRLF in LF, Frontmatter-Regex mit \n funktioniert auch für Windows-Dateien
type: learning
---
`Path.read_text()` nutzt Universal Newlines, CRLF kommt als `\n` an. Die Frontmatter-Regex `---\n…\n---\n` erkennt deshalb auch Dateien mit Windows-Zeilenenden (im Review 2026-11-15 getestet).
**Warum:** Der Vault stammt ursprünglich von Windows. Der Verdacht auf ignoriertes `superseded_by` lag nahe, hat sich aber nicht bestätigt.
**Anwenden:** Nicht „fixen“. Nur wenn Dateien je binär (`read_bytes`) gelesen werden, muss CRLF selbst behandelt werden.
