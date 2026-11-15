"""Tests für wikitila.py mit einem synthetischen Mini-Korpus (keine Vault-Daten, kein Ollama).

Aufruf: python3 -m unittest test_wikitila -v   (im Ordner second_brain_stack)
"""
import json, os, tempfile, unittest
from pathlib import Path

import wikitila as W


def make(root: Path, files: dict):
    for rel, txt in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")


CORPUS = {
    "01_Strategie/Preise.md": "---\ntitle: Preise\nstatus: superseded\nsuperseded_by: Preise_neu.md\n---\n# Preise\n\nDer Starter kostet 299 EUR.\n",
    "01_Strategie/Preise_neu.md": "# Preise neu\n\nDer Starter kostet 549 EUR. Siehe auch Preise.md und ADR-001.\n",
    "00_Projektmanagement/ADR/ADR-001-Preisstufen.md": "# ADR-001 Preisstufen\n\nEntscheidung zu drei Preisstufen.\n",
    "06_Marketing/TikTok_Specs.md": "# TikTok Specs\n\n## Safe Zones\n\nOben 10 Prozent, unten 20 Prozent frei halten.\n\n## Schrift\n\nBai Jamjuree.\n",
    "09_Personal/Zugang.md": "# Zugang\n\napi_key: sk-abcdefghijklmnopqrstuvwxyz123456\nPasswort: geheim123456\n",
    "node_modules/x/readme.md": "# Fremdcode\n\nSafe Zones in Fremdcode.\n",
    "Archiv/alt.md": "# Alt\n\nSafe Zones alt.\n",
    ".graphifyignore": "Archiv/\n*Template_*.md\n",
}


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.root = Path(self.d.name)
        make(self.root, CORPUS)
        self.cfg = W.load_cfg(self.root)

    def tearDown(self):
        self.d.cleanup()

    def build(self):
        W.cmd_build(self.root, self.cfg)
        return W.connect(self.root, self.cfg)

    def test_ignore_and_sensitive_findable(self):
        c = self.build()
        paths = {p for (p,) in c.execute("select path from files")}
        self.assertNotIn("Archiv/alt.md", paths)
        self.assertNotIn("node_modules/x/readme.md", paths)
        self.assertIn("09_Personal/Zugang.md", paths)  # sensible Ordner bleiben auffindbar

    def test_search_finds_section_and_heading(self):
        c = self.build()
        r = W.search(c, self.cfg, "Welche Safe Zones gelten für TikTok?", 3)["results"]
        self.assertEqual(r[0]["path"], "06_Marketing/TikTok_Specs.md")
        self.assertEqual(r[0]["heading"], "Safe Zones")

    def test_passages_return_best_chunks(self):
        c = self.build()
        r = W.search(c, self.cfg, "Safe Zones TikTok Schrift", 3)["results"]
        self.assertIn("passages", r[0])
        self.assertTrue(1 <= len(r[0]["passages"]) <= 3)
        self.assertEqual(r[0]["passages"][0]["heading"], r[0]["heading"])
        joined = " ".join(p["heading"] + " " + p["body"] for p in r[0]["passages"])
        self.assertIn("20 Prozent", joined)

    def test_manifest_reports_coverage(self):
        self.build()
        W.cmd_manifest(self.root, self.cfg, None)
        mf = self.root / ".wikitila" / "source_manifest.json"
        self.assertTrue(mf.exists())
        m = json.loads(mf.read_text(encoding="utf-8"))
        self.assertGreaterEqual(m["totals"]["indexed"], 1)
        self.assertIn(".md", m["indexed_by_ext"])
        self.assertGreaterEqual(m["totals"]["on_disk"], m["totals"]["indexed"])  # .graphifyignore selbst ist nicht indexiert

    def test_authority_register_supersession(self):
        (self.root / "authority_register.json").write_text(json.dumps({
            "entries": [{"id": "preise", "scope": "Preise", "canonical": "01_Strategie/Preise_neu.md",
                         "authority": "canonical", "owner": "Owner", "verified_at": "2026-11-14",
                         "stale_after": None, "supersedes": ["01_Strategie/Preise.md"], "status": "accepted",
                         "authority_confirmed": True, "note": ""}]}), encoding="utf-8")
        cfg = W.load_cfg(self.root)   # neu laden, damit das Register gelesen wird
        c = self.build()
        r = W.search(c, cfg, "Starter kostet EUR", 5)["results"]
        paths = [h["path"] for h in r]
        self.assertIn("01_Strategie/Preise_neu.md", paths)
        neu = next(h for h in r if h["path"] == "01_Strategie/Preise_neu.md")
        alt = next(h for h in r if h["path"] == "01_Strategie/Preise.md")
        self.assertTrue(neu["canonical"])
        self.assertEqual(alt["superseded_by"], "01_Strategie/Preise_neu.md")
        self.assertLess(paths.index("01_Strategie/Preise_neu.md"), paths.index("01_Strategie/Preise.md"))

    def test_authority_register_scope_surfaces_canonical(self):
        (self.root / "authority_register.json").write_text(json.dumps({
            "entries": [{"id": "such-architektur", "scope": "Such-Architektur des Vaults",
                         "canonical": "00_Projektmanagement/ADR/ADR-001-Preisstufen.md",
                         "authority": "canonical", "owner": "Owner", "verified_at": "2026-11-14",
                         "stale_after": None, "supersedes": [], "status": "accepted",
                         "authority_confirmed": True, "note": ""}]}), encoding="utf-8")
        cfg = W.load_cfg(self.root)
        c = self.build()
        r = W.search(c, cfg, "Welche Such Architektur nutzt der Vault?", 5)["results"]
        self.assertIn("00_Projektmanagement/ADR/ADR-001-Preisstufen.md", [h["path"] for h in r])

    def test_answer_gate_status(self):
        c = self.build()
        self.assertEqual(W.search(c, self.cfg, "Sauerteig backen", 3)["answer_status"], "nicht_belegt")
        self.assertEqual(W.search(c, self.cfg, "Safe Zones TikTok", 3)["answer_status"], "belegt")
        self.assertEqual(W.search(c, self.cfg, "Starter kostet EUR", 3)["answer_status"], "widersprüchlich")

    def test_check_reports_drift(self):
        self.build()
        self.assertFalse(W.cmd_check(self.root, self.cfg, None))          # aktuell -> kein Drift
        (self.root / "06_Marketing/Neu.md").write_text("# Neu\n\nEin neuer Text über Reels.\n", encoding="utf-8")
        self.assertTrue(W.cmd_check(self.root, self.cfg, None))           # neue Datei -> Drift
        self.build()
        self.assertFalse(W.cmd_check(self.root, self.cfg, None))          # nach build -> kein Drift

    def test_stem_prefix_matches_inflection(self):
        c = self.build()
        r = W.search(c, self.cfg, "Preisstufe Entscheidungen", 3)["results"]
        self.assertEqual(r[0]["path"], "00_Projektmanagement/ADR/ADR-001-Preisstufen.md")

    def test_link_graph_and_adr_edges(self):
        c = self.build()
        n = c.execute("select count(*) from links where a='01_Strategie/Preise_neu.md'").fetchone()[0]
        self.assertGreaterEqual(n, 2)  # Preise.md und ADR-001

    def test_superseded_is_demoted_and_flagged(self):
        c = self.build()
        r = W.search(c, self.cfg, "Starter kostet EUR", 3)["results"]
        self.assertEqual(r[0]["path"], "01_Strategie/Preise_neu.md")
        old = next(h for h in r if h["path"] == "01_Strategie/Preise.md")
        self.assertEqual(old["superseded_by"], "Preise_neu.md")

    def test_secrets_are_masked_in_snippets(self):
        c = self.build()
        r = W.search(c, self.cfg, "api_key Passwort Zugang", 3)["results"]
        snip = " ".join(h["snippet"] for h in r)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz123456", snip)
        self.assertNotIn("geheim123456", snip)
        self.assertIn("[maskiert]", snip)

    def test_incremental_build(self):
        self.build()
        (self.root / "06_Marketing/Neu.md").write_text("# Neu\n\nEin neuer Text über Reels.\n", encoding="utf-8")
        (self.root / "01_Strategie/Preise_neu.md").unlink()
        c = self.build()
        paths = {p for (p,) in c.execute("select path from files")}
        self.assertIn("06_Marketing/Neu.md", paths)
        self.assertNotIn("01_Strategie/Preise_neu.md", paths)
        self.assertEqual(c.execute("select count(*) from t where path='01_Strategie/Preise_neu.md'").fetchone()[0], 0)

    def test_graphify_entities_boost_sharing_docs(self):
        g = {"nodes": [
            {"id": "doc_a", "file_type": "document", "source_file": "06_Marketing/TikTok_Specs.md", "label": "A"},
            {"id": "doc_b", "file_type": "document", "source_file": "01_Strategie/Preise_neu.md", "label": "B"},
            {"id": "ent_x", "file_type": "concept", "label": "Bai Jamjuree", "source_file": "x"}],
            "links": [{"source": "doc_a", "target": "ent_x", "relation": "references"},
                      {"source": "ent_x", "target": "doc_b", "relation": "references"}]}  # zweite Kante vertauscht
        (self.root / "graphify-out").mkdir()
        (self.root / "graphify-out/graph.json").write_text(json.dumps(g), encoding="utf-8")
        c = self.build()
        self.assertEqual(c.execute("select count(*) from ent").fetchone()[0], 2)
        r = W.search(c, self.cfg, "Safe Zones TikTok", 5)["results"]
        b = next(h for h in r if h["path"] == "01_Strategie/Preise_neu.md")
        self.assertTrue(any("teilt" in w for w in b["why"]))

    def test_tiny_file_is_still_findable(self):
        (self.root / "06_Marketing/Kurz.md").write_text("# Flyer Kickoff\n", encoding="utf-8")
        c = self.build()
        r = W.search(c, self.cfg, "Flyer Kickoff", 3)["results"]
        self.assertEqual(r[0]["path"], "06_Marketing/Kurz.md")

    def test_decision_systemone_contract_with_mock_server(self):
        import http.server, threading

        seen = []

        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                seen.append((self.path, body))
                p = 0.95 if "Safe Zones" in body["state"]["passage"] else 0.05
                out = json.dumps({"answers": {"relevant": {"type": "noul", "noul": p}}}).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
                self.wfile.write(out)

            def log_message(self, *a):
                pass

        srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            c = self.build()
            cfg = W.merge(self.cfg, {"decision": {"enabled": True, "backend": "systemone", "model": "laya:latest",
                                                  "url": f"http://127.0.0.1:{srv.server_address[1]}"}})
            res = W.search(c, cfg, "Safe Zones TikTok", 3)
            self.assertEqual(res["note"], "Decision-Modell angewendet")
            self.assertEqual(res["results"][0]["path"], "06_Marketing/TikTok_Specs.md")
            self.assertTrue(all(p == "/v1/systemone" for p, _ in seen))
            self.assertEqual(seen[0][1]["questions"]["relevant"]["type"], "noul")
            self.assertEqual(seen[0][1].get("model"), "laya:latest")
        finally:
            srv.shutdown()

    def test_decision_failure_falls_back_to_ranking(self):
        c = self.build()
        cfg = W.merge(self.cfg, {"decision": {"enabled": True, "model": "gibt-es-nicht", "url": "http://127.0.0.1:1"}})
        res = W.search(c, cfg, "Safe Zones TikTok", 3)
        self.assertIn("Rückfall", res["note"])
        self.assertEqual(res["results"][0]["path"], "06_Marketing/TikTok_Specs.md")

    def test_embedding_failure_keeps_bm25(self):
        c = self.build()
        cfg = W.merge(self.cfg, {"embedding": {"enabled": True, "url": "http://127.0.0.1:1"}})
        res = W.search(c, cfg, "Safe Zones TikTok", 3)
        self.assertEqual(res["results"][0]["path"], "06_Marketing/TikTok_Specs.md")


if __name__ == "__main__":
    unittest.main()
