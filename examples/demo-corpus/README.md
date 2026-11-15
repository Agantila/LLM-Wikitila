# Demo-Korpus

Synthetischer Mini-Ordner passend zu `golden_catalog.example.jsonl` und `authority_register.example.json`.
Damit lässt sich die Katalog-Validierung ohne echten Vault reproduzieren (auch in der CI):

```bash
python3 wikitila.py --root examples/demo-corpus build
python3 validate_catalog.py --root examples/demo-corpus --catalog golden_catalog.example.jsonl
```

Die Zahlen hier belegen nur, dass die Werkzeugkette funktioniert — nicht die Qualität auf einem echten Ordner.
