#!/usr/bin/env python3
"""LLM-Wikitila: schlanke Suche über einen Markdown-Ordner.

Nur Standardbibliothek (numpy nur, wenn das optionale Embedding an ist).
Eine SQLite-Datei: FTS5 (BM25), Link-Graph, Entitäten aus Graphify, optionale Vektoren.

  wikitila.py build   [--root DIR]           Index aufbauen oder aktualisieren (inkrementell)
  wikitila.py search  "Frage" [-k 5] [--json]
  wikitila.py eval    golden.jsonl [--variants]   Messung gegen ein Golden Set
  wikitila.py embed                          optional: Vektoren mit einem Ollama-Modell
  wikitila.py status

Konfiguration: <root>/wikitila.toml (siehe config.example.toml).
"""
from __future__ import annotations

import argparse, fnmatch, hashlib, json, math, os, re, sqlite3, sys, time, urllib.request
from collections import defaultdict
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

DEFAULTS = {
    "corpus": {"include_ext": [".md", ".txt"], "ignore_file": ".graphifyignore", "extra_ignore": [".wikitila/", "graphify-out/"]},
    "index": {"db": ".wikitila/index.db", "max_chunk_chars": 450, "min_chunk_chars": 40},
    "rank": {"filename_boost": 0.004, "graph_weight": 0.05, "graph_top": 3, "rrf_k": 60, "stem_prefix": True,
             "superseded_factor": 0.8},
    "graph": {"use_links": True, "use_graphify": True, "graphify_json": "graphify-out/graph.json",
              "entity_max_docs": 40},
    "embedding": {"enabled": False, "model": "embeddinggemma:latest", "url": "http://localhost:11434"},
    "decision": {"enabled": False, "backend": "chat", "model": "", "url": "http://localhost:11434", "top_k": 8, "chars": 400,
                 "token_env": "LAYA_TOKEN"},
    "authority": {"enabled": True, "register": ""},
    "privacy": {"mask_secrets": True},
}

STOP = set("""der die das den dem des ein eine einen einem einer und oder ist sind wird werden wie was wer wo welche welcher
welches wir ich mit ohne für bei auf in im zu zum zur von vom aus nach vor über unter auch nicht nur noch dass damit muss
müssen soll sollen kann können hat haben wofür worauf wann warum nutzen nutzt aktuell the and for with what how which""".split())

SECRET_RES = [
    re.compile(r"\b(sk|pk|rk)-[A-Za-z0-9_\-]{16,}"), re.compile(r"\bAKIA[0-9A-Z]{12,}"),
    re.compile(r"\b(ghp|gho|ghs|xox[bap])[_\-][A-Za-z0-9\-]{16,}"),
    re.compile(r"(?i)\b(passw\w*|token|secret|api[_\- ]?key|apikey)\b\s*[:=]\s*[`'\"]?[^\s`'\"]{8,}"),
    re.compile(r"\b[A-Za-z0-9_\-]{40,}\b"),
]


def merge(base: dict, over: dict) -> dict:
    out = {}
    for k, v in base.items():
        out[k] = {**v, **over.get(k, {})} if isinstance(v, dict) else over.get(k, v)
    return out


def load_register(root: Path, cfg: dict) -> dict:
    """Lädt das Authority-Register (JSON) und baut Ablösungs-/Freshness-Karten.

    Rückgabe: {"superseded_by": {alt -> neu}, "supersedes": {neu -> [alt]}, "meta": {pfad -> {…}}}.
    Leeres Register (Datei fehlt oder nicht aktiv) => leere Karten, die Suche läuft unverändert.
    """
    empty = {"superseded_by": {}, "supersedes": {}, "meta": {}}
    if not cfg.get("authority", {}).get("enabled", True):
        return empty
    rel = (cfg.get("authority", {}) or {}).get("register", "").strip()
    candidates = [root / rel] if rel else []
    candidates.append(root / "authority_register.json")
    path = next((p for p in candidates if p.exists()), None)
    if not path:
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return empty
    out = {"superseded_by": {}, "supersedes": {}, "meta": {}}
    for e in data.get("entries", []):
        canon = e.get("canonical")
        if not canon:
            continue
        out["meta"][canon] = {
            "authority": e.get("authority"),
            "stale_after": e.get("stale_after"),
            "status": e.get("status"),
            "verified_at": e.get("verified_at"),
            "confirmed": bool(e.get("authority_confirmed")),
            "value": e.get("value") or [],
            "alias": " ".join([e.get("id") or "", e.get("scope") or "", e.get("note") or ""]),
        }
        for old in e.get("supersedes") or []:
            out["superseded_by"][old] = canon
            out["supersedes"].setdefault(canon, []).append(old)
    return out


def load_cfg(root: Path) -> dict:
    p = Path(os.environ.get("WIKITILA_CONFIG", root / "wikitila.toml"))
    cfg = merge(DEFAULTS, tomllib.loads(p.read_text(encoding="utf-8"))) if (p.exists() and tomllib) else merge(DEFAULTS, {})
    cfg["_authority"] = load_register(root, cfg)
    return cfg


def mask(t: str) -> str:
    for r in SECRET_RES:
        t = r.sub("[maskiert]", t)
    return t


# ---------- Ignore (gitignore-light) ----------
def load_ignore(root: Path, cfg: dict) -> list[str]:
    pats = list(cfg["corpus"]["extra_ignore"])
    f = root / cfg["corpus"]["ignore_file"]
    if f.exists():
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                pats.append(line)
    return pats


def ignored(rel: str, pats: list[str]) -> bool:
    parts = rel.split("/")
    for pat in pats:
        p = pat.strip()
        if p.startswith("**/"):
            p = p[3:]
        p = p.lstrip("/")
        d = p.endswith("/")
        p = p.rstrip("/")
        if "/" in p:
            if rel == p or rel.startswith(p + "/") or fnmatch.fnmatch(rel, p):
                return True
        else:
            names = parts if d else parts
            if any(fnmatch.fnmatch(x, p) for x in names):
                return True
    return False


def walk(root: Path, cfg: dict):
    pats = load_ignore(root, cfg)
    exts = tuple(cfg["corpus"]["include_ext"])
    for r, dirs, files in os.walk(root):
        rr = os.path.relpath(r, root).replace(os.sep, "/")
        rr = "" if rr == "." else rr
        dirs[:] = [d for d in dirs if not d.startswith(".git") and d != "node_modules"
                   and not ignored((rr + "/" + d).lstrip("/"), pats)]
        for n in files:
            rel = (rr + "/" + n).lstrip("/")
            if n.endswith(exts) and not ignored(rel, pats):
                yield rel


# ---------- Dokumente ----------
def parse_doc(text: str) -> tuple[dict, str]:
    fm = {}
    if text.startswith("---"):
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        if m:
            for line in m.group(1).splitlines():
                mm = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
                if mm:
                    fm[mm.group(1).lower()] = mm.group(2).strip().strip("\"'")
            text = text[m.end():]
    return fm, text


def chunk_text(body: str, cap: int, mn: int) -> list[tuple[str, str]]:
    out = []
    for sec in re.split(r"(?m)^(?=#{1,3}\s)", body):
        sec = sec.strip()
        if len(sec) < mn:
            continue
        head = sec.split("\n", 1)[0].lstrip("# ").strip()
        cur = ""
        for para in re.split(r"\n\s*\n", sec):
            while len(para) > cap * 1.5:  # sehr lange Absätze an Satzgrenzen teilen
                cut = max(para.rfind(". ", 0, cap), para.rfind("\n", 0, cap))
                cut = cut + 1 if cut > cap // 3 else cap
                piece, para = para[:cut], para[cut:].lstrip()
                if cur:
                    out.append((head, cur)); cur = ""
                out.append((head, piece))
            if len(cur) + len(para) > cap and cur:
                out.append((head, cur)); cur = ""
            cur += ("\n\n" if cur else "") + para
        if cur.strip():
            out.append((head, cur))
    return [(h, c) for h, c in out if len(c.strip()) >= mn]


def connect(root: Path, cfg: dict) -> sqlite3.Connection:
    db = root / cfg["index"]["db"]
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(db)
    c.executescript("""
    create table if not exists files(path text primary key, sha text, title text, status text, superseded_by text, summary text);
    create virtual table if not exists t using fts5(title, head, body, path unindexed, tokenize='unicode61 remove_diacritics 2');
    create table if not exists links(a text, b text);
    create index if not exists links_a on links(a);
    create table if not exists ent(doc text, entity text, label text, n integer);
    create index if not exists ent_doc on ent(doc); create index if not exists ent_e on ent(entity);
    create table if not exists emb(cid integer primary key, h text, vec blob);
    create table if not exists meta(k text primary key, v text);
    """)
    return c


# ---------- build ----------
def cmd_build(root: Path, cfg: dict):
    t0 = time.time()
    c = connect(root, cfg)
    known = {p: s for p, s in c.execute("select path, sha from files")}
    cap, mn = cfg["index"]["max_chunk_chars"], cfg["index"]["min_chunk_chars"]
    seen, changed, texts = set(), 0, {}
    for rel in walk(root, cfg):
        seen.add(rel)
        try:
            raw = (root / rel).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if len(raw) > 600_000:
            continue
        texts[rel] = raw
        sha = hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()
        if known.get(rel) == sha:
            continue
        changed += 1
        fm, body = parse_doc(raw)
        mt = re.search(r"^#\s+(.+)$", body, re.M)
        base = fm.get("title") or (mt.group(1).strip() if mt else Path(rel).stem)
        search_title = base + " " + Path(rel).stem   # Dateinamen-Stamm durchsuchbar (ADR-Nummern, Identifier)
        c.execute("delete from t where path=?", (rel,))
        c.execute("delete from emb where cid not in (select rowid from t)")
        desc = fm.get("description", "")
        chs = chunk_text(body, cap, mn) or [(base, base + (" " + body.strip() if body.strip() else ""))]  # Kurzdatei bleibt über den Titel auffindbar
        for head, ch in chs:
            c.execute("insert into t(title, head, body, path) values (?,?,?,?)",
                      (search_title + (" " + desc if desc else ""), head, ch, rel))
        c.execute("insert or replace into files values (?,?,?,?,?,?)",
                  (rel, sha, base, fm.get("status", ""), fm.get("superseded_by", ""), desc))
    gone = [p for p in known if p not in seen]
    for p in gone:
        c.execute("delete from t where path=?", (p,)); c.execute("delete from files where path=?", (p,))
    # Link-Graph: deterministisch aus Dateinamen, Wikilinks, Markdown-Links und ADR-Nummern
    c.execute("delete from links")
    if cfg["graph"]["use_links"]:
        base = defaultdict(list)
        for p in seen:
            base[os.path.basename(p)].append(p)
        adr = {}
        for p in seen:
            m = re.search(r"ADR-0?(\d+)", os.path.basename(p))
            if m and "/ADR/" in p:
                adr[int(m.group(1))] = p
        edges = set()
        for p, t in texts.items():
            refs = set()
            for m in re.finditer(r"\[\[([^\]|#]+)", t):
                x = os.path.basename(m.group(1).strip()); refs.add(x if x.endswith(".md") else x + ".md")
            for m in re.finditer(r"\]\(([^)#\s]+\.md)", t):
                refs.add(os.path.basename(m.group(1)))
            for m in re.finditer(r"[\w\-]+\.md\b", t):
                refs.add(m.group(0))
            tg = set()
            for r in refs:
                cand = base.get(r, [])
                if 0 < len(cand) <= 2:
                    tg.update(cand)
            for m in re.finditer(r"ADR-0?(\d+)", t):
                if int(m.group(1)) in adr:
                    tg.add(adr[int(m.group(1))])
            tg.discard(p)
            for x in tg:
                edges.add((p, x)); edges.add((x, p))
        c.executemany("insert into links values (?,?)", list(edges))
    # Entitäten aus Graphify (doc -> concept)
    c.execute("delete from ent")
    gfile = root / cfg["graph"]["graphify_json"]
    nent = 0
    if cfg["graph"]["use_graphify"] and gfile.exists():
        g = json.loads(gfile.read_text(encoding="utf-8"))
        nodes = {n["id"]: n for n in g.get("nodes", [])}
        pairs = defaultdict(set)
        for e in g.get("links", g.get("edges", [])):
            a, b = nodes.get(e.get("source")), nodes.get(e.get("target"))
            if not a or not b:
                continue
            if a.get("file_type") == "concept" and b.get("file_type") == "document":
                a, b = b, a  # Graphify speichert ungerichtet, die Richtung kann vertauscht sein
            if a.get("file_type") == "document" and b.get("file_type") == "concept" and a.get("source_file") in seen:
                pairs[b["id"]].add((a["source_file"], b.get("label", "")))
        mx = cfg["graph"]["entity_max_docs"]
        for eid, ds in pairs.items():
            if 2 <= len(ds) <= mx:
                for d, lab in ds:
                    c.execute("insert into ent values (?,?,?,?)", (d, eid, lab, len(ds))); nent += 1
    c.execute("insert or replace into meta values ('built', ?)", (time.strftime("%Y-%m-%dT%H:%M:%S"),))
    c.commit()
    n_chunks = c.execute("select count(*) from t").fetchone()[0]
    n_links = c.execute("select count(*) from links").fetchone()[0] // 2
    print(f"Index: {len(seen)} Dateien ({changed} neu/geändert, {len(gone)} entfernt), {n_chunks} Abschnitte, "
          f"{n_links} Link-Kanten, {nent} Entitäts-Zuordnungen, {time.time()-t0:.1f}s")


# ---------- Suche ----------
def tokens(q: str) -> list[str]:
    return [t for t in re.findall(r"\w+", q.lower()) if len(t) > 2 and t not in STOP]


def fts_query(q: str, stem: bool) -> str | None:
    parts = []
    for t in tokens(q):
        parts.append(f'"{t[:-2]}"*' if stem and len(t) >= 7 else f'"{t}"')
    return " OR ".join(parts) or None


def file_scores(lists: list[list[int]], cpath: dict, k: int) -> dict:
    sc = defaultdict(float)
    for lst in lists:
        best = {}
        for r, cid in enumerate(lst):
            best.setdefault(cpath[cid], r)
        for p, r in best.items():
            sc[p] += 1 / (k + r + 1)
    return sc


def embed_texts(cfg, texts: list[str]) -> list[list[float]]:
    e = cfg["embedding"]
    req = urllib.request.Request(e["url"] + "/api/embed", json.dumps({"model": e["model"], "input": texts}).encode(),
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=300))["embeddings"]


def dense_list(c, cfg, q: str, n=60) -> list[int]:
    import numpy as np
    rows = c.execute("select cid, vec from emb").fetchall()
    if not rows:
        return []
    ids = [r[0] for r in rows]
    M = np.frombuffer(b"".join(r[1] for r in rows), dtype="float32").reshape(len(rows), -1)
    v = np.array(embed_texts(cfg, [q])[0], dtype="float32"); v /= np.linalg.norm(v)
    return [ids[i] for i in np.argsort(-(M @ v))[:n]]


def decide(cfg, q: str, cands: list[tuple[str, str]]) -> list[float]:
    d = cfg["decision"]
    lines = "\n".join(f"[{i}] {h}: {s[:d['chars']]}" for i, (h, s) in enumerate(cands))
    schema = {"type": "object", "properties": {"scores": {"type": "array", "items": {"type": "object",
              "properties": {"index": {"type": "integer"}, "score": {"type": "number"}}, "required": ["index", "score"]}}},
              "required": ["scores"]}
    payload = {"model": d["model"], "stream": False, "think": False, "format": schema, "options": {"temperature": 0},
               "messages": [{"role": "system", "content": "You are a relevance judge for a search system. Return one score "
                             "between 0.0 and 1.0 per numbered passage, judged only from the passage content."},
                            {"role": "user", "content": f"Query: {q}\n\nPassages:\n{lines}"}]}
    req = urllib.request.Request(d["url"] + "/api/chat", json.dumps(payload).encode(), {"Content-Type": "application/json"})
    res = json.loads(json.load(urllib.request.urlopen(req, timeout=60))["message"]["content"])
    out = [0.0] * len(cands)
    for s in res["scores"]:
        if 0 <= s["index"] < len(cands):
            out[s["index"]] = max(0.0, min(1.0, float(s["score"])))
    return out


def decide_systemone(cfg, q: str, cands: list[tuple[str, str]]) -> list[float]:
    """LAYA-Vertrag (docs: laya-serve): POST /v1/systemone, Frage vom Typ noul je Fundstelle."""
    d = cfg["decision"]
    headers = {"Content-Type": "application/json"}
    tok = os.environ.get(d["token_env"], "")
    if tok:
        headers["Authorization"] = "Bearer " + tok
    out = []
    for head, text in cands:
        body = {"state": {"question": q, "passage": f"{head}: {text[:d['chars']]}"},
                "questions": {"relevant": {"type": "noul", "instructions": "Does the passage contain the answer to the question? Answer true only if the passage itself states the answer."}}}
        if d["model"]:
            body["model"] = d["model"]  # Ollama (/v1/systemone) verlangt das Modell, laya-serve nicht
        req = urllib.request.Request(d["url"].rstrip("/") + "/v1/systemone", json.dumps(body).encode(), headers)
        res = json.load(urllib.request.urlopen(req, timeout=30))
        out.append(max(0.0, min(1.0, float(res["answers"]["relevant"]["noul"]))))
    return out


def search(c, cfg, q: str, k=5, *, graph=True, dense=None, filename=True, decision=None) -> dict:
    r = cfg["rank"]
    dense = cfg["embedding"]["enabled"] if dense is None else dense
    decision = cfg["decision"]["enabled"] if decision is None else decision
    cpath = {cid: p for cid, p in c.execute("select rowid, path from t")}
    lists, why = [], defaultdict(list)
    fq = fts_query(q, r["stem_prefix"])
    bm = []
    bm25_top = None
    if fq:
        bm_rows = c.execute("select rowid, bm25(t, 6.0, 3.0, 1.0) from t where t match ? "
                            "order by bm25(t, 6.0, 3.0, 1.0) limit 60", (fq,)).fetchall()
        bm = [x[0] for x in bm_rows]
        bm25_top = bm_rows[0][1] if bm_rows else None
    lists.append(bm)
    if dense:
        try:
            dl = dense_list(c, cfg, q)
            if dl:
                lists.append(dl)
        except Exception as e:  # Ollama weg: BM25 trägt weiter
            why["_warn"].append(f"Embedding aus: {str(e)[:60]}")
    sc = file_scores(lists, cpath, r["rrf_k"])
    best_chunk = {}
    best_chunks = {}
    for lst in lists:
        for cid in lst:
            p = cpath[cid]
            best_chunk.setdefault(p, cid)
            if p not in best_chunks:
                best_chunks[p] = []
            if cid not in best_chunks[p] and len(best_chunks[p]) < 3:
                best_chunks[p].append(cid)
    for p in sc:
        why[p].append("Text")
    if filename:
        tk = tokens(q)
        for p in list(sc):
            hit = sum(1 for t in tk if t in os.path.basename(p).lower())
            if hit:
                sc[p] += r["filename_boost"] * hit; why[p].append("Dateiname")
    if graph:
        top = sorted(sc.items(), key=lambda x: -x[1])[: r["graph_top"]]
        add = defaultdict(float)
        for p, s in top:
            for (b,) in c.execute("select b from links where a=?", (p,)):
                add[b] += r["graph_weight"] * s; why[b].append(f"verlinkt mit {os.path.basename(p)}")
            for ent, lab, n in c.execute("select entity, label, n from ent where doc=?", (p,)):
                wgt = 1 / math.log(2 + n)
                for (d2,) in c.execute("select doc from ent where entity=? and doc!=?", (ent, p)):
                    add[d2] += r["graph_weight"] * s * wgt; why[d2].append(f"teilt '{lab}'")
        for b, a in add.items():
            sc[b] = sc.get(b, 0) + a
    meta = {p: (t, st, sb, sm) for p, t, st, sb, sm in c.execute("select path, title, status, superseded_by, summary from files")}
    for p in list(sc):
        if p in meta and (meta[p][2] or meta[p][1].lower() == "superseded"):
            sc[p] *= r["superseded_factor"]
    reg = cfg.get("_authority") or {}
    if reg:
        sbb = reg.get("superseded_by", {})
        for old, new in sbb.items():
            if old in sc and new in meta:
                sc[new] = max(sc.get(new, 0.0), sc[old] * 1.05)
                why[new].append(f"kanonisch (löst {os.path.basename(old)} ab)")
                if new not in best_chunks:
                    vals = reg.get("meta", {}).get(new, {}).get("value") or []
                    if vals:
                        picked = [cid for (cid, bd) in c.execute("select rowid, body from t where path=?", (new,))
                                  if any(v in bd for v in vals)]
                        if picked:
                            best_chunks[new] = picked[:3]
                    if new not in best_chunks and fq:
                        for (cid,) in c.execute("select rowid from t where path=? and t match ? "
                                                "order by bm25(t, 6.0, 3.0, 1.0) limit 3", (new, fq)):
                            best_chunks.setdefault(new, []).append(cid)
            if old in sc:
                sc[old] *= r["superseded_factor"]
                why[old].append(f"überholt durch {os.path.basename(new)}")
        # Register als Thema→kanonisch-Karte: Trifft die Frage ein Register-Thema, die kanonische Datei hochziehen
        qtoks = tokens(q)
        for canon, m in reg.get("meta", {}).items():
            alias = (m.get("alias") or "").lower()
            if canon in meta and any(t in alias for t in qtoks):
                sc[canon] = max(sc.get(canon, 0.0), 0.015)   # nur einordnen, starkes BM25 nicht verdrängen
                why[canon].append("kanonisch (Thema im Register)")
                if canon not in best_chunks:
                    vals = m.get("value") or []
                    if vals:
                        picked = [cid for (cid, bd) in c.execute("select rowid, body from t where path=?", (canon,))
                                  if any(v in bd for v in vals)]
                        if picked:
                            best_chunks[canon] = picked[:3]
                    if canon not in best_chunks and fq:
                        for (cid,) in c.execute("select rowid from t where path=? and t match ? "
                                                "order by bm25(t, 6.0, 3.0, 1.0) limit 3", (canon, fq)):
                            best_chunks.setdefault(canon, []).append(cid)
    ranked = sorted(sc.items(), key=lambda x: -x[1])
    note = None
    if decision and (cfg["decision"]["backend"] == "systemone" or cfg["decision"]["model"]) and ranked:
        kk = cfg["decision"]["top_k"]
        head = ranked[:kk]
        cands = []
        for p, _ in head:
            cid = best_chunk.get(p)
            row = c.execute("select head, body from t where rowid=?", (cid,)).fetchone() if cid else None
            if not row:
                row = c.execute("select head, body from t where path=? limit 1", (p,)).fetchone() or ("", "")
            cands.append((p + " / " + row[0], row[1]))
        try:
            ds = (decide_systemone if cfg["decision"]["backend"] == "systemone" else decide)(cfg, q, cands)
            order_d = sorted(range(len(head)), key=lambda i: -ds[i])
            rr = {i: 1 / (r["rrf_k"] + o + 1) for o, i in enumerate(order_d)}
            merged = sorted(range(len(head)), key=lambda i: -(1 / (r["rrf_k"] + i + 1) + rr[i]))
            ranked = [head[i] for i in merged] + ranked[kk:]
            note = "Decision-Modell angewendet"
        except Exception as e:
            note = f"Decision-Modell Rückfall: {str(e)[:60]}"
    out = []
    for p, s in ranked[:k]:
        rows = []
        for cid in best_chunks.get(p, []):
            row = c.execute("select head, body from t where rowid=?", (cid,)).fetchone()
            if row:
                rows.append(row)
        if not rows:
            rows = [c.execute("select head, body from t where path=? order by rowid limit 1", (p,)).fetchone() or ("", "")]
        pr = cfg["privacy"]["mask_secrets"]
        passages = []
        for head, body in rows:
            body = re.sub(r"\s+", " ", body).strip()
            passages.append({"heading": head, "body": mask(body) if pr else body})
        snippet = passages[0]["body"][:260]
        rm = reg.get("meta", {}).get(p, {}) if reg else {}
        today = time.strftime("%Y-%m-%d")
        stale = bool(rm.get("stale_after")) and rm["stale_after"] < today
        unverified = bool(rm) and (not rm.get("confirmed") or rm.get("status") in ("proposed", "draft"))
        sup_by = reg.get("superseded_by", {}).get(p) or meta.get(p, ("", "", ""))[2]
        out.append({"path": p, "score": round(s, 5), "title": meta.get(p, ("",))[0], "heading": passages[0]["heading"],
                    "snippet": snippet, "passages": passages,
                    "why": list(dict.fromkeys(why[p]))[:4],
                    "superseded_by": sup_by or None,
                    "canonical": bool(rm.get("authority") == "canonical"),
                    "stale": stale, "unverified": unverified})
    # --- Antwort-Tor (P0-4, modellfrei): vier Antwortstatus + Signale ---
    toks = tokens(q)
    matched = set()
    for t in toks:
        fq_t = f'"{t[:-2]}"*' if (r["stem_prefix"] and len(t) >= 7) else f'"{t}"'
        try:
            if c.execute("select 1 from t where t match ? limit 1", (fq_t,)).fetchone():
                matched.add(t)
        except Exception:
            pass
    unmatched = [t for t in toks if t not in matched]
    top1_missing = []
    if out:
        t1 = " ".join([out[0]["title"], out[0]["heading"]] +
                      [p["heading"] + " " + p["body"] for p in out[0]["passages"]]).lower()
        top1_missing = [t for t in toks if t in matched and t not in t1]
    if not ranked:
        answer_status = "nicht_belegt"
    elif any(h.get("superseded_by") for h in out):
        answer_status = "widersprüchlich"
    elif out and out[0].get("unverified"):
        answer_status = "belegt_gueltigkeit_unbestaetigt"
    else:
        answer_status = "belegt"
    if unmatched:
        why["_warn"].append("Begriffe ohne Treffer im Repository: " + ", ".join(unmatched))
    if top1_missing:
        why["_warn"].append("Begriffe nicht im Top-1-Ergebnis: " + ", ".join(top1_missing))
    return {"results": out, "note": note, "warnings": why.get("_warn", []),
            "answer_status": answer_status, "unmatched_terms": unmatched,
            "top1_missing_terms": top1_missing, "bm25_top": bm25_top}


def cmd_search(root, cfg, a):
    c = connect(root, cfg)
    t0 = time.time()
    res = search(c, cfg, a.query, a.k)
    dt = (time.time() - t0) * 1000
    if a.json:
        print(json.dumps({**res, "ms": round(dt)}, ensure_ascii=False, indent=1)); return
    for i, h in enumerate(res["results"], 1):
        flags = []
        if h.get("superseded_by"):
            flags.append(f"überholt durch {h['superseded_by']}")
        if h.get("canonical"):
            flags.append("kanonisch")
        if h.get("stale"):
            flags.append("veraltet")
        if h.get("unverified"):
            flags.append("Gültigkeit nicht bestätigt")
        flag = f"  [{' | '.join(flags)}]" if flags else ""
        print(f"{i}. {h['path']}{flag}\n   {h['title']} > {h['heading']}\n   {h['snippet']}\n   ({', '.join(h['why'])})")
    for w in res["warnings"] + ([res["note"]] if res["note"] else []):
        print("Hinweis:", w)
    extra = f" (bm25_top {res['bm25_top']:.2f})" if res.get("bm25_top") is not None else ""
    print(f"Antwortstatus: {res.get('answer_status')}{extra}")
    print(f"{dt:.0f} ms")


# ---------- Embedding (optional) ----------
def cmd_embed(root, cfg):
    import numpy as np
    c = connect(root, cfg)
    rows = c.execute("select rowid, title, head, body from t").fetchall()
    have = {h for (h,) in c.execute("select h from emb")}
    todo = []
    for cid, t, h, b in rows:
        txt = (t + " | " + h + "\n" + b)[:900]
        hh = hashlib.sha1(txt.encode()).hexdigest()
        if hh not in have:
            todo.append((cid, hh, txt))
    t0 = time.time()
    for i in range(0, len(todo), 32):
        batch = todo[i:i + 32]
        vs = np.array(embed_texts(cfg, [x[2] for x in batch]), dtype="float32")
        vs /= np.linalg.norm(vs, axis=1, keepdims=True)
        for (cid, hh, _), v in zip(batch, vs):
            c.execute("insert or replace into emb values (?,?,?)", (cid, hh, v.tobytes()))
        c.commit()
    c.execute("delete from emb where cid not in (select rowid from t)")
    c.commit()
    print(f"Vektoren: {len(todo)} neu, {len(rows)} gesamt, {time.time()-t0:.0f}s, Modell {cfg['embedding']['model']}")


# ---------- Messung ----------
def cmd_eval(root, cfg, a):
    c = connect(root, cfg)
    gold = [json.loads(l) for l in Path(a.golden).read_text(encoding="utf-8").splitlines() if l.strip()]
    variants = {"BM25": dict(graph=False, dense=False, filename=False, decision=False),
                "BM25 + Dateiname": dict(graph=False, dense=False, filename=True, decision=False),
                "BM25 + Dateiname + Graph": dict(graph=True, dense=False, filename=True, decision=False)}
    has_emb = c.execute("select count(*) from emb").fetchone()[0] > 0
    if has_emb:
        variants["+ Embedding"] = dict(graph=True, dense=True, filename=True, decision=False)
    if cfg["decision"]["model"] or cfg["decision"]["backend"] == "systemone":
        variants["+ Decision-Modell"] = dict(graph=True, dense=has_emb, filename=True, decision=True)
    if not a.variants:
        variants = {"Konfiguration": dict()}
    for name, kw in variants.items():
        ranks, lat = [], []
        for g in gold:
            t0 = time.time()
            res = search(c, cfg, g["q"], 10, **kw)
            lat.append(time.time() - t0)
            exp = set(g["expect"])
            rk = next((i + 1 for i, h in enumerate(res["results"]) if h["path"] in exp), None)
            ranks.append(rk)
        n = len(ranks)
        rec = lambda k: sum(1 for x in ranks if x and x <= k) / n
        mrr = sum(1 / x for x in ranks if x) / n
        print(f"{name:28s} R@1 {rec(1):.2f} R@3 {rec(3):.2f} R@5 {rec(5):.2f} R@10 {rec(10):.2f} MRR {mrr:.3f} "
              f"p50 {sorted(lat)[n//2]*1000:.0f}ms p95 {sorted(lat)[int(n*0.95)-1]*1000:.0f}ms (n={n})")
        if a.misses:
            for g, x in zip(gold, ranks):
                if not x:
                    print("   verfehlt:", g["q"][:90])


def cmd_status(root, cfg):
    c = connect(root, cfg)
    q = lambda s: c.execute(s).fetchone()[0]
    built = c.execute("select v from meta where k='built'").fetchone()
    print(f"Dateien {q('select count(*) from files')}, Abschnitte {q('select count(*) from t')}, "
          f"Link-Kanten {q('select count(*) from links')//2}, Entitäts-Zuordnungen {q('select count(*) from ent')}, "
          f"Vektoren {q('select count(*) from emb')}, Stand {built[0] if built else '-'}")
    print("Embedding:", "an" if cfg["embedding"]["enabled"] else "aus", "| Decision-Modell:",
          cfg["decision"]["model"] if cfg["decision"]["enabled"] else "aus")


def cmd_manifest(root: Path, cfg: dict, a):
    """Coverage-Report: Was ist auf der Platte, was ist indexiert, was ist warum ausgeschlossen.

    Schreibt `.wikitila/source_manifest.json` und druckt eine Kurzfassung. Scope = include_ext
    (Markdown laut Entscheidung 2026-11-14); alles andere wird als „nach Typ ausgeschlossen“ geführt.
    """
    from collections import Counter
    c = connect(root, cfg)
    indexed = [p for (p,) in c.execute("select path from files")]
    pats = load_ignore(root, cfg)
    exts = tuple(cfg["corpus"]["include_ext"])
    disk = Counter()
    indexed_ext = Counter(Path(p).suffix.lower() or "(none)" for p in indexed)
    excl_type = Counter()
    excl_ignore = Counter()
    oversized = 0
    for r, dirs, files in os.walk(root):
        rr = os.path.relpath(r, root).replace(os.sep, "/")
        rr = "" if rr == "." else rr
        dirs[:] = [d for d in dirs if not d.startswith(".git") and d != "node_modules"
                   and not ignored((rr + "/" + d).lstrip("/"), pats)]
        for n in files:
            rel = (rr + "/" + n).lstrip("/")
            ext = Path(n).suffix.lower() or "(none)"
            if ignored(rel, pats):
                excl_ignore[ext] += 1
                continue
            disk[ext] += 1
            if not n.endswith(exts):
                excl_type[ext] += 1
            elif (root / rel).stat().st_size > 600_000:
                oversized += 1
    total_disk = sum(disk.values())
    manifest = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "root": str(root),
        "scope_include_ext": list(exts),
        "totals": {
            "on_disk": total_disk,
            "indexed": len(indexed),
            "in_scope_on_disk": sum(v for e, v in disk.items() if e in exts),
            "excluded_type": sum(excl_type.values()),
            "excluded_ignore": sum(excl_ignore.values()),
            "oversized_skipped": oversized,
        },
        "indexed_by_ext": dict(sorted(indexed_ext.items())),
        "excluded_type_by_ext": dict(sorted(excl_type.items())),
        "excluded_ignore_by_ext": dict(sorted(excl_ignore.items())),
    }
    mf = (root / cfg["index"]["db"]).parent / "source_manifest.json"
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Source-Manifest: {total_disk} Dateien auf Disk, {len(indexed)} indexiert "
          f"({', '.join(exts)}), {sum(excl_type.values())} nach Typ ausgeschlossen, "
          f"{sum(excl_ignore.values())} ignoriert, {oversized} zu groß übersprungen")
    print("  Indexiert nach Typ:", ", ".join(f"{e} {n}" for e, n in sorted(indexed_ext.items())))
    print("  Ausgeschlossen (Top):", ", ".join(f"{e} {n}" for e, n in excl_type.most_common(8)))
    print(f"  Manifest: {mf}")


def cmd_check(root: Path, cfg: dict, a) -> bool:
    """Index-/Quellstand-Abgleich (P0-5): meldet Drift zwischen Index und Disk, ohne zu bauen.

    Rückgabe: True bei Drift (neu/geändert/entfernt), False wenn Index aktuell ist.
    """
    c = connect(root, cfg)
    known = {p: s for p, s in c.execute("select path, sha from files")}
    seen = {}
    for rel in walk(root, cfg):
        try:
            raw = (root / rel).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if len(raw) > 600_000:
            continue
        seen[rel] = hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()
    new_changed = [p for p, s in seen.items() if known.get(p) != s]
    removed = [p for p in known if p not in seen]
    drift = bool(new_changed or removed)
    print(f"Quellstand: {len(seen)} Dateien im Scope, Index: {len(known)} Dateien, "
          f"{len(new_changed)} neu/geändert, {len(removed)} entfernt")
    if drift:
        print("  Drift erkannt — `wikitila.py --root . build` ausführen.")
        for p in new_changed[:8]:
            print(f"    neu/geändert: {p}")
        for p in removed[:8]:
            print(f"    entfernt: {p}")
    else:
        print("  OK — Index stimmt mit dem Quellstand überein (kein Drift).")
    return drift


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.environ.get("WIKITILA_ROOT", "."))
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("build"); sp.add_parser("embed"); sp.add_parser("status"); sp.add_parser("manifest"); sp.add_parser("check")
    s = sp.add_parser("search"); s.add_argument("query"); s.add_argument("-k", type=int, default=5); s.add_argument("--json", action="store_true")
    e = sp.add_parser("eval"); e.add_argument("golden"); e.add_argument("--variants", action="store_true"); e.add_argument("--misses", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    cfg = load_cfg(root)
    {"build": lambda: cmd_build(root, cfg), "embed": lambda: cmd_embed(root, cfg), "status": lambda: cmd_status(root, cfg),
     "manifest": lambda: cmd_manifest(root, cfg, a), "check": lambda: cmd_check(root, cfg, a),
     "search": lambda: cmd_search(root, cfg, a), "eval": lambda: cmd_eval(root, cfg, a)}[a.cmd]()


if __name__ == "__main__":
    main()
