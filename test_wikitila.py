"""Tests für wikitila.py mit einem synthetischen Mini-Korpus (keine Vault-Daten, kein Ollama).

Aufruf: python3 -m unittest test_wikitila -v   (im Repo-Wurzelordner)
"""
import json, os, subprocess, sys, tempfile, unittest
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
        c = W.connect(self.root, self.cfg)
        self.addCleanup(c.close)
        return c

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
            srv.shutdown(); srv.server_close()

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


    # ---------- Review 2026-11-15 (F1–F13), siehe pm/plans/2026-11-15-review-fixes.md ----------

    def test_f1_example_config_uses_wikitila_dir(self):
        import tomllib
        here = Path(__file__).resolve().parent
        ex = tomllib.loads((here / "config.example.toml").read_text(encoding="utf-8"))
        self.assertEqual(ex["index"]["db"], W.DEFAULTS["index"]["db"])
        self.assertTrue(ex["index"]["db"].startswith(".wikitila/"))
        self.assertIn(".wikitila/", ex["corpus"]["extra_ignore"])

    def test_f2_secret_in_first_line_masked_everywhere(self):
        (self.root / "09_Personal/Notiz.md").write_text(
            "token: Zx9fakeSECRETvalue12345\n\nNotiz zur Lieferantenliste mit weiteren Details zum Projekt.\n", encoding="utf-8")
        c = self.build()
        res = W.search(c, self.cfg, "Lieferantenliste", 3)
        dump = json.dumps(res, ensure_ascii=False)
        self.assertNotIn("Zx9fakeSECRETvalue12345", dump)
        self.assertEqual(res["results"][0]["path"], "09_Personal/Notiz.md")

    def test_f3_chunks_mapping_stays_consistent(self):
        c = self.build()
        n = lambda q: c.execute(q).fetchone()[0]
        self.assertEqual(n("select count(*) from t"), n("select count(*) from chunks"))
        (self.root / "06_Marketing/TikTok_Specs.md").write_text("# TikTok Specs\n\n## Neu\n\nNur noch ein Abschnitt mit genug Text.\n", encoding="utf-8")
        (self.root / "01_Strategie/Preise.md").unlink()
        c = self.build()
        self.assertEqual(n("select count(*) from t"), n("select count(*) from chunks"))
        self.assertEqual(n("select count(*) from chunks c left join t on t.rowid=c.cid where t.rowid is null"), 0)
        self.assertEqual(n("select count(*) from chunks where path='01_Strategie/Preise.md'"), 0)
        self.assertEqual(n("select count(*) from chunks where path='06_Marketing/TikTok_Specs.md'"), 1)

    def test_f3_migration_of_old_index(self):
        c = self.build()
        c.execute("drop table chunks"); c.execute("delete from meta where k='schema'"); c.commit(); c.close()
        c = W.connect(self.root, self.cfg)
        self.addCleanup(c.close)
        self.assertEqual(c.execute("select count(*) from chunks").fetchone()[0], c.execute("select count(*) from t").fetchone()[0])
        self.assertEqual(W.search(c, self.cfg, "Safe Zones TikTok", 3)["results"][0]["path"], "06_Marketing/TikTok_Specs.md")

    def test_f5_broken_register_warns(self):
        (self.root / "authority_register.json").write_text("{kaputt", encoding="utf-8")
        cfg = W.load_cfg(self.root)
        res = W.search(self.build(), cfg, "Safe Zones TikTok", 3)
        self.assertTrue(any("Authority-Register" in w for w in res["warnings"]))

    def test_f5_register_wrong_types_do_not_crash(self):
        for data in ([], {"entries": "x"}, {"entries": [1, {"canonical": 5}, {"canonical": "06_Marketing/TikTok_Specs.md",
                                                                               "stale_after": 20250101, "value": "Safe",
                                                                               "supersedes": "x", "id": 3}]}):
            (self.root / "authority_register.json").write_text(json.dumps(data), encoding="utf-8")
            cfg = W.load_cfg(self.root)
            res = W.search(self.build(), cfg, "Safe Zones TikTok", 3)
            self.assertTrue(res["warnings"], data)
            self.assertEqual(res["results"][0]["path"], "06_Marketing/TikTok_Specs.md")

    def test_f6_missing_or_empty_index_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg = W.load_cfg(root)
            with self.assertRaises(W.WikitilaError):
                W.require_index(root, cfg)
            self.assertFalse((root / ".wikitila").exists())   # Lesebefehle legen nichts an
            W.cmd_build(root, cfg)                              # leerer Ordner -> leerer Index
            with self.assertRaises(W.WikitilaError):
                W.require_index(root, cfg)

    def test_f6_cli_exit_code(self):
        with tempfile.TemporaryDirectory() as d:
            here = Path(__file__).resolve().parent
            r = subprocess.run([sys.executable, str(here / "wikitila.py"), "--root", d, "search", "x"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn("build", r.stderr)
            self.assertNotIn("Traceback", r.stderr)

    @unittest.skipIf(os.name == "nt", "Symlinks unter Windows nur mit Rechten")
    def test_f7_f8_symlinks_outside_root_and_broken(self):
        with tempfile.TemporaryDirectory() as outside:
            (Path(outside) / "x.md").write_text("# Aussen\n\nMarmelade Rezept außerhalb des Ordners mit Text.\n", encoding="utf-8")
            os.symlink(Path(outside) / "x.md", self.root / "link.md")
            os.symlink(self.root / "fehlt.md", self.root / "kaputt.md")
            (self.root / "intern.md").symlink_to(self.root / "06_Marketing/TikTok_Specs.md")
            c = self.build()
            paths = {p for (p,) in c.execute("select path from files")}
            self.assertNotIn("link.md", paths)
            self.assertNotIn("kaputt.md", paths)
            self.assertIn("intern.md", paths)                   # Symlink innerhalb des Ordners bleibt erlaubt
            W.cmd_manifest(self.root, self.cfg, None)            # darf nicht abbrechen
            m = json.loads((self.root / ".wikitila/source_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(m["totals"]["symlink_outside_root"], 2)

    def test_f9_broken_toml_is_clear_error(self):
        (self.root / "wikitila.toml").write_text("[rank\n", encoding="utf-8")
        with self.assertRaises(W.WikitilaError):
            W.load_cfg(self.root)

    def test_f9_broken_graph_json_does_not_stop_build(self):
        (self.root / "graphify-out").mkdir()
        (self.root / "graphify-out/graph.json").write_text("{x", encoding="utf-8")
        c = self.build()
        self.assertGreater(c.execute("select count(*) from files").fetchone()[0], 0)
        self.assertEqual(c.execute("select count(*) from ent").fetchone()[0], 0)

    def test_f10_oversized_file_skipped_by_bytes(self):
        (self.root / "gross.md").write_text("# Gross\n\n" + "ä" * (W.MAX_FILE_BYTES // 2 + 10), encoding="utf-8")
        c = self.build()
        self.assertNotIn("gross.md", {p for (p,) in c.execute("select path from files")})
        self.assertFalse(W.cmd_check(self.root, self.cfg, None))   # check zählt gleich wie build

    def test_f11_superseded_penalty_applied_once(self):
        c = self.build()
        q = "Starter kostet EUR"
        score = lambda cfg: next(h["score"] for h in W.search(c, cfg, q, 5)["results"] if h["path"] == "01_Strategie/Preise.md")
        only_fm = score(self.cfg)
        (self.root / "authority_register.json").write_text(json.dumps({"entries": [{
            "id": "p", "canonical": "01_Strategie/Preise_neu.md", "supersedes": ["01_Strategie/Preise.md"],
            "authority": "canonical", "authority_confirmed": True}]}), encoding="utf-8")
        both = score(W.load_cfg(self.root))
        self.assertAlmostEqual(only_fm, both, places=5)

    def test_f13_demo_corpus_reproduces_example_catalog(self):
        here = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as d:
            import shutil
            root = Path(d) / "demo"
            shutil.copytree(here / "examples/demo-corpus", root, ignore=shutil.ignore_patterns(".wikitila"))
            cfg = W.load_cfg(root)
            W.cmd_build(root, cfg)
            c = W.require_index(root, cfg)
            self.addCleanup(c.close)
            for line in (here / "golden_catalog.example.jsonl").read_text(encoding="utf-8").splitlines():
                g = json.loads(line)
                if g["kind"] in ("positiv", "authority"):
                    paths = [h["path"] for h in W.search(c, cfg, g["q"], 10)["results"]]
                    self.assertTrue(set(g["expect"]) & set(paths), g["q"])

    # ---------- Qualität/Suchsicht (Plan 2026-11-25, P1–P5) ----------

    def test_numeric_tokens_kept(self):
        self.assertEqual(W.tokens("Preis 1.199 EUR"), ["preis", "199", "eur"])
        self.assertEqual(W.tokens("Stand 10.794 Knoten"), ["stand", "10", "794", "knoten"])

    def test_frontmatter_status_searchable(self):
        (self.root / "06_Marketing/Preisbeschluss.md").write_text(
            "---\ntitle: Preisbeschluss\nstatus: proposed\n---\n# Preisbeschluss\n\nDie Erhöhung ist noch nicht verbindlich.\n", encoding="utf-8")
        c = self.build()
        r = W.search(c, self.cfg, "Preisbeschluss proposed", 5)["results"]
        self.assertEqual(r[0]["path"], "06_Marketing/Preisbeschluss.md")

    def test_authority_value_chunks_preferred_and_metadata(self):
        (self.root / "06_Marketing/Preise_Multi.md").write_text(
            "# Preise\n\n## Einleitung\n\nViele Details zum Produkt und seinen Stufen.\n\n## Aktuell\n\nDer Preis beträgt 549 EUR heute.\n\n## Alt\n\nFrüher waren es 299 EUR.\n", encoding="utf-8")
        (self.root / "authority_register.json").write_text(json.dumps({
            "entries": [{"id": "preise", "scope": "Preise", "canonical": "06_Marketing/Preise_Multi.md",
                         "authority": "canonical", "verified_at": "2026-11-14", "stale_after": None,
                         "supersedes": [], "status": "accepted", "authority_confirmed": True,
                         "value": ["549"]}]}), encoding="utf-8")
        cfg = W.load_cfg(self.root)
        c = self.build()
        top = W.search(c, cfg, "Preise Produkt Details", 5)["results"][0]
        self.assertEqual(top["path"], "06_Marketing/Preise_Multi.md")
        joined = " ".join(p["heading"] + " " + p["body"] for p in top["passages"])
        self.assertIn("549", joined)
        self.assertEqual(top["authority"], "canonical")
        self.assertEqual(top["verified_at"], "2026-11-14")

    def test_authority_value_slash_separated(self):
        (self.root / "06_Marketing/Preise_Kompakt.md").write_text(
            "# Preise\n\n## Übersicht\n\nDrei Produktstufen mit unterschiedlichen Preisen für verschiedene Zielgruppen.\n\n"
            "## Starter\n\nDas Starter-Paket kostet 549 EUR monatlich und enthält Basis-Features.\n\n"
            "## Pro\n\nDas Pro-Paket kostet 899 EUR monatlich mit erweiterten Features.\n\n"
            "## Premium\n\nDas Premium-Paket kostet 1.199 EUR monatlich mit allen Features.\n", encoding="utf-8")
        (self.root / "authority_register.json").write_text(json.dumps({
            "entries": [{"id": "preise", "scope": "Preise", "canonical": "06_Marketing/Preise_Kompakt.md",
                         "authority": "canonical", "verified_at": "2026-11-14", "stale_after": None,
                         "supersedes": [], "status": "proposed", "authority_confirmed": False,
                         "value": ["549/899/1.199"]}]}), encoding="utf-8")
        cfg = W.load_cfg(self.root)
        c = self.build()
        res = W.search(c, cfg, "Preise Produktstufen Zielgruppen", 5)["results"]
        # Absicht: der Register-Wert-Chunk steht in den Passagen der kanonischen Datei (B-015).
        # Rang 1 ist hier nicht Gegenstand: im Mini-Korpus entscheidet ein Graph-Bonus von 0,001
        # zwischen den beiden Top-Dateien (seit B-010 zählt nur der beste Chunk je Datei).
        top = next(h for h in res if h["path"] == "06_Marketing/Preise_Kompakt.md")
        self.assertLessEqual(res.index(top), 1)
        joined = " ".join(p["heading"] + " " + p["body"] for p in top["passages"])
        self.assertIn("549", joined)

    def test_coverage_grade_near_topic_negative(self):
        (self.root / "06_Marketing/pinterest.md").write_text(
            "# Pinterest\n\nPinterest ist eine weitere Plattform.\n", encoding="utf-8")
        c = self.build()
        res = W.search(c, self.cfg, "Welche Safe Zones gelten für Pinterest?", 3)
        self.assertLess(res["term_coverage"], 1.0)
        self.assertIn("pinterest", res["uncovered"])
        full = W.search(c, self.cfg, "Safe Zones TikTok Prozent", 3)
        self.assertEqual(full["term_coverage"], 1.0)

    def test_trace_and_gate_reason(self):
        c = self.build()
        res = W.search(c, self.cfg, "Starter kostet EUR", 3)
        self.assertEqual(res["answer_status"], "widersprüchlich")
        self.assertIn("trace", res)
        self.assertEqual(res["trace"]["query_tokens"], W.tokens("Starter kostet EUR"))
        self.assertIn("abgelöste Quelle", res["trace"]["gate"])

    def test_short_section_with_heading_is_indexed(self):
        (self.root / "06_Marketing/Schrift.md").write_text(
            "# Fonts\n\n## Hauptschrift\n\nBai Jamjuree.\n", encoding="utf-8")
        c = self.build()
        r = W.search(c, self.cfg, "Bai Jamjuree", 3)["results"]
        self.assertEqual(r[0]["path"], "06_Marketing/Schrift.md")


class TestLint(unittest.TestCase):
    """Schreibseite (Plan 2026-11-27, B-020): lint prüft Frontmatter mit derselben
    Sicht wie der Index (parse_doc), zweistufig Verstoss/Hinweis."""

    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.root = Path(self.d.name)
        make(self.root, {
            "konform.md": "---\ntitle: Preise\ndescription: \"Aktuelle Preise.\"\nstatus: draft\n---\n# Preise\n\nText.\n",
            "ohne_fm.md": "# Ohne Frontmatter\n\nText.\n",
            "ohne_description.md": "---\ntitle: Nur Titel\n---\n# Titel\n\nText.\n",
            "doppelpunkt.md": "---\ntitle: Runbook\ndescription: Anleitung für Produktionen: Schritt eins\n---\n# Runbook\n\nText.\n",
            "status_frei.md": "---\ntitle: Entscheid\ndescription: \"Beschluss.\"\nstatus: accepted\n---\n# X\n\nText.\n",
            "copy_social.md": "# Copy\n\nText ohne Frontmatter.\n",
        })
        self.cfg = W.load_cfg(self.root)

    def tearDown(self):
        self.d.cleanup()

    def test_konform(self):
        errors, notes = W.lint_text((self.root / "konform.md").read_text(encoding="utf-8"), self.cfg)
        self.assertEqual(errors, [])
        self.assertEqual(notes, [])

    def test_kein_frontmatter_ist_verstoss(self):
        errors, _ = W.lint_text((self.root / "ohne_fm.md").read_text(encoding="utf-8"), self.cfg)
        self.assertTrue(any("kein Frontmatter" in e for e in errors))

    def test_fehlendes_pflichtfeld_ist_verstoss(self):
        errors, _ = W.lint_text((self.root / "ohne_description.md").read_text(encoding="utf-8"), self.cfg)
        self.assertTrue(any("'description'" in e for e in errors))

    def test_unquotierter_doppelpunkt_ist_hinweis_kein_verstoss(self):
        errors, notes = W.lint_text((self.root / "doppelpunkt.md").read_text(encoding="utf-8"), self.cfg)
        self.assertEqual(errors, [])  # der Index liest die Felder zeilenweise weiter
        self.assertTrue(any("Doppelpunkt" in n for n in notes))

    def test_status_ausserhalb_konvention_ist_hinweis(self):
        errors, notes = W.lint_text((self.root / "status_frei.md").read_text(encoding="utf-8"), self.cfg)
        self.assertEqual(errors, [])
        self.assertTrue(any("status" in n for n in notes))

    def test_exclude_muster_greift_auf_dateinamen(self):
        self.assertTrue(W.lint_excluded("06_Marketing/copy_social.md", self.cfg["lint"]["exclude"]))
        self.assertTrue(W.lint_excluded("x/README.md", self.cfg["lint"]["exclude"]))
        self.assertFalse(W.lint_excluded("06_Marketing/konform.md", self.cfg["lint"]["exclude"]))

    def test_require_aus_config_ueberschreibt_default(self):
        (self.root / "wikitila.toml").write_text('[lint]\nrequire = ["title"]\n', encoding="utf-8")
        cfg = W.load_cfg(self.root)
        errors, _ = W.lint_text((self.root / "ohne_description.md").read_text(encoding="utf-8"), cfg)
        self.assertEqual(errors, [])  # description ist hier nicht mehr Pflicht

    def run_lint(self, cfg=None, **kw):
        """cmd_lint mit --json ausführen; liefert (Verstöße?, JSON-Ergebnis), Ausgabe abgefangen."""
        import argparse, contextlib, io
        a = argparse.Namespace(**{"all": False, "json": True, "path": None, **kw})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = W.cmd_lint(self.root, cfg or self.cfg, a)
        return rc, json.loads(buf.getvalue())

    def test_cmd_lint_all_zaehlt_und_filtert(self):
        rc, out = self.run_lint(all=True)
        self.assertTrue(rc)  # ohne_fm.md und ohne_description.md haben Verstösse
        pfade = {f["path"] for f in out["files"] if f["errors"]}
        self.assertEqual(pfade, {"ohne_fm.md", "ohne_description.md"})
        self.assertEqual(out["excluded"], 1)  # copy_social.md
        self.assertEqual(out["checked"], 5)

    def test_cmd_lint_since_laesst_alte_dateien_aussen_vor(self):
        os.utime(self.root / "ohne_fm.md", (1_000_000_000, 1_000_000_000))  # mtime 2001
        (self.root / "wikitila.toml").write_text('[lint]\nsince = "2026-01-01"\n', encoding="utf-8")
        _, out = self.run_lint(cfg=W.load_cfg(self.root), all=True)
        pfade = {f["path"] for f in out["files"] if f["errors"]}
        self.assertEqual(pfade, {"ohne_description.md"})
        self.assertEqual(out["excluded"], 2)  # copy_social.md + ohne_fm.md (zu alt)

    def test_cmd_lint_since_ungueltig_ist_bedienfehler(self):
        (self.root / "wikitila.toml").write_text('[lint]\nsince = "27.11.2026"\n', encoding="utf-8")
        with self.assertRaises(W.WikitilaError):
            self.run_lint(cfg=W.load_cfg(self.root), all=True)

    def test_cmd_lint_all_ignoriert_txt(self):
        (self.root / "notizen.txt").write_text("Freitext ohne Frontmatter.\n", encoding="utf-8")
        _, out = self.run_lint(all=True)
        self.assertNotIn("notizen.txt", {f["path"] for f in out["files"]})
        self.assertEqual(out["checked"], 5)

    def test_exclude_ohne_gross_klein(self):
        self.assertTrue(W.lint_excluded("pm/adr/TEMPLATE.md", self.cfg["lint"]["exclude"]))
        self.assertTrue(W.lint_excluded("x/OKF_FRONTMATTER_TEMPLATE.md", self.cfg["lint"]["exclude"]))

    def test_frontmatter_nicht_abgeschlossen(self):
        errors, _ = W.lint_text("---\ntitle: X\ndescription: \"Y\"\n# Kein Ende\n", self.cfg)
        self.assertTrue(any("nicht abgeschlossen" in e for e in errors))

    def test_cmd_lint_einzeldatei_exit_semantik(self):
        self.assertFalse(self.run_lint(path="konform.md")[0])
        self.assertTrue(self.run_lint(path="ohne_fm.md")[0])

    def test_cmd_lint_einzeldatei_absoluter_pfad(self):
        rc, out = self.run_lint(path=str(self.root / "ohne_fm.md"))
        self.assertTrue(rc)
        self.assertEqual(out["path"], "ohne_fm.md")

    def test_cmd_lint_einzeldatei_ausgenommen_ist_ok(self):
        rc, out = self.run_lint(path="copy_social.md")  # Hook auf ausgenommene Datei: Exit 0
        self.assertFalse(rc)
        self.assertTrue(out["excluded"])

    def test_cmd_lint_einzeldatei_ausserhalb_ist_bedienfehler(self):
        with tempfile.TemporaryDirectory() as fremd:
            f = Path(fremd) / "x.md"
            f.write_text("# X\n", encoding="utf-8")
            with self.assertRaises(W.WikitilaError):
                self.run_lint(path=str(f))
            with self.assertRaises(W.WikitilaError):
                self.run_lint(path=os.path.relpath(f, self.root))


HERE = Path(__file__).resolve().parent


def cli(*args, env=None):
    """wikitila.py als Subprozess (Exit-Codes und Fehlermeldungen wie beim Nutzer)."""
    e = {k: v for k, v in os.environ.items() if k not in ("WIKITILA_CONFIG", "WIKITILA_ROOT")}
    e.update(env or {})
    return subprocess.run([sys.executable, str(HERE / "wikitila.py"), *args], capture_output=True, text=True, env=e)


class TestHaertung(unittest.TestCase):
    """Produktionsreife (Plan 2026-11-27-produktionsreife): Indexformat, Konfiguration,
    Frontmatter-Randfälle, eval, Fehlerpfade der CLI, Katalog-Gate."""

    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.root = Path(self.d.name)
        make(self.root, CORPUS)
        self.cfg = W.load_cfg(self.root)

    def tearDown(self):
        self.d.cleanup()

    def quiet(self, fn, *args):
        import contextlib, io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = fn(*args)
        return rc, out.getvalue(), err.getvalue()

    def toml(self, text):
        (self.root / "wikitila.toml").write_text(text, encoding="utf-8")

    # ---------- P1 Indexformat (ADR-006) ----------
    def test_formatwechsel_erzwingt_vollneubau(self):
        self.quiet(W.cmd_build, self.root, self.cfg)
        with contextlib_closing(W.connect(self.root, self.cfg)) as c:
            self.assertEqual(W.index_format(c), W.INDEX_FORMAT)
            # Index eines älteren Formats simulieren: Verarbeitung anders, Hash gleich
            c.execute("update files set title='ALT' where path='01_Strategie/Preise_neu.md'")
            c.execute("update meta set v='1' where k='format'")
            c.commit()
        _, out, err = self.quiet(W.cmd_build, self.root, self.cfg)
        self.assertIn("Vollneubau", err)
        self.assertIn("5 neu/geändert", out)
        with contextlib_closing(W.connect(self.root, self.cfg)) as c:
            title = c.execute("select title from files where path='01_Strategie/Preise_neu.md'").fetchone()[0]
            self.assertEqual(title, "Preise neu")
            self.assertEqual(W.index_format(c), W.INDEX_FORMAT)
        _, out, err = self.quiet(W.cmd_build, self.root, self.cfg)   # danach wieder inkrementell
        self.assertIn("0 neu/geändert", out)
        self.assertNotIn("Vollneubau", err)

    def test_check_meldet_veraltetes_format_als_drift(self):
        self.quiet(W.cmd_build, self.root, self.cfg)
        import argparse
        self.assertFalse(self.quiet(W.cmd_check, self.root, self.cfg, argparse.Namespace())[0])
        with contextlib_closing(W.connect(self.root, self.cfg)) as c:
            c.execute("delete from meta where k='format'"); c.commit()
        drift, out, _ = self.quiet(W.cmd_check, self.root, self.cfg, argparse.Namespace())
        self.assertTrue(drift)
        self.assertIn("Indexformat veraltet", out)

    # ---------- P2 Konfiguration ----------
    def test_config_falscher_typ_ist_bedienfehler(self):
        for text in ('[lint]\nrequire = "title"\n', 'lint = 5\n', '[index]\nmax_chunk_chars = 0\n',
                     '[rank]\nrrf_k = "60"\n', '[privacy]\nmask_secrets = 1\n', '[index]\nmax_chunk_chars = -5\n'):
            with self.subTest(text=text):
                self.toml(text)
                with self.assertRaises(W.WikitilaError):
                    W.load_cfg(self.root)

    def test_config_unbekanntes_nur_warnung(self):
        self.toml('[lnit]\nrequire = ["title"]\n[rank]\nrrf = 5\nrrf_k = 50\n')
        import contextlib, io
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            cfg = W.load_cfg(self.root)
        self.assertEqual(cfg["rank"]["rrf_k"], 50)
        self.assertIn("[lnit]", err.getvalue())
        self.assertIn("rank.rrf", err.getvalue())

    def test_config_float_akzeptiert_ganze_zahl(self):
        self.toml('[rank]\nsuperseded_factor = 1\n')
        self.assertEqual(W.load_cfg(self.root)["rank"]["superseded_factor"], 1)

    def test_config_beispiel_ist_gueltig(self):
        import contextlib, io, shutil
        shutil.copy(HERE / "config.example.toml", self.root / "wikitila.toml")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            W.load_cfg(self.root)
        self.assertEqual(err.getvalue(), "")

    def test_wikitila_config_auf_fehlende_datei(self):
        r = cli("--root", str(self.root), "status", env={"WIKITILA_CONFIG": str(self.root / "fehlt.toml")})
        self.assertEqual(r.returncode, 2)
        self.assertIn("WIKITILA_CONFIG", r.stderr)

    # ---------- P5 Frontmatter ----------
    def test_frontmatter_bom(self):
        fm, body = W.parse_doc("﻿---\ntitle: Mit BOM\n---\n# Kopf\n\nText.\n")
        self.assertEqual(fm["title"], "Mit BOM")
        self.assertTrue(body.startswith("# Kopf"))
        fm, body = W.parse_doc("﻿# Ohne Frontmatter\n")
        self.assertEqual(fm, {})
        self.assertTrue(body.startswith("# Ohne"))

    def test_frontmatter_am_dateiende_und_leer(self):
        self.assertEqual(W.parse_doc("---\ntitle: Nur Kopf\n---")[0]["title"], "Nur Kopf")
        fm, body = W.parse_doc("---\n---\n# Titel\n\nText\n\n---\n\nNach der Linie.\n")
        self.assertEqual(fm, {})
        self.assertIn("Nach der Linie", body)   # leerer Block verschluckt den Text nicht bis zur nächsten Linie
        self.assertTrue(body.startswith("# Titel"))

    def test_frontmatter_schluessel_mit_bindestrich_und_ziffern(self):
        fm, _ = W.parse_doc("---\ncreated-at: 2026-11-27\nokf2: ja\n---\n# T\n")
        self.assertEqual(fm["created-at"], "2026-11-27")
        self.assertEqual(fm["okf2"], "ja")
        errors, notes = W.lint_text("---\ntitle: T\ndescription: \"D\"\ncreated-at: 2026-11-27\n---\n# T\n", self.cfg)
        self.assertEqual((errors, notes), ([], []))

    def test_lint_bom_datei_konform(self):
        errors, _ = W.lint_text("﻿---\ntitle: T\ndescription: \"D\"\n---\n# T\n", self.cfg)
        self.assertEqual(errors, [])

    def test_bom_titel_im_index(self):
        (self.root / "bom.md").write_text("﻿# Bomtitel\n\nEin Absatz über das Kürbisfeld im Herbst.\n", encoding="utf-8")
        self.quiet(W.cmd_build, self.root, self.cfg)
        with contextlib_closing(W.connect(self.root, self.cfg)) as c:
            self.assertEqual(c.execute("select title from files where path='bom.md'").fetchone()[0], "Bomtitel")

    # ---------- P4 eval ----------
    def test_eval_ueberspringt_negativfaelle(self):
        import argparse
        self.quiet(W.cmd_build, self.root, self.cfg)
        g = self.root / "gold.jsonl"
        g.write_text('{"q":"Was kostet der Starter?","expect":["01_Strategie/Preise_neu.md"]}\n'
                     '{"q":"Wetter in Zimbabwe","expect":[]}\n', encoding="utf-8")
        _, out, _ = self.quiet(W.cmd_eval, self.root, self.cfg, argparse.Namespace(golden=str(g), variants=False, misses=False))
        self.assertIn("R@10 1.00", out)
        self.assertIn("n=1, 1 ohne expect übersprungen", out)

    def test_eval_kaputtes_golden_set(self):
        import argparse
        self.quiet(W.cmd_build, self.root, self.cfg)
        g = self.root / "gold.jsonl"
        for text, msg in (('{"q":"a","expect":["x"]}\n{kaputt\n', ":2:"), ('{"q":"a"}\n', "expect"),
                          ('{"q":"a","expect":[]}\n', "keine Fälle mit erwarteter Datei")):
            with self.subTest(text=text):
                g.write_text(text, encoding="utf-8")
                with self.assertRaises(W.WikitilaError) as cm:
                    W.cmd_eval(self.root, self.cfg, argparse.Namespace(golden=str(g), variants=False, misses=False))
                self.assertIn(msg, str(cm.exception))
        with self.assertRaises(W.WikitilaError):
            W.load_jsonl(str(self.root / "fehlt.jsonl"), {"q": str})

    def test_perzentil_nearest_rank(self):
        self.assertEqual(W.pct(list(range(1, 11)), 0.95), 10)
        self.assertEqual(W.pct(list(range(1, 11)), 0.5), 5)
        self.assertEqual(W.pct([7], 0.95), 7)
        self.assertEqual(W.pct([], 0.95), 0.0)

    # ---------- P9 status ----------
    def test_status_meldet_register_pfade_ohne_index(self):
        (self.root / "authority_register.json").write_text(json.dumps({"entries": [
            {"canonical": "01_Strategie/Preise_neu.md", "supersedes": ["01_Strategie/Tippfehler.md"]}]}), encoding="utf-8")
        cfg = W.load_cfg(self.root)
        self.quiet(W.cmd_build, self.root, cfg)
        _, out, _ = self.quiet(W.cmd_status, self.root, cfg)
        self.assertIn("Register-Pfad nicht im Index", out)
        self.assertIn("Tippfehler.md", out)
        self.assertNotIn("Preise_neu.md (", out)

    # ---------- P3/P10 CLI-Fehlerpfade ----------
    def test_cli_k_muss_positiv_sein(self):
        self.quiet(W.cmd_build, self.root, self.cfg)
        for k in ("0", "-3", "zwei"):
            r = cli("--root", str(self.root), "search", "Preise", "-k", k)
            self.assertEqual(r.returncode, 2, k)
            self.assertNotIn("Traceback", r.stderr)

    def test_cli_root_fehlt(self):
        r = cli("--root", str(self.root / "gibt_es_nicht"), "build")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Ordner nicht gefunden", r.stderr)
        self.assertFalse((self.root / "gibt_es_nicht").exists())   # build legt keinen Phantom-Ordner an

    def test_cli_kaputter_index_ohne_traceback(self):
        db = self.root / ".wikitila" / "index.db"
        db.parent.mkdir(parents=True)
        db.write_bytes(b"kein SQLite " * 200)
        r = cli("--root", str(self.root), "status")
        self.assertEqual(r.returncode, 2)
        self.assertIn("SQLite", r.stderr)
        self.assertIn(".wikitila/", r.stderr)   # Hinweis: Index löschen und neu bauen
        self.assertNotIn("Traceback", r.stderr)

    def test_cli_embed_ohne_dienst_ohne_traceback(self):
        self.toml('[embedding]\nurl = "http://127.0.0.1:9"\n')
        self.assertEqual(cli("--root", str(self.root), "build").returncode, 0)
        r = cli("--root", str(self.root), "embed")
        self.assertEqual(r.returncode, 2)   # numpy fehlt (CI) oder Dienst nicht erreichbar
        self.assertIn("FEHLER", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_cli_kaputte_konfiguration(self):
        self.toml('[lint]\nrequire = "title"\n')
        r = cli("--root", str(self.root), "lint", "--all")
        self.assertEqual(r.returncode, 2)
        self.assertIn("lint.require", r.stderr)

    # ---------- P6/P7 Demo-Korpus und Katalog-Gate ----------
    def demo(self):
        import shutil
        root = self.root / "demo"
        shutil.copytree(HERE / "examples/demo-corpus", root, ignore=shutil.ignore_patterns(".wikitila"))
        return root

    def test_demo_korpus_ist_lint_konform(self):
        import argparse
        root = self.demo()
        rc, out, _ = self.quiet(W.cmd_lint, root, W.load_cfg(root), argparse.Namespace(all=True, json=True, path=None))
        self.assertFalse(rc, out)
        self.assertEqual(json.loads(out)["notes"], 0)

    def test_validate_catalog_gate(self):
        root = self.demo()
        self.assertEqual(cli("--root", str(root), "build").returncode, 0)
        vc = [sys.executable, str(HERE / "validate_catalog.py"), "--root", str(root), "--gate", "--catalog"]
        r = subprocess.run(vc + [str(HERE / "golden_catalog.example.jsonl")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("GATE: bestanden", r.stdout)
        bad = self.root / "bad.jsonl"
        bad.write_text('{"q":"Welche Farbe ist die Akzentfarbe der Marke?","kind":"positiv","expect":["doku/fehlt.md"]}\n',
                       encoding="utf-8")
        r = subprocess.run(vc + [str(bad)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("GATE: nicht bestanden", r.stdout)
        bad.write_text('{"q":"x","kind":"unbekannt","expect":[]}\n', encoding="utf-8")
        r = subprocess.run(vc + [str(bad)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)


class TestRankingB010(unittest.TestCase):
    """B-010 (Plan 2026-11-27-b010-ranking): Dateiscore aus dem besten Chunk, nicht aus der Summe."""

    def test_bester_chunk_schlaegt_viele_schwache(self):
        # Datei "kurz" hat den besten Chunk (Rang 0); "lang" hat drei schwächere (Ränge 1–3)
        cpath = {10: "kurz.md", 11: "lang.md", 12: "lang.md", 13: "lang.md"}
        sc = W.file_scores([[10, 11, 12, 13]], cpath, 60)
        self.assertGreater(sc["kurz.md"], sc["lang.md"])
        sc3 = W.file_scores([[10, 11, 12, 13]], cpath, 60, per_file=3)   # alte Aggregation kehrt es um
        self.assertGreater(sc3["lang.md"], sc3["kurz.md"])

    def test_chunks_per_file_konfigurierbar_und_geprueft(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertEqual(W.load_cfg(root)["rank"]["chunks_per_file"], 1)
            (root / "wikitila.toml").write_text("[rank]\nchunks_per_file = 3\n", encoding="utf-8")
            self.assertEqual(W.load_cfg(root)["rank"]["chunks_per_file"], 3)
            (root / "wikitila.toml").write_text("[rank]\nchunks_per_file = 0\n", encoding="utf-8")
            with self.assertRaises(W.WikitilaError):
                W.load_cfg(root)

    def test_suche_praeziese_kurze_datei_vor_langer(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            lang = "# Handbuch\n\n" + "\n\n".join(
                f"## Abschnitt {i}\n\nAllgemeines zur Kampagne und zu Formaten, Teil {i}, mit vielen Wörtern." for i in range(8))
            make(root, {"handbuch.md": lang,
                        "reels.md": "# Reels\n\nBei Reels unten 20 Prozent für Buttons der Kampagne frei halten.\n"})
            cfg = W.load_cfg(root)
            import contextlib, io
            with contextlib.redirect_stdout(io.StringIO()):
                W.cmd_build(root, cfg)
            with contextlib.closing(W.require_index(root, cfg)) as c:
                r = W.search(c, cfg, "Reels Buttons Kampagne frei", 5)["results"]
            self.assertEqual(r[0]["path"], "reels.md")


def contextlib_closing(c):
    import contextlib
    return contextlib.closing(c)


if __name__ == "__main__":
    unittest.main()
