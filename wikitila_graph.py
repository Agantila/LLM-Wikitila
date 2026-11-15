#!/usr/bin/python3
"""Lokale semantische Graphify-Extraktion (Ollama, ohne Thinking) und Graph-Aufbau.

Ersetzt nur den Subagenten-Schritt (Step 3B) des Graphify-Skills. Alles andere
(AST, Cache, Build, Cluster, Bericht, Manifest) nutzt das Graphify-Paket.

Aufruf (mit dem Python, in dem graphify installiert ist, hier /usr/bin/python3):
  wikitila_graph.py [--root DIR] bench --models a,b,c [--n 8]     Modelle vergleichen
  wikitila_graph.py run   --model M [--workers 3] [--limit N]   Extraktion, fortsetzbar
  wikitila_graph.py build [--no-ast]                 Graph, Cluster, Bericht, Manifest

Der Cache liegt im Graphify-Cache (graphify-out/cache), Schlüssel ist der Hash
des Dateiinhalts ohne Frontmatter. Ein zweiter Lauf überspringt unveränderte Dateien.
"""
from __future__ import annotations

import argparse, hashlib, json, os, re, sys, time, unicodedata, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(os.environ.get("WIKITILA_ROOT", ".")).resolve()
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MAX_CHARS = int(os.environ.get("WIKITILA_MAX_CHARS", "7000"))  # Kopf des Dokuments
NUM_CTX = int(os.environ.get("WIKITILA_NUM_CTX", "6144"))
NUM_PREDICT = int(os.environ.get("WIKITILA_NUM_PREDICT", "900"))

REL = ["uses", "part_of", "depends_on", "decides", "replaces", "related_to", "defines", "targets", "produces"]
ETYPES = ["concept", "product", "tool", "person", "org", "decision", "process", "place", "metric"]

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "entities": {"type": "array", "maxItems": 12, "items": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "type": {"type": "string", "enum": ETYPES}},
            "required": ["name", "type"]}},
        "relations": {"type": "array", "maxItems": 10, "items": {
            "type": "object",
            "properties": {"source": {"type": "string"}, "target": {"type": "string"},
                           "relation": {"type": "string", "enum": REL},
                           "evidence": {"type": "string", "enum": ["EXTRACTED", "INFERRED"]}},
            "required": ["source", "target", "relation", "evidence"]}},
    },
    "required": ["summary", "entities", "relations"],
}

SYSTEM = (
    "You extract a small knowledge-graph fragment from one document of a company knowledge base. "
    "Answer with JSON only. Keep names exactly as written in the document (German stays German).\n"
    "- summary: one factual sentence, at most 28 words, what the document is and decides.\n"
    "- entities: up to 12 specific things: named concepts, products, tools, people, organisations, "
    "decisions, processes, metrics. No generic words (e.g. 'Text', 'Datei', 'Beispiel'). Prefer the "
    "short canonical name (e.g. 'Second Brain Starter', 'ADR-008', 'Graphify', 'Safe Zones').\n"
    "- relations: up to 10 between the listed entities only. EXTRACTED if the text says it explicitly, "
    "INFERRED if it is a reasonable conclusion. 'decides' = a decision selects/rejects something, "
    "'replaces' = supersedes an older thing."
)


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")[:80] or "x"


def docid(rel: str) -> str:
    """Eindeutige Dokument-ID: gekürzter Pfad plus Hash (gekürzte Pfade kollidierten bei 221 Dokumenten)."""
    return "doc_" + slug(rel)[:60] + "_" + hashlib.sha1(rel.encode("utf-8")).hexdigest()[:8]


def read_doc(path: Path) -> tuple[str, str]:
    t = path.read_text(encoding="utf-8", errors="ignore")
    if t.startswith("---"):
        m = re.match(r"---\n.*?\n---\n", t, re.S)
        if m:
            t = t[m.end():]
    title = path.stem
    mt = re.search(r"^#\s+(.+)$", t, re.M)
    if mt:
        title = mt.group(1).strip()
    body = t[:MAX_CHARS]
    if len(t) > MAX_CHARS:
        heads = re.findall(r"(?m)^#{2,3}\s+(.+)$", t[MAX_CHARS:])
        body += "\n\n[... gekürzt. Weitere Überschriften: " + "; ".join(heads[:25]) + "]"
    return title, body


def chat(model: str, user: str, timeout: int = 240) -> tuple[dict, dict]:
    payload = {
        "model": model, "stream": False, "think": False, "format": SCHEMA, "keep_alive": "30m",
        "options": {"temperature": 0, "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT, "repeat_penalty": 1.1},
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
    }
    req = urllib.request.Request(f"{OLLAMA}/api/chat", json.dumps(payload).encode(), {"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=timeout))
    return json.loads(d["message"]["content"]), d


def to_graphify(rel: str, title: str, res: dict) -> dict:
    did = docid(rel)
    nodes = [{"id": did, "label": title, "file_type": "document", "source_file": rel,
              "source_location": None, "summary": (res.get("summary") or "")[:300]}]
    edges, by_name = [], {}
    for e in res.get("entities", [])[:12]:
        name = (e.get("name") or "").strip()
        if len(name) < 3 or len(name) > 80:
            continue
        eid = "ent_" + slug(name)
        by_name[name.lower()] = eid
        nodes.append({"id": eid, "label": name, "file_type": "concept", "source_file": rel,
                      "source_location": None, "entity_type": e.get("type", "concept")})
        edges.append({"source": did, "target": eid, "relation": "references", "confidence": "EXTRACTED",
                      "confidence_score": 1.0, "source_file": rel, "source_location": None, "weight": 1.0})
    for r in res.get("relations", [])[:10]:
        a, b = by_name.get((r.get("source") or "").strip().lower()), by_name.get((r.get("target") or "").strip().lower())
        if not a or not b or a == b:
            continue
        # Messung 2026-11-12: kleine lokale Modelle vergeben die Relationsart oft falsch
        # ("A replaces B" ohne Beleg). Darum immer neutral und nie EXTRACTED; die Art des
        # Modells bleibt als Attribut erhalten. Tragend sind die Dokument-Entitäts-Kanten.
        edges.append({"source": a, "target": b, "relation": "related_to", "model_relation": r.get("relation"),
                      "confidence": "INFERRED", "confidence_score": 0.5, "source_file": rel,
                      "source_location": None, "weight": 0.5})
    return {"nodes": nodes, "edges": edges, "hyperedges": []}


def detect_docs() -> dict:
    import graphify.detect as D
    # Sensible Dateien bleiben auffindbar: nur echte Schlüsseldateien überspringen.
    D._is_sensitive = lambda p: bool(re.search(r"(\.pem|\.key|\.p12|\.pfx|id_rsa|id_ed25519|\.env($|\.))", p.name, re.I))
    return D.detect(ROOT)


def sample_docs(n: int) -> list[Path]:
    det = json.loads(Path(os.environ.get("WIKITILA_DETECT", "")).read_text()) if os.environ.get("WIKITILA_DETECT") else detect_docs()
    docs = [Path(f) for f in det["files"]["document"] if str(f).endswith(".md")]
    docs.sort(key=lambda p: slug(str(p)))
    step = max(1, len(docs) // max(n, 1))
    return [d if d.is_absolute() else ROOT / d for d in docs[step::step][:n]]


def cmd_bench(a):
    docs = sample_docs(a.n)
    out = {}
    for m in a.models.split(","):
        rows, tot_t, bad = [], 0.0, 0
        try:
            chat(m, "Titel: Test\n\nKurzer Testtext über das eigene Projekt.")  # Laden/Warmup
        except Exception as e:
            print(f"{m}: nicht nutzbar ({e})"); continue
        for p in docs:
            title, body = read_doc(p)
            t0 = time.time()
            try:
                res, d = chat(m, f"Titel: {title}\n\n{body}")
                dt = time.time() - t0
                g = to_graphify(str(p.relative_to(ROOT)), title, res)
                rows.append({"doc": str(p.relative_to(ROOT)), "s": round(dt, 1), "in": d.get("prompt_eval_count"),
                             "out": d.get("eval_count"), "ents": len(res["entities"]), "rels": len(res["relations"]),
                             "kept_rels": sum(1 for e in g["edges"] if e["relation"] != "references"), "res": res})
                tot_t += dt
            except Exception as e:
                bad += 1; rows.append({"doc": str(p), "err": str(e)[:120]})
        ok = [r for r in rows if "err" not in r]
        if ok:
            print(f"{m:44s} ok {len(ok)}/{len(rows)}  {sum(r['s'] for r in ok)/len(ok):5.1f}s/Doku  "
                  f"in {sum(r['in'] for r in ok)//len(ok)} out {sum(r['out'] for r in ok)//len(ok)} tok  "
                  f"Entitäten {sum(r['ents'] for r in ok)/len(ok):4.1f}  Relationen {sum(r['kept_rels'] for r in ok)/len(ok):4.1f}")
        out[m] = rows
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))


def cmd_run(a):
    from graphify.cache import load_cached, save_cached
    det = detect_docs()
    docs = [Path(f) if Path(f).is_absolute() else ROOT / f for f in det["files"]["document"]]
    docs = [p for p in docs if p.suffix in (".md", ".txt")]
    todo = [p for p in docs if load_cached(p, ROOT) is None]
    if a.limit:
        todo = todo[: a.limit]
    print(f"Dokumente {len(docs)}, im Cache {len(docs)-len(todo) if not a.limit else '?'}, offen {len(todo)}, Modell {a.model}, Worker {a.workers}", flush=True)
    t0, done, fail = time.time(), 0, 0
    (ROOT / "graphify-out").mkdir(exist_ok=True)
    log = open(ROOT / "graphify-out" / "wikitila_run.log", "a", encoding="utf-8")

    def work(p: Path):
        title, body = read_doc(p)
        if len(body.strip()) < 60:
            return p, {"nodes": [{"id": docid(str(p.relative_to(ROOT))), "label": title, "file_type": "document",
                                  "source_file": str(p.relative_to(ROOT)), "source_location": None}], "edges": [], "hyperedges": []}, None
        last: Exception = RuntimeError("keine Antwort")
        for _ in range(2):
            try:
                res, d = chat(a.model, f"Titel: {title}\n\n{body}")
                return p, to_graphify(str(p.relative_to(ROOT)), title, res), d
            except Exception as e:
                last = e
        raise last

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(work, p): p for p in todo}
        for f in as_completed(futs):
            p = futs[f]
            try:
                _, g, d = f.result()
                save_cached(p, g, ROOT)
                done += 1
            except Exception as e:
                fail += 1
                log.write(f"FAIL {p}: {str(e)[:200]}\n"); log.flush()
            if (done + fail) % 25 == 0:
                el = time.time() - t0
                rate = (done + fail) / el
                print(f"{done+fail}/{len(todo)}  fail {fail}  {rate:.2f} Dok/s  Rest ~{(len(todo)-done-fail)/max(rate,1e-6)/60:.0f} min", flush=True)
    print(f"FERTIG {done} ok, {fail} fehlgeschlagen, {(time.time()-t0)/60:.1f} min", flush=True)


def cmd_build(a):
    import networkx as nx
    from graphify.build import build_from_json
    from graphify.cache import load_cached
    from graphify.cluster import cluster, score_all
    from graphify.analyze import god_nodes, surprising_connections, suggest_questions
    from graphify.report import generate
    from graphify.export import to_json
    from graphify.detect import save_manifest
    det = detect_docs()
    out = ROOT / "graphify-out"
    out.mkdir(exist_ok=True)
    ast = {"nodes": [], "edges": [], "hyperedges": []}
    if not a.no_ast:
        from graphify.extract import collect_files, extract
        code = []
        for f in det["files"]["code"]:
            code.extend(collect_files(Path(f)) if Path(f).is_dir() else [Path(f)])
        if code:
            ast = extract(code)
    print(f"AST: {len(ast['nodes'])} Knoten, {len(ast['edges'])} Kanten", flush=True)
    seen = {n["id"] for n in ast["nodes"]}
    nodes, edges, missing = list(ast["nodes"]), list(ast["edges"]), 0
    edge_seen = set()
    ent_docs: dict[str, set] = {}
    for f in det["files"]["document"]:
        p = Path(f) if Path(f).is_absolute() else ROOT / f
        r = load_cached(p, ROOT)
        if r is None:
            missing += 1
            rel = str(p.relative_to(ROOT))
            title, _ = read_doc(p)
            r = {"nodes": [{"id": docid(rel), "label": title, "file_type": "document",
                            "source_file": rel, "source_location": None}], "edges": []}
        else:  # Cache aus Läufen vor der Hash-ID: Dokument-IDs umbenennen, Kanten mitziehen
            rel = str(p.relative_to(ROOT))
            remap = {n["id"]: docid(rel) for n in r.get("nodes", [])
                     if n.get("file_type") == "document" and str(n["id"]).startswith("doc_") and n.get("source_file") == rel}
            if remap:
                r = {"nodes": [dict(n, id=remap.get(n["id"], n["id"])) for n in r.get("nodes", [])],
                     "edges": [dict(e, source=remap.get(e["source"], e["source"]), target=remap.get(e["target"], e["target"]))
                               for e in r.get("edges", [])]}
        for n in r.get("nodes", []):
            if n["id"] not in seen:
                seen.add(n["id"]); nodes.append(n)
        for e in r.get("edges", []):
            k = (e["source"], e["target"], e["relation"])
            if k in edge_seen:
                continue
            edge_seen.add(k); edges.append(e)
    print(f"Semantik: {len(nodes)-len(ast['nodes'])} Knoten, {len(edges)-len(ast['edges'])} Kanten, ohne Cache {missing} Dokumente", flush=True)
    extraction = {"nodes": nodes, "edges": edges, "hyperedges": [], "input_tokens": 0, "output_tokens": 0}
    G = build_from_json(extraction)
    comms = cluster(G)
    coh = score_all(G, comms)
    gods = god_nodes(G)
    surprises = surprising_connections(G, comms)
    # Community-Namen deterministisch: die drei Knoten mit höchstem Grad
    labels = {}
    for cid, ns in comms.items():
        top = sorted(ns, key=lambda x: -G.degree(x))[:3]
        labels[cid] = " / ".join(G.nodes[x].get("label", x)[:28] for x in top) or f"Community {cid}"
    questions = suggest_questions(G, comms, labels)
    detect_for_report = dict(det)
    rep = generate(G, comms, coh, labels, gods, surprises, detect_for_report,
                   {"input": 0, "output": 0}, str(ROOT), suggested_questions=questions)
    (out / "GRAPH_REPORT.md").write_text(rep)
    to_json(G, comms, str(out / "graph.json"))
    (out / ".graphify_labels.json").write_text(json.dumps({str(k): v for k, v in labels.items()}, ensure_ascii=False))
    save_manifest(det["files"])
    print(f"Graph: {G.number_of_nodes()} Knoten, {G.number_of_edges()} Kanten, {len(comms)} Communities", flush=True)


def main():
    global ROOT
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None, help="Ziel-Ordner (Vorgabe: WIKITILA_ROOT oder aktuelles Verzeichnis)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("bench"); b.add_argument("--models", required=True); b.add_argument("--n", type=int, default=8)
    b.add_argument("--out", default=str(Path(os.environ.get("TMPDIR", "/tmp")) / "wikitila_bench.json"))
    r = sp.add_parser("run"); r.add_argument("--model", required=True); r.add_argument("--workers", type=int, default=3)
    r.add_argument("--limit", type=int, default=0)
    bu = sp.add_parser("build"); bu.add_argument("--no-ast", action="store_true")
    a = ap.parse_args()
    if a.root:
        ROOT = Path(a.root).resolve()
    os.chdir(ROOT)
    {"bench": cmd_bench, "run": cmd_run, "build": cmd_build}[a.cmd](a)


if __name__ == "__main__":
    main()
