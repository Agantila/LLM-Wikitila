#!/usr/bin/env python3
"""LLM-Wikitila: schlanke Suche über einen Markdown-Ordner.

Nur Standardbibliothek (numpy nur, wenn das optionale Embedding an ist).
Eine SQLite-Datei: FTS5 (BM25), Link-Graph, Entitäten aus Graphify, optionale Vektoren.

  wikitila.py build   [--root DIR]           Index aufbauen oder aktualisieren (inkrementell)
  wikitila.py search  "Frage" [-k 5] [--json]
  wikitila.py coverage "Frage" [--json]      Coverage-Note (Antwortabdeckung, ohne Ranking)
  wikitila.py eval    golden.jsonl [--variants]   Messung gegen ein Golden Set
  wikitila.py lint    [datei | --all] [--json]   Schreibseite prüfen (Frontmatter-Konvention)
  wikitila.py embed                          optional: Vektoren mit einem Ollama-Modell
  wikitila.py status | manifest | check       Indexzustand, Source-Manifest, Index-/Quellstand-Abgleich

Konfiguration: <root>/wikitila.toml (siehe config.example.toml).
"""
from __future__ import annotations

import argparse, contextlib, fnmatch, hashlib, json, math, os, re, sys, time, urllib.error, urllib.request
from collections import defaultdict
from pathlib import Path

try:
    import sqlite3
except ImportError:  # Python ohne _sqlite3 (z. B. selbst gebautes pyenv) — main meldet das verständlich
    sqlite3 = None

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

__version__ = "0.3.0"
MAX_FILE_BYTES = 600_000   # Dateien darüber werden übersprungen (Bytes, in build/check/manifest gleich)
# Indexformat (ADR-006): erhöhen, sobald sich ändert, was build aus einer unveränderten Datei
# erzeugt (Parsing, Chunking, Felder). Ein abweichender Wert erzwingt beim nächsten build einen Vollneubau.
INDEX_FORMAT = "3"
FM_RE = re.compile(r"---[ \t]*\n(?:(.*?)\n)??---[ \t]*(?:\n|\Z)", re.S)   # Frontmatter-Block (auch leer, auch am Dateiende)
FM_KEY_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_\-]*):\s*(.*)$")


class WikitilaError(Exception):
    """Bedienfehler mit verständlicher Meldung (main gibt sie ohne Traceback aus, Exit-Code 2)."""


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
    "lint": {"require": ["title", "description"],
             "status_values": ["draft", "stable", "deprecated", "superseded"],   # superseded wertet der Index ab
             "exclude": ["index.md", "log.md", "README.md", "CHANGELOG.md",
                         "CLAUDE.md", "AGENTS.md", "MASTER.md", "copy_*", "*template*"],
             "since": ""},
}

STOP = set("""der die das den dem des ein eine einen einem einer und oder ist sind wird werden wie was wer wo welche welcher
welches wir ich mit ohne für bei auf in im zu zum zur von vom aus nach vor über unter auch nicht nur noch dass damit muss
müssen soll sollen kann können hat haben wofür worauf wann warum nutzen nutzt aktuell gelten gilt gibt geben the and for with what how which""".split())

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
    out = {"superseded_by": {}, "supersedes": {}, "meta": {}, "warnings": []}
    if not cfg.get("authority", {}).get("enabled", True):
        return out
    rel = str((cfg.get("authority", {}) or {}).get("register", "") or "").strip()
    candidates = [root / rel] if rel else []
    candidates.append(root / "authority_register.json")
    path = next((p for p in candidates if p.is_file()), None)
    if not path:
        return out
    warn = out["warnings"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        warn.append(f"Authority-Register unlesbar ({path.name}: {str(e)[:80]}) — Register wird ignoriert, "
                    "kanonisch/überholt-Markierungen fehlen")
        return out
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        warn.append(f"Authority-Register ungültig ({path.name}: erwartet Objekt mit Liste 'entries') — Register wird ignoriert")
        return out
    s = lambda v: v if isinstance(v, str) else ""
    for i, e in enumerate(entries):
        if not isinstance(e, dict) or not isinstance(e.get("canonical"), str) or not e["canonical"].strip():
            warn.append(f"Authority-Register: Eintrag {i} übersprungen (kein Objekt oder 'canonical' fehlt)")
            continue
        canon = e["canonical"].strip()
        stale = e.get("stale_after")
        if stale is not None and not (isinstance(stale, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", stale)):
            warn.append(f"Authority-Register: '{e.get('id') or canon}' stale_after ungültig (erwartet JJJJ-MM-TT) — ignoriert")
            stale = None
        vals = e.get("value") or []
        vals = [vals] if isinstance(vals, str) else [v for v in vals if isinstance(v, str)] if isinstance(vals, list) else []
        out["meta"][canon] = {
            "authority": e.get("authority"),
            "stale_after": stale,
            "status": e.get("status"),
            "verified_at": e.get("verified_at"),
            "confirmed": e.get("authority_confirmed") is True,
            "value": vals,
            "alias": " ".join([s(e.get("id")), s(e.get("scope")), s(e.get("note"))]),
        }
        sup = e.get("supersedes") or []
        if not isinstance(sup, list):
            warn.append(f"Authority-Register: '{e.get('id') or canon}' supersedes ist keine Liste — ignoriert")
            sup = []
        for old in sup:
            if isinstance(old, str) and old and old != canon:
                out["superseded_by"][old] = canon
                out["supersedes"].setdefault(canon, []).append(old)
    return out


def _typ_ok(default, v) -> bool:
    """Wert passt zum Typ des Defaults (bool ist kein int, ganze Zahl bleibt ganz, Listen enthalten Text)."""
    if isinstance(default, bool):
        return isinstance(v, bool)
    if isinstance(default, int):
        return isinstance(v, int) and not isinstance(v, bool) and v >= 0
    if isinstance(default, float):
        return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0
    if isinstance(default, list):
        return isinstance(v, list) and all(isinstance(x, str) for x in v)
    if isinstance(default, str):
        return isinstance(v, str)
    return True


def check_cfg(over: dict, src: Path) -> None:
    """Prüft wikitila.toml gegen DEFAULTS: falsche Typen sind Bedienfehler, Unbekanntes nur eine Warnung."""
    typ = {bool: "true/false", int: "ganze Zahl ≥ 0", float: "Zahl ≥ 0", list: "Liste von Texten", str: "Text"}
    for sec, val in over.items():
        if sec not in DEFAULTS:
            print(f"Warnung: {src}: unbekannte Sektion [{sec}] wird ignoriert", file=sys.stderr)
            continue
        if not isinstance(val, dict):
            raise WikitilaError(f"Konfiguration fehlerhaft: {src}: [{sec}] muss eine Sektion sein, nicht {type(val).__name__}")
        for key, v in val.items():
            if key not in DEFAULTS[sec]:
                print(f"Warnung: {src}: unbekannter Schlüssel {sec}.{key} wird ignoriert", file=sys.stderr)
                continue
            d = DEFAULTS[sec][key]
            if not _typ_ok(d, v):
                raise WikitilaError(f"Konfiguration fehlerhaft: {src}: {sec}.{key} = {v!r} — erwartet "
                                    f"{typ.get(type(d), type(d).__name__)}")
    if over.get("index", {}).get("max_chunk_chars", 1) < 1:
        raise WikitilaError(f"Konfiguration fehlerhaft: {src}: index.max_chunk_chars muss ≥ 1 sein")


def load_cfg(root: Path) -> dict:
    env = os.environ.get("WIKITILA_CONFIG")
    p = Path(env) if env else root / "wikitila.toml"
    if env and not p.is_file():
        raise WikitilaError(f"WIKITILA_CONFIG zeigt auf keine Datei: {p}")
    over = {}
    if p.exists():
        if tomllib is None:
            print(f"Warnung: {p} wird ignoriert (Python < 3.11 hat kein tomllib)", file=sys.stderr)
        else:
            try:
                over = tomllib.loads(p.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
                raise WikitilaError(f"Konfiguration fehlerhaft: {p}: {e}")
            check_cfg(over, p)
    cfg = merge(DEFAULTS, over)
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


def inside_root(root: Path, rel: str) -> bool:
    """False, wenn rel ein Symlink ist, der aus dem Ordner herausführt (oder ins Leere zeigt)."""
    p = root / rel
    if not p.is_symlink():
        return True
    try:
        p.resolve(strict=True).relative_to(root.resolve())
        return True
    except (OSError, ValueError, RuntimeError):
        return False


def walk(root: Path, cfg: dict):
    """Dateien im Scope (include_ext, nicht ignoriert, nicht außerhalb des Ordners verlinkt)."""
    pats = load_ignore(root, cfg)
    exts = tuple(cfg["corpus"]["include_ext"])
    for r, dirs, files in os.walk(root):
        rr = os.path.relpath(r, root).replace(os.sep, "/")
        rr = "" if rr == "." else rr
        dirs[:] = [d for d in dirs if not d.startswith(".git") and d != "node_modules"
                   and not ignored((rr + "/" + d).lstrip("/"), pats)]
        for n in files:
            rel = (rr + "/" + n).lstrip("/")
            if n.endswith(exts) and not ignored(rel, pats) and inside_root(root, rel):
                yield rel


def read_source(root: Path, rel: str) -> str | None:
    """Liest eine Quelldatei; None bei Lesefehler oder über MAX_FILE_BYTES (vor dem Lesen geprüft)."""
    p = root / rel
    try:
        if p.stat().st_size > MAX_FILE_BYTES:
            return None
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


# ---------- Dokumente ----------
def frontmatter(text: str):
    """(Match oder None, Text ohne BOM). Gemeinsame Sicht von build und lint auf den Frontmatter-Block."""
    if text.startswith("\ufeff"):
        text = text[1:]
    return (FM_RE.match(text) if text.startswith("---") else None), text


def parse_doc(text: str) -> tuple[dict, str]:
    fm = {}
    m, text = frontmatter(text)
    if m:
        for line in (m.group(1) or "").splitlines():
            mm = FM_KEY_RE.match(line)
            if mm:
                fm[mm.group(1).lower()] = mm.group(2).strip().strip("\"'")
        text = text[m.end():]
    return fm, text


def chunk_text(body: str, cap: int, mn: int) -> list[tuple[str, str]]:
    out = []
    for sec in re.split(r"(?m)^(?=#{1,3}\s)", body):
        sec = sec.strip()
        # Kurze Abschnitte mit Überschrift und Inhalt behalten („## Schrift · Bai Jamjuree“);
        # nur Überschriften ohne Inhalt oder kurzer Text ohne Überschrift entfallen.
        if len(sec) < mn and ("\n" not in sec or not sec.startswith("#")):
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
    return [(h, c) for h, c in out if len(c.strip()) >= mn or (h and "\n" in c)]


def connect(root: Path, cfg: dict, create: bool = True) -> sqlite3.Connection:
    """Öffnet den Index. create=False: Fehler statt leerer Index, wenn die Datei fehlt (Lesebefehle)."""
    db = root / cfg["index"]["db"]
    if not create and not db.exists():
        raise WikitilaError(f"Kein Index unter {db} — zuerst `wikitila.py --root {root} build` ausführen.")
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(db, timeout=30)   # paralleler build/Hook: warten statt sofort „database is locked“
    try:
        _schema(c)
    except BaseException:
        c.close()
        raise
    return c


def _schema(c) -> None:
    c.executescript("""
    create table if not exists files(path text primary key, sha text, title text, status text, superseded_by text, summary text);
    create virtual table if not exists t using fts5(title, head, body, path unindexed, tokenize='unicode61 remove_diacritics 2');
    create table if not exists links(a text, b text);
    create index if not exists links_a on links(a);
    create table if not exists ent(doc text, entity text, label text, n integer);
    create index if not exists ent_doc on ent(doc); create index if not exists ent_e on ent(entity);
    create table if not exists emb(cid integer primary key, h text, vec blob);
    create table if not exists meta(k text primary key, v text);
    create table if not exists chunks(cid integer primary key, path text not null);
    create index if not exists chunks_path on chunks(path);
    """)
    # Migration (ADR-002): ältere Indizes ohne chunks-Tabelle einmalig nachziehen
    if c.execute("select v from meta where k='schema'").fetchone() is None:
        c.execute("delete from chunks")
        c.execute("insert into chunks(cid, path) select rowid, path from t")
        c.execute("insert or replace into meta values ('schema', '2')")
        c.commit()


def index_format(c) -> str | None:
    row = c.execute("select v from meta where k='format'").fetchone()
    return row[0] if row else None


def chunk_ids(c, path: str) -> list[int]:
    return [cid for (cid,) in c.execute("select cid from chunks where path=? order by cid", (path,))]


def delete_doc(c, path: str):
    ids = chunk_ids(c, path)
    for i in range(0, len(ids), 500):
        part = ids[i:i + 500]
        c.execute(f"delete from t where rowid in ({','.join('?' * len(part))})", part)
        c.execute(f"delete from emb where cid in ({','.join('?' * len(part))})", part)
    c.execute("delete from chunks where path=?", (path,))


def in_rows(c, sql: str, ids: list, extra: tuple = ()):
    """Führt sql mit einer IN-Liste in Portionen aus (SQLite-Parameterlimit). sql enthält {q} für die Platzhalter."""
    ids = list(ids)
    for i in range(0, len(ids), 500):
        part = ids[i:i + 500]
        yield from c.execute(sql.format(q=",".join("?" * len(part))), (*part, *extra))


# ---------- build ----------
def cmd_build(root: Path, cfg: dict):
    t0 = time.time()
    c = connect(root, cfg)
    known = {p: s for p, s in c.execute("select path, sha from files")}
    fmt = index_format(c)
    if fmt != INDEX_FORMAT:
        # ADR-006: Hash-Vergleich allein erkennt keine geänderte Verarbeitung — alles neu aufbauen.
        if known:
            had_emb = c.execute("select count(*) from emb").fetchone()[0] > 0
            print(f"Indexformat {fmt or 'alt'} → {INDEX_FORMAT}: Vollneubau"
                  + (" (Vektoren danach mit `embed` neu erzeugen)" if had_emb else ""), file=sys.stderr)
        for tbl in ("t", "chunks", "files", "emb", "links", "ent"):
            c.execute(f"delete from {tbl}")
        known = {}
    cap, mn = cfg["index"]["max_chunk_chars"], cfg["index"]["min_chunk_chars"]
    seen, changed, texts = set(), 0, {}
    for rel in walk(root, cfg):
        raw = read_source(root, rel)
        if raw is None:
            continue
        seen.add(rel)
        texts[rel] = raw
        sha = hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()
        if known.get(rel) == sha:
            continue
        changed += 1
        fm, body = parse_doc(raw)
        mt = re.search(r"^#\s+(.+)$", body, re.M)
        base = fm.get("title") or (mt.group(1).strip() if mt else Path(rel).stem)
        search_title = base + " " + Path(rel).stem   # Dateinamen-Stamm durchsuchbar (ADR-Nummern, Identifier)
        delete_doc(c, rel)
        desc = fm.get("description", "")
        # Frontmatter-Metadaten durchsuchbar machen: status (proposed/accepted/…) und
        # superseded_by tragen Antworten, die sonst nicht auffindbar wären („verbindlich beschlossen?“ -> „proposed“).
        fm_extra = " ".join(x for x in (fm.get("status", ""), fm.get("superseded_by", "")) if x)
        title_field = " ".join(x for x in (search_title, desc, fm_extra) if x)
        chs = chunk_text(body, cap, mn) or [(base, base + (" " + body.strip() if body.strip() else ""))]  # Kurzdatei bleibt über den Titel auffindbar
        for head, ch in chs:
            cur = c.execute("insert into t(title, head, body, path) values (?,?,?,?)",
                            (title_field, head, ch, rel))
            c.execute("insert into chunks(cid, path) values (?,?)", (cur.lastrowid, rel))
        c.execute("insert or replace into files values (?,?,?,?,?,?)",
                  (rel, sha, base, fm.get("status", ""), fm.get("superseded_by", ""), desc))
    gone = [p for p in known if p not in seen]
    for p in gone:
        delete_doc(c, p); c.execute("delete from files where path=?", (p,))
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
    g = None
    if cfg["graph"]["use_graphify"] and gfile.exists():
        try:
            g = json.loads(gfile.read_text(encoding="utf-8"))
            if not isinstance(g, dict):
                raise ValueError("kein JSON-Objekt")
        except (OSError, ValueError) as e:
            print(f"Warnung: {gfile} unlesbar ({str(e)[:80]}) — Index ohne Entitäten gebaut", file=sys.stderr)
            g = None
    if g is not None:
        nodes = {n["id"]: n for n in g.get("nodes", []) if isinstance(n, dict) and "id" in n}
        pairs = defaultdict(set)
        for e in g.get("links", g.get("edges", [])):
            if not isinstance(e, dict):
                continue
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
    c.execute("insert or replace into meta values ('format', ?)", (INDEX_FORMAT,))
    c.execute("insert or replace into meta values ('version', ?)", (__version__,))
    c.commit()
    n_chunks = c.execute("select count(*) from t").fetchone()[0]
    n_links = c.execute("select count(*) from links").fetchone()[0] // 2
    print(f"Index: {len(seen)} Dateien ({changed} neu/geändert, {len(gone)} entfernt), {n_chunks} Abschnitte, "
          f"{n_links} Link-Kanten, {nent} Entitäts-Zuordnungen, {time.time()-t0:.1f}s")
    c.close()


# ---------- Suche ----------
def tokens(q: str) -> list[str]:
    # Zahlen bleiben erhalten (Preise, Kennzahlen); einzelne Ziffern entfallen (Rauschen).
    return [t for t in re.findall(r"\w+", q.lower()) if t not in STOP and (len(t) > 2 or (len(t) == 2 and t.isdigit()))]


def fts_query(q: str, stem: bool) -> str | None:
    parts = []
    for t in tokens(q):
        parts.append(f'"{t[:-2]}"*' if stem and len(t) >= 7 else f'"{t}"')
    return " OR ".join(parts) or None


def file_scores(lists: list[list[int]], cpath: dict, k: int) -> dict:
    sc = defaultdict(float)
    for lst in lists:
        ranks: dict[str, list[int]] = defaultdict(list)
        for r, cid in enumerate(lst):
            p = cpath[cid]
            if len(ranks[p]) < 3:          # bis zu drei Chunks je Datei einfließen lassen
                ranks[p].append(r)
        for p, rs in ranks.items():
            sc[p] += sum(1 / (k + r + 1) for r in rs)
    return sc


def embed_texts(cfg, texts: list[str]) -> list[list[float]]:
    e = cfg["embedding"]
    req = urllib.request.Request(e["url"].rstrip("/") + "/api/embed",
                                 json.dumps({"model": e["model"], "input": texts}).encode(),
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            vecs = json.load(resp)["embeddings"]
    except (OSError, ValueError, KeyError, TypeError) as ex:   # URLError/HTTPError/Timeout sind OSError
        raise WikitilaError(f"Embedding-Dienst {e['url']} (Modell {e['model']}) nicht nutzbar: {str(ex)[:120]}")
    if not isinstance(vecs, list) or len(vecs) != len(texts):
        raise WikitilaError(f"Embedding-Dienst {e['url']} lieferte {len(vecs) if isinstance(vecs, list) else 0} "
                            f"statt {len(texts)} Vektoren")
    return vecs


def dense_list(c, cfg, q: str, n=60) -> list[int]:
    import numpy as np
    rows = c.execute("select cid, vec from emb").fetchall()
    if not rows:
        return []
    ids = [r[0] for r in rows]
    M = np.frombuffer(b"".join(r[1] for r in rows), dtype="float32").reshape(len(rows), -1)
    v = np.array(embed_texts(cfg, [q])[0], dtype="float32"); v /= (np.linalg.norm(v) or 1.0)
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


def _chunks_with_values(c, path: str, vals: list[str]) -> list[int]:
    """Chunks einer Datei, die Register-Werte enthalten (unmaskierter Body).

    Register-Werte sind oft Daten (Preise, Kennzahlen) und keine Query-Token — BM25
    hebt solche Chunks nicht hervor. Kompakt notierte Werte („549/899/1.199“) werden
    in Atome zerlegt und einzeln gesucht, damit ein Chunk mit „549 EUR“ gefunden wird.
    Rückgabe absteigend nach Anzahl getroffener Atome (bester Beleg zuerst).
    """
    if not vals:
        return []
    atoms = {a for v in vals for a in re.split(r"[\s/,;·|]+", v) if a}
    if not atoms:
        return []
    hits = []
    for cid, bd in in_rows(c, "select rowid, body from t where rowid in ({q})", chunk_ids(c, path)):
        n = sum(1 for a in atoms if a in bd)
        if n:
            hits.append((n, cid))
    hits.sort(key=lambda x: -x[0])
    return [cid for _, cid in hits]


def coverage_grade(c, cfg, q: str) -> dict:
    """Deterministische Coverage-Note (Analog zu Auto Ontologys `check_answerable`).

    Ein signifikanter Query-Token gilt als „gedeckt“, wenn er in mindestens einem
    Chunk zusammen mit einem anderen signifikanten Token vorkommt (Ko-Lokation).
    Nahe-am-Thema-Fragen („Safe Zones für Pinterest“) treffen die Begriffe nur
    verstreut — `uncovered` nennt den isolierten Begriff, `term_coverage` ist < 1.
    Kein Modell, nur FTS5.
    """
    r = cfg["rank"]
    toks = tokens(q)
    if not toks:
        return {"term_coverage": 1.0, "uncovered": [], "uncovered_hint": {}}
    chunks_of: dict[str, set[int]] = {}
    hint: dict[str, str] = {}
    for t in toks:
        fq_t = f'"{t[:-2]}"*' if (r["stem_prefix"] and len(t) >= 7) else f'"{t}"'
        try:
            ids = [cid for (cid,) in c.execute("select rowid from t where t match ? limit 60", (fq_t,)).fetchall()]
        except Exception:
            ids = []
        chunks_of[t] = set(ids)
        if ids:
            hint[t] = next((p for (p,) in c.execute("select path from chunks where cid=?", (ids[0],))), "")
    if len(toks) == 1:
        t = toks[0]
        return {"term_coverage": 1.0 if chunks_of[t] else 0.0,
                "uncovered": [] if chunks_of[t] else [t],
                "uncovered_hint": {t: hint.get(t, "")} if not chunks_of[t] else {}}
    covered, uncovered = [], []
    for t in toks:
        if any(chunks_of[t] & chunks_of[o] for o in toks if o != t):
            covered.append(t)
        else:
            uncovered.append(t)
    return {"term_coverage": round(len(covered) / len(toks), 3),
            "uncovered": uncovered,
            "uncovered_hint": {t: hint.get(t, "") for t in uncovered}}


def search(c, cfg, q: str, k=5, *, graph=True, dense=None, filename=True, decision=None) -> dict:
    r = cfg["rank"]
    dense = cfg["embedding"]["enabled"] if dense is None else dense
    decision = cfg["decision"]["enabled"] if decision is None else decision
    lists, why = [], defaultdict(list)
    reg = cfg.get("_authority") or {}
    why["_warn"].extend(reg.get("warnings", []))
    auth_events: list[str] = []   # für den Trace: welche Register-Regeln gezogen haben
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
    cand_ids = {cid for lst in lists for cid in lst}
    cpath = dict(in_rows(c, "select cid, path from chunks where cid in ({q})", cand_ids))
    lists = [[cid for cid in lst if cid in cpath] for lst in lists]
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
                    lab_out = mask(lab) if cfg["privacy"]["mask_secrets"] else lab   # F2: Entitäts-Labels aus dem Graph
                    add[d2] += r["graph_weight"] * s * wgt; why[d2].append(f"teilt '{lab_out}'")
        for b, a in add.items():
            sc[b] = sc.get(b, 0) + a
    need = set(sc) | set(reg.get("meta", {})) | set(reg.get("superseded_by", {})) | set(reg.get("superseded_by", {}).values())
    meta = {p: (t, st, sb, sm) for p, t, st, sb, sm in
            in_rows(c, "select path, title, status, superseded_by, summary from files where path in ({q})", need)}
    penalized = set()   # F11: Abwertungsfaktor höchstens einmal je Datei
    for p in list(sc):
        if p in meta and (meta[p][2] or meta[p][1].lower() == "superseded"):
            sc[p] *= r["superseded_factor"]; penalized.add(p)
    if reg:
        sbb = reg.get("superseded_by", {})
        for old, new in sbb.items():
            if old in sc and new in meta:
                sc[new] = max(sc.get(new, 0.0), sc[old] * 1.05)
                why[new].append(f"kanonisch (löst {os.path.basename(old)} ab)")
                auth_events.append(f"Register: {os.path.basename(new)} löst {os.path.basename(old)} ab")
                if new not in best_chunks:
                    vals = reg.get("meta", {}).get(new, {}).get("value") or []
                    if vals:
                        picked = [cid for (cid, bd) in in_rows(c, "select rowid, body from t where rowid in ({q})", chunk_ids(c, new))
                                  if any(v in bd for v in vals)]
                        if picked:
                            best_chunks[new] = picked[:3]
                    if new not in best_chunks and fq:
                        for (cid,) in c.execute("select rowid from t where t match ? and rowid in "
                                                "(select cid from chunks where path=?) order by bm25(t, 6.0, 3.0, 1.0) limit 3", (fq, new)):
                            best_chunks.setdefault(new, []).append(cid)
            if old in sc:
                if old not in penalized:
                    sc[old] *= r["superseded_factor"]; penalized.add(old)
                why[old].append(f"überholt durch {os.path.basename(new)}")
        # Register als Thema→kanonisch-Karte: Trifft die Frage ein Register-Thema, die kanonische Datei hochziehen
        qtoks = tokens(q)
        for canon, m in reg.get("meta", {}).items():
            alias = (m.get("alias") or "").lower()
            if canon in meta and any(t in alias for t in qtoks):
                sc[canon] = max(sc.get(canon, 0.0), 0.015)   # nur einordnen, starkes BM25 nicht verdrängen
                why[canon].append("kanonisch (Thema im Register)")
                auth_events.append(f"Register-Thema: {os.path.basename(canon)}")
                if canon not in best_chunks:
                    vals = m.get("value") or []
                    if vals:
                        picked = [cid for (cid, bd) in in_rows(c, "select rowid, body from t where rowid in ({q})", chunk_ids(c, canon))
                                  if any(v in bd for v in vals)]
                        if picked:
                            best_chunks[canon] = picked[:3]
                    if canon not in best_chunks and fq:
                        for (cid,) in c.execute("select rowid from t where t match ? and rowid in "
                                                "(select cid from chunks where path=?) order by bm25(t, 6.0, 3.0, 1.0) limit 3", (fq, canon)):
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
                ids = chunk_ids(c, p)[:1]
                row = (c.execute("select head, body from t where rowid=?", (ids[0],)).fetchone() if ids else None) or ("", "")
            cands.append((p + " / " + row[0], mask(row[1]) if cfg["privacy"]["mask_secrets"] else row[1]))
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
        rm = reg.get("meta", {}).get(p, {}) if reg else {}
        vals = rm.get("value") or []
        rows = []
        cids = _chunks_with_values(c, p, vals) if vals else []   # Wert-Chunks zuerst (Passagen-Präsenz)
        if not cids:
            cids = best_chunks.get(p, [])
        for cid in cids:
            row = c.execute("select head, body from t where rowid=?", (cid,)).fetchone()
            if row:
                rows.append(row)
        if not rows:
            ids = chunk_ids(c, p)[:1]
            rows = [(c.execute("select head, body from t where rowid=?", (ids[0],)).fetchone() if ids else None) or ("", "")]
        pr = cfg["privacy"]["mask_secrets"]
        mk = mask if pr else (lambda x: x)   # F2: alle Textfelder der Ausgabe, nicht nur body
        passages = []
        for head, body in rows:
            body = re.sub(r"\s+", " ", body).strip()
            passages.append({"heading": mk(head), "body": mk(body)})
        snippet = passages[0]["body"][:260]
        today = time.strftime("%Y-%m-%d")
        stale = isinstance(rm.get("stale_after"), str) and rm["stale_after"] < today
        unverified = bool(rm) and (not rm.get("confirmed") or rm.get("status") in ("proposed", "draft"))
        sup_by = reg.get("superseded_by", {}).get(p) or meta.get(p, ("", "", ""))[2]
        out.append({"path": p, "score": round(s, 5), "title": mk(meta.get(p, ("",))[0]), "heading": passages[0]["heading"],
                    "snippet": snippet, "passages": passages,
                    "why": list(dict.fromkeys(why[p]))[:4],   # Labels schon beim Erzeugen maskiert; Dateinamen bleiben lesbar
                    "superseded_by": sup_by or None,
                    "canonical": bool(rm.get("authority") == "canonical"),
                    "authority": mk(rm.get("authority")) if rm.get("authority") else None,
                    "verified_at": rm.get("verified_at"),
                    "stale": stale, "unverified": unverified})
    # --- Antwort-Tor (modellfrei): vier Antwortstatus + Signale ---
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
    gate_reason = ""
    if not ranked:
        answer_status = "nicht_belegt"; gate_reason = "keine Treffer"
    elif any(h.get("superseded_by") for h in out):
        answer_status = "widersprüchlich"; gate_reason = "abgelöste Quelle im Ergebnis (Auflösung sichtbar)"
    elif out and out[0].get("unverified"):
        answer_status = "belegt_gueltigkeit_unbestaetigt"; gate_reason = "Top-1-Gültigkeit nicht bestätigt"
    else:
        answer_status = "belegt"; gate_reason = "Top-1 belegt"
    if unmatched:
        why["_warn"].append("Begriffe ohne Treffer im Repository: " + ", ".join(unmatched))
    if top1_missing:
        why["_warn"].append("Begriffe nicht im Top-1-Ergebnis: " + ", ".join(top1_missing))
    cov = coverage_grade(c, cfg, q)
    if cov["uncovered"]:
        why["_warn"].append("Begriffe ohne ko-lokalen Beleg: " + ", ".join(cov["uncovered"]))
    trace = {"query_tokens": toks, "authority": auth_events, "gate": gate_reason}
    return {"results": out, "note": note, "warnings": why.get("_warn", []),
            "answer_status": answer_status, "unmatched_terms": unmatched,
            "top1_missing_terms": top1_missing, "term_coverage": cov["term_coverage"],
            "uncovered": cov["uncovered"], "uncovered_hint": cov["uncovered_hint"],
            "trace": trace, "bm25_top": bm25_top}


def require_index(root, cfg) -> sqlite3.Connection:
    """Index für Lesebefehle: fehlt er oder ist er leer, Fehler statt scheinbarem 'nicht_belegt' (F6)."""
    c = connect(root, cfg, create=False)
    if c.execute("select count(*) from files").fetchone()[0] == 0:
        c.close()
        raise WikitilaError(f"Index ist leer — zuerst `wikitila.py --root {root} build` ausführen "
                            "(oder include_ext/Ignore-Muster prüfen).")
    return c


def cmd_search(root, cfg, a):
    with contextlib.closing(require_index(root, cfg)) as c:
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
    if res.get("uncovered"):
        print(f"Term-Abdeckung: {res['term_coverage']:.2f} (ohne ko-lokalen Beleg: {', '.join(res['uncovered'])})")
    extra = f" (bm25_top {res['bm25_top']:.2f})" if res.get("bm25_top") is not None else ""
    print(f"Antwortstatus: {res.get('answer_status')}{extra}")
    print(f"{dt:.0f} ms")


def cmd_coverage(root, cfg, a):
    """Pre-Flight: wie gut deckt der Index die Frage ab (ohne Ranking). Analog zu `check_answerable`."""
    with contextlib.closing(require_index(root, cfg)) as c:
        t0 = time.time()
        cov = coverage_grade(c, cfg, a.query)
    dt = (time.time() - t0) * 1000
    if a.json:
        print(json.dumps({**cov, "ms": round(dt)}, ensure_ascii=False, indent=1)); return
    print(f"Frage: {a.query}")
    print(f"Term-Abdeckung: {cov['term_coverage']:.2f}")
    if cov.get("uncovered"):
        print("Ohne ko-lokalen Beleg:")
        for t in cov["uncovered"]:
            hint = cov.get("uncovered_hint", {}).get(t, "")
            print(f"  - {t}" + (f"  (nur in {hint})" if hint else "  (kein Treffer)"))
    print(f"{dt:.0f} ms")


# ---------- Embedding (optional) ----------
def cmd_embed(root, cfg):
    try:
        import numpy as np
    except ImportError:
        raise WikitilaError("embed braucht numpy (`pip install numpy`). Embedding ist optional, die Suche läuft ohne.")
    with contextlib.closing(require_index(root, cfg)) as c:
        _embed(c, cfg, np)


def _embed(c, cfg, np):
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
        norm = np.linalg.norm(vs, axis=1, keepdims=True)
        vs /= np.where(norm == 0, 1, norm)   # Nullvektor nicht durch 0 teilen
        for (cid, hh, _), v in zip(batch, vs):
            c.execute("insert or replace into emb values (?,?,?)", (cid, hh, v.tobytes()))
        c.commit()
    c.execute("delete from emb where cid not in (select rowid from t)")
    c.commit()
    print(f"Vektoren: {len(todo)} neu, {len(rows)} gesamt, {time.time()-t0:.0f}s, Modell {cfg['embedding']['model']}")


# ---------- Messung ----------
def load_jsonl(path: str, required: dict) -> list[dict]:
    """Liest ein Golden Set/einen Katalog (JSON Lines). required: {schlüssel: typ}. Fehler mit Zeilennummer."""
    p = Path(path)
    if not p.is_file():
        raise WikitilaError(f"Datei nicht gefunden: {path}")
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as e:
        raise WikitilaError(f"Datei unlesbar: {path}: {e}")
    out = []
    for i, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("//"):
            continue
        try:
            g = json.loads(line)
        except ValueError as e:
            raise WikitilaError(f"{path}:{i}: kein gültiges JSON ({e})")
        if not isinstance(g, dict):
            raise WikitilaError(f"{path}:{i}: erwartet ein JSON-Objekt je Zeile")
        for key, typ in required.items():
            if not isinstance(g.get(key), typ):
                raise WikitilaError(f"{path}:{i}: Feld '{key}' fehlt oder hat den falschen Typ "
                                    f"(erwartet {typ.__name__})")
        out.append(g)
    if not out:
        raise WikitilaError(f"{path} enthält keine Fälle.")
    return out


def pct(values: list[float], p: float) -> float:
    """Perzentil nach Nearest-Rank (gleiche Definition wie validate_catalog.py)."""
    sl = sorted(values)
    return sl[max(0, math.ceil(len(sl) * p) - 1)] if sl else 0.0


def cmd_eval(root, cfg, a):
    alle = load_jsonl(a.golden, {"q": str, "expect": list})
    with contextlib.closing(require_index(root, cfg)) as c:
        _eval(c, cfg, a, alle)


def _eval(c, cfg, a, alle):
    gold = [g for g in alle if g["expect"]]   # Negativfälle (expect leer) misst validate_catalog.py, nicht eval
    if not gold:
        raise WikitilaError(f"Golden Set {a.golden} enthält keine Fälle mit erwarteter Datei (expect).")
    skipped = len(alle) - len(gold)
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
              f"p50 {pct(lat, 0.5)*1000:.0f}ms p95 {pct(lat, 0.95)*1000:.0f}ms (n={n}"
              + (f", {skipped} ohne expect übersprungen" if skipped else "") + ")")
        if a.misses:
            for g, x in zip(gold, ranks):
                if not x:
                    print("   verfehlt:", g["q"][:90])


def cmd_status(root, cfg):
    c = connect(root, cfg, create=False)
    q = lambda s: c.execute(s).fetchone()[0]
    built = c.execute("select v from meta where k='built'").fetchone()
    print(f"Dateien {q('select count(*) from files')}, Abschnitte {q('select count(*) from t')}, "
          f"Link-Kanten {q('select count(*) from links')//2}, Entitäts-Zuordnungen {q('select count(*) from ent')}, "
          f"Vektoren {q('select count(*) from emb')}, Stand {built[0] if built else '-'}")
    print("Embedding:", "an" if cfg["embedding"]["enabled"] else "aus", "| Decision-Modell:",
          cfg["decision"]["model"] if cfg["decision"]["enabled"] else "aus")
    for w in cfg["_authority"].get("warnings", []):
        print("Hinweis:", w)
    for w in index_hints(c, cfg):
        print("Hinweis:", w)
    c.close()


def index_hints(c, cfg) -> list[str]:
    """Hinweise zum Indexzustand: veraltetes Format, Register-Pfade ohne Datei im Index."""
    out = []
    fmt = index_format(c)
    if fmt != INDEX_FORMAT:
        out.append(f"Indexformat {fmt or 'alt'} ist veraltet (aktuell {INDEX_FORMAT}) — `build` baut ihn vollständig neu")
    reg = cfg.get("_authority") or {}
    paths = {p for (p,) in c.execute("select path from files")}
    regp = set(reg.get("meta", {})) | set(reg.get("superseded_by", {}))
    missing = sorted(p for p in regp if p not in paths)
    for p in missing[:10]:
        out.append(f"Register-Pfad nicht im Index (Tippfehler, verschoben oder ignoriert?): {p}")
    if len(missing) > 10:
        out.append(f"… und {len(missing) - 10} weitere Register-Pfade nicht im Index")
    return out


def cmd_manifest(root: Path, cfg: dict, a):
    """Coverage-Report: Was ist auf der Platte, was ist indexiert, was ist warum ausgeschlossen.

    Schreibt `.wikitila/source_manifest.json` und druckt eine Kurzfassung. Scope = include_ext
    (Markdown laut Entscheidung 2026-11-14); alles andere wird als „nach Typ ausgeschlossen“ geführt.
    """
    from collections import Counter
    db = root / cfg["index"]["db"]
    indexed = []
    if db.exists():
        with contextlib.closing(connect(root, cfg)) as c:
            indexed = [p for (p,) in c.execute("select path from files")]
    pats = load_ignore(root, cfg)
    exts = tuple(cfg["corpus"]["include_ext"])
    disk = Counter()
    indexed_ext = Counter(Path(p).suffix.lower() or "(none)" for p in indexed)
    excl_type = Counter()
    excl_ignore = Counter()
    oversized = unreadable = outside = 0
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
            elif not inside_root(root, rel):
                outside += 1   # Symlink aus dem Ordner heraus oder ins Leere (F7)
            else:
                try:
                    if (root / rel).stat().st_size > MAX_FILE_BYTES:
                        oversized += 1
                except OSError:
                    unreadable += 1
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
            "oversized_limit_bytes": MAX_FILE_BYTES,
            "symlink_outside_root": outside,
            "unreadable": unreadable,
        },
        "indexed_by_ext": dict(sorted(indexed_ext.items())),
        "excluded_type_by_ext": dict(sorted(excl_type.items())),
        "excluded_ignore_by_ext": dict(sorted(excl_ignore.items())),
    }
    mf = db.parent / "source_manifest.json"
    mf.parent.mkdir(parents=True, exist_ok=True)
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Source-Manifest: {total_disk} Dateien auf Disk, {len(indexed)} indexiert "
          f"({', '.join(exts)}), {sum(excl_type.values())} nach Typ ausgeschlossen, "
          f"{sum(excl_ignore.values())} ignoriert, {oversized} zu groß übersprungen, "
          f"{outside} Symlinks außerhalb, {unreadable} unlesbar")
    print("  Indexiert nach Typ:", ", ".join(f"{e} {n}" for e, n in sorted(indexed_ext.items())))
    print("  Ausgeschlossen (Top):", ", ".join(f"{e} {n}" for e, n in excl_type.most_common(8)))
    print(f"  Manifest: {mf}")


def cmd_check(root: Path, cfg: dict, a) -> bool:
    """Index-/Quellstand-Abgleich (P0-5): meldet Drift zwischen Index und Disk, ohne zu bauen.

    Rückgabe: True bei Drift (neu/geändert/entfernt), False wenn Index aktuell ist.
    """
    db = root / cfg["index"]["db"]
    known = {}
    fmt_alt = False
    if db.exists():
        with contextlib.closing(connect(root, cfg)) as c:
            known = {p: s for p, s in c.execute("select path, sha from files")}
            fmt_alt = bool(known) and index_format(c) != INDEX_FORMAT
    if not db.exists():
        print(f"  Kein Index unter {db}.")
    seen = {}
    for rel in walk(root, cfg):
        raw = read_source(root, rel)
        if raw is None:
            continue
        seen[rel] = hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()
    new_changed = [p for p, s in seen.items() if known.get(p) != s]
    removed = [p for p in known if p not in seen]
    drift = bool(new_changed or removed or fmt_alt)
    if fmt_alt:
        print(f"  Indexformat veraltet (aktuell {INDEX_FORMAT}) — `build` baut den Index vollständig neu.")
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


# ---------- Lint (Schreibseite) ----------
LINT_EXT = (".md",)  # nur Markdown trägt Frontmatter; .txt bleibt im Such-Scope, aber außerhalb von lint


def lint_excluded(rel: str, pats: list[str]) -> bool:
    """True, wenn die Datei von lint ausgenommen ist (Muster auf Dateiname oder relativen Pfad,
    ohne Groß-/Kleinschreibung: `*template*` trifft auch `TEMPLATE.md`)."""
    rel_l = rel.lower()
    name = rel_l.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatchcase(name, p.lower()) or fnmatch.fnmatchcase(rel_l, p.lower()) for p in pats)


def lint_text(text: str, cfg: dict) -> tuple[list[str], list[str]]:
    """Prüft den Rohtext einer Datei gegen die Schreib-Konvention ([lint] in wikitila.toml).

    Verstösse = was der Index nicht verwerten kann: kein Frontmatter oder ein
    Pflichtfeld aus `require` fehlt/ist leer — gelesen mit derselben
    parse_doc-Logik wie der Build, damit „lint-konform = index-optimal" gilt.
    Hinweise = Konventionen ohne Suchbruch: unquotierter Doppelpunkt (bricht
    strikte YAML-Parser), status ausserhalb `status_values`, strukturlose
    Frontmatter-Zeilen. Hinweise haben keinen Einfluss auf den Exit-Code.
    """
    errors: list[str] = []
    notes: list[str] = []
    m, text = frontmatter(text)   # gleiche Erkennung wie parse_doc (BOM, leerer Block, Block am Dateiende)
    if not m:
        if text.startswith("---"):
            errors.append("Frontmatter nicht abgeschlossen (schließende '---'-Zeile fehlt)")
        else:
            errors.append("kein Frontmatter (Datei beginnt nicht mit '---')")
        return errors, notes
    for line in (m.group(1) or "").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        km = FM_KEY_RE.match(line)
        if km:
            val = km.group(2).strip()
            if val and not val.startswith(("\"", "'", "[", "{", "|", ">")) and ": " in val:
                notes.append(f"'{km.group(1)}' enthält einen unquotierten Doppelpunkt — strikte YAML-Parser "
                             "brechen daran, den Wert in Anführungszeichen setzen")
        elif not line.startswith((" ", "\t", "- ")):
            notes.append(f"Frontmatter-Zeile ohne erkennbare Struktur: {line[:40]!r}")
    fm, _ = parse_doc(text)  # bewusst dieselbe Sicht wie der Index
    for field in cfg["lint"]["require"]:
        if not fm.get(field):
            errors.append(f"Pflichtfeld '{field}' fehlt oder ist leer (der Index liest es nicht)")
    status = fm.get("status")
    sv = cfg["lint"]["status_values"]
    if status and sv and status not in sv:
        notes.append(f"'status' außerhalb der Konvention ({'/'.join(sv)}): {status!r}")
    return errors, notes


def cmd_lint(root: Path, cfg: dict, a) -> bool:
    """Schreibseite prüfen: Frontmatter gegen [lint] aus wikitila.toml.

    Einzeldatei (`lint <datei>`) oder Gesamt-Report (`lint --all [--json]`).
    Rückgabe: True, wenn Verstösse gefunden wurden (main gibt dann Exit 1).
    """
    lcfg = cfg.get("lint", {})
    pats = [str(p) for p in (lcfg.get("exclude") or [])]
    since = str(lcfg.get("since") or "").strip()
    cutoff = None
    if since:
        try:
            cutoff = time.mktime(time.strptime(since, "%Y-%m-%d"))
        except ValueError:
            raise WikitilaError(f"[lint] since ungültig (erwartet JJJJ-MM-TT): {since!r}")
    hide = cfg["privacy"]["mask_secrets"]

    def pruefe(rel: str, raw: str) -> dict:
        errors, notes = lint_text(raw, cfg)
        if hide:
            errors, notes = [mask(e) for e in errors], [mask(n) for n in notes]
        return {"path": rel, "errors": errors, "notes": notes}

    if a.all:
        ergebnisse, ok, ausgenommen = [], 0, 0
        for rel in walk(root, cfg):
            if not rel.lower().endswith(LINT_EXT):
                continue  # .txt u. a.: kein Frontmatter-Format, nicht Teil der Schreib-Konvention
            if lint_excluded(rel, pats) or (cutoff is not None and os.path.getmtime(root / rel) < cutoff):
                ausgenommen += 1
                continue
            raw = read_source(root, rel)
            if raw is None:
                continue
            e = pruefe(rel, raw)
            if e["errors"] or e["notes"]:
                ergebnisse.append(e)
            else:
                ok += 1
        ver = [e for e in ergebnisse if e["errors"]]
        hin = [e for e in ergebnisse if not e["errors"]]
        if a.json:
            print(json.dumps({"checked": ok + len(ergebnisse), "ok": ok, "notes": len(hin),
                              "violations": len(ver), "excluded": ausgenommen,
                              "files": ergebnisse}, ensure_ascii=False, indent=1))
        else:
            print(f"Lint: {ok + len(ergebnisse)} geprüft, {ok} konform, {len(hin)} mit Hinweisen, "
                  f"{len(ver)} mit Verstößen, {ausgenommen} ausgenommen")
            for e in ergebnisse:
                tag = "VERSTOSS" if e["errors"] else "HINWEIS"
                erstes = e["errors"][0] if e["errors"] else e["notes"][0]
                print(f"  {tag} {e['path']}: {erstes}")
        return bool(ver)

    arg = getattr(a, "path", None)
    if not arg:
        raise WikitilaError("lint braucht eine Datei (`lint <datei>`) oder --all.")
    # Hooks übergeben oft absolute Pfade; relative gelten zum Ordner (--root).
    p = Path(arg) if Path(arg).is_absolute() else root / arg
    try:
        rel = p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        raise WikitilaError(f"Datei liegt außerhalb des Ordners ({root}): {arg}")
    if not (root / rel).is_file():
        raise WikitilaError(f"Datei nicht gefunden: {arg}")
    if not rel.lower().endswith(LINT_EXT) or lint_excluded(rel, pats):
        # Ausgenommen ist kein Fehler: ein Hook auf README.md oder notizen.txt bleibt bei Exit 0.
        if a.json:
            print(json.dumps({"path": rel, "excluded": True, "errors": [], "notes": []}, ensure_ascii=False, indent=1))
        else:
            print(f"AUSGENOMMEN — {rel} fällt nicht unter die Schreib-Konvention ([lint] exclude bzw. kein .md)")
        return False
    raw = read_source(root, rel)
    if raw is None:
        raise WikitilaError(f"Datei unlesbar oder zu gross: {rel}")
    e = pruefe(rel, raw)
    if a.json:
        print(json.dumps(e, ensure_ascii=False, indent=1))
        return bool(e["errors"])
    for n in e["notes"]:
        print(f"  HINWEIS: {n}")
    if e["errors"]:
        for err in e["errors"]:
            print(f"  VERSTOSS: {err}")
        n = len(e["errors"])
        print(f"{rel}: {n} Verstoß" + ("" if n == 1 else "e"))
    else:
        print(f"OK — {rel} erfüllt die Schreib-Konvention" + (f" ({len(e['notes'])} Hinweis(e))" if e["notes"] else ""))
    return bool(e["errors"])


def positive_int(v: str) -> int:
    try:
        n = int(v)
    except ValueError:
        raise argparse.ArgumentTypeError(f"ganze Zahl erwartet: {v!r}")
    if n < 1:
        raise argparse.ArgumentTypeError(f"muss ≥ 1 sein: {n}")
    return n


def main():
    if sys.version_info < (3, 11):
        print(f"FEHLER: LLM-Wikitila braucht Python ≥ 3.11 (gefunden {sys.version.split()[0]}: {sys.executable}).",
              file=sys.stderr)
        sys.exit(2)
    if sqlite3 is None:
        print(f"FEHLER: Dieses Python ({sys.executable}) hat kein sqlite3-Modul. Ein anderes Python ≥ 3.11 nutzen "
              "(z. B. das System-Python) oder Python mit SQLite-Unterstützung neu bauen.", file=sys.stderr)
        sys.exit(2)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"LLM-Wikitila {__version__}")
    ap.add_argument("--root", default=os.environ.get("WIKITILA_ROOT", "."))
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("build"); sp.add_parser("embed"); sp.add_parser("status"); sp.add_parser("manifest"); sp.add_parser("check")
    s = sp.add_parser("search"); s.add_argument("query"); s.add_argument("-k", type=positive_int, default=5); s.add_argument("--json", action="store_true")
    cv = sp.add_parser("coverage"); cv.add_argument("query"); cv.add_argument("--json", action="store_true")
    l = sp.add_parser("lint"); l.add_argument("path", nargs="?"); l.add_argument("--all", action="store_true"); l.add_argument("--json", action="store_true")
    e = sp.add_parser("eval"); e.add_argument("golden"); e.add_argument("--variants", action="store_true"); e.add_argument("--misses", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    try:
        if not root.is_dir():
            raise WikitilaError(f"Ordner nicht gefunden: {root} (--root bzw. WIKITILA_ROOT prüfen)")
        cfg = load_cfg(root)
        cmds = {"build": lambda: cmd_build(root, cfg), "embed": lambda: cmd_embed(root, cfg),
                "status": lambda: cmd_status(root, cfg), "manifest": lambda: cmd_manifest(root, cfg, a),
                "check": lambda: cmd_check(root, cfg, a), "search": lambda: cmd_search(root, cfg, a),
                "coverage": lambda: cmd_coverage(root, cfg, a), "eval": lambda: cmd_eval(root, cfg, a),
                "lint": lambda: cmd_lint(root, cfg, a)}
        rc = cmds[a.cmd]()
        if a.cmd == "lint" and rc:  # einziger Befehl mit Exit 1 bei Verstößen (CI-/Agenten-Gating)
            sys.exit(1)
    except WikitilaError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        sys.exit(2)
    except sqlite3.Error as e:
        hint = (" — dieses SQLite hat kein FTS5; ein Python mit FTS5-fähigem SQLite nutzen" if "fts5" in str(e).lower()
                else " — Index beschädigt? `.wikitila/` löschen und `build` erneut ausführen" if any(x in str(e).lower() for x in ("malformed", "not a database"))
                else "")
        print(f"FEHLER: SQLite: {e}{hint}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("Abgebrochen.", file=sys.stderr)
        sys.exit(130)
    except BrokenPipeError:   # Ausgabe in `head` o. ä. umgeleitet und vorzeitig geschlossen
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(1)


if __name__ == "__main__":
    main()
