#!/usr/bin/env python3
"""Generiert das Stack-Kompositions-Diagramm von LLM-Wikitila.

Ausgaben (aus EINER Layout-Definition, dadurch immer synchron):
  - stack-komposition.excalidraw   editierbar (excalidraw.com, Datei per Drag&Drop)
  - stack-komposition.png          Render für README/Doku (Playwright headless)

Optional, nur für die Neu-Erzeugung nötig: pip install playwright && playwright install chromium
"""
import json
import sys
from pathlib import Path

OUT = Path(__file__).parent
W, H = 1440, 980

# ---------------------------------------------------------------- Layout
# (id, x, y, w, h, fill, label, fontsize)
BOXES = [
    # Quelle (oben links)
    ("src",        40,  40, 360, 200, "#a5d8ff", "Projekt-Ordner (kanonisch)\nMarkdown-Dateien (.md/.txt)\n.graphifyignore\nwikitila.toml\nauthority_register.json", 18),
    # Aufbau links
    ("build",      40, 330, 360,  90, "#d0bfff", "wikitila.py build\n(inkrementell, Sekunden)", 18),
    ("index",      40, 500, 360, 170, "#c3fae8", "SQLite-Datei .wikitila/index.db\nFTS5 / BM25 + Wortstamm-Präfix\nLink-Graph (deterministisch)\nEntitäts-Graph (Gewicht 0,05)", 17),
    # Aufbau rechts (optionaler Graph)
    ("graphrun",  520, 330, 320,  90, "#ffd8a8", "wikitila_graph.py run/build\n(optional, fortsetzbar)", 17),
    ("ollama",    520, 500, 320,  80, "#ffd8a8", "Ollama · ling-3.0-tiny:8b\n(ohne Thinking, lokal)", 16),
    ("graphjson", 520, 620, 320,  70, "#ffd8a8", "graphify-out/graph.json\n(Navigation, nie Belegquelle)", 16),
    # Laufzeit (Mitte unten)
    ("search",     40, 790, 700,  90, "#b2f2bb", "wikitila.py search  (~20 ms, kein Modell)\nBM25 -> Dateiname -> Graph-Boost\nAuthority-Register -> Antwort-Tor", 17),
    ("register",  900, 500, 500, 110, "#fff3bf", "Authority-Register (Owner-geführt)\nkanonisch · überholt durch · stale_after · value", 17),
    ("gate",      900, 660, 500,  90, "#b2f2bb", "Antwort-Tor: belegt · widersprüchlich ·\nbelegt_gueltigkeit_unbestaetigt · nicht_belegt", 17),
    ("result",    900, 800, 500,  90, "#b2f2bb", "Ergebnis: Datei · Überschrift ·\nOriginalpassagen · Flags · answer_status", 17),
]

# (start_id, end_id, start_fp, end_fp, label, dashed)
ARROWS = [
    ("src",      "build",    [0.5, 1],  [0.5, 0], "Dateien",           False),
    ("src",      "graphrun", [1, 0.5],  [0, 0.5], "Dateien (optional)", False),
    ("build",    "index",    [0.5, 1],  [0.5, 0], "",                 False),
    ("graphrun", "ollama",   [0.5, 1],  [0.5, 0], "",                 False),
    ("ollama",   "graphjson",[0.5, 1],  [0.5, 0], "",                 False),
    ("graphjson","index",    [0, 0.5],  [1, 0.75], "Entitäten",        True),
    ("index",    "search",   [0.65, 1], [0.25, 0], "",                 False),
    ("register", "gate",     [0.5, 1],  [0.5, 0], "",                 False),
    ("gate",     "result",   [0.5, 1],  [0.5, 0], "",                 False),
    ("register", "search",   [0, 0.95], [1, 0.5], "Thema -> kanonisch", True),
    ("search",   "result",   [1, 0.5],  [0, 0.5], "Treffer",           False),
]

TITLE = "LLM-Wikitila — Stack-Komposition"

# ---------------------------------------------------------------- Helfer
def shape(box):
    i, x, y, w, h, fill, label, fs = box
    text_id = f"t_{i}"
    return (
        {"type": "rectangle", "id": i, "x": x, "y": y, "width": w, "height": h,
         "roundness": {"type": 3}, "backgroundColor": fill, "fillStyle": "solid",
         "boundElements": [{"id": text_id, "type": "text"}]},
        {"type": "text", "id": text_id, "x": x + 10, "y": y + (h - fs * 1.35 * (label.count("\n") + 1)) / 2,
         "width": w - 20, "height": fs * 1.35 * (label.count("\n") + 1),
         "text": label, "fontSize": fs, "fontFamily": 1, "strokeColor": "#1e1e1e",
         "textAlign": "center", "verticalAlign": "middle",
         "containerId": i, "originalText": label, "autoResize": True},
    )

def arrow(ar):
    a, b, sfp, efp, label, dashed = ar
    ba = next(x for x in BOXES if x[0] == a)
    bb = next(x for x in BOXES if x[0] == b)
    x1 = ba[1] + ba[3] * sfp[0]
    y1 = ba[2] + ba[4] * sfp[1]
    x2 = bb[1] + bb[3] * efp[0]
    y2 = bb[2] + bb[4] * efp[1]
    aid = f"a_{a}_{b}"
    elements = [{"type": "arrow", "id": aid, "x": x1, "y": y1,
                 "width": x2 - x1, "height": y2 - y1,
                 "points": [[0, 0], [x2 - x1, y2 - y1]], "endArrowhead": "arrow",
                 "strokeStyle": "dashed" if dashed else "solid",
                 "startBinding": {"elementId": a, "fixedPoint": sfp},
                 "endBinding": {"elementId": b, "fixedPoint": efp}}]
    if label:
        tid = f"t_{aid}"
        elements.append({"type": "text", "id": tid,
                         "x": (x1 + x2) / 2 - (len(label) * 7.2) / 2,
                         "y": (y1 + y2) / 2 - 12, "width": len(label) * 7.2, "height": 20,
                         "text": label, "fontSize": 15, "fontFamily": 1, "strokeColor": "#1e1e1e",
                         "textAlign": "center", "verticalAlign": "middle",
                         "containerId": aid, "originalText": label, "autoResize": True})
    return elements

def main():
    elements = [{"type": "text", "id": "title", "x": 40, "y": 5, "width": 700, "height": 30,
                 "text": TITLE, "fontSize": 24, "fontFamily": 1, "strokeColor": "#1e1e1e",
                 "originalText": TITLE, "autoResize": True}]
    for b in BOXES:
        elements.extend(shape(b))
    for ar in ARROWS:
        elements.extend(arrow(ar))
    doc = {"type": "excalidraw", "version": 2, "source": "hermes-agent",
           "elements": elements, "appState": {"viewBackgroundColor": "#ffffff"}}
    (OUT / "stack-komposition.excalidraw").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print("geschrieben:", OUT / "stack-komposition.excalidraw")

    # ---------------- HTML für PNG (gleiche Koordinaten)
    html = [f"""<!doctype html><html><head><meta charset="utf-8"><style>
    body {{ margin:0; width:{W}px; height:{H}px; background:#fff;
           font-family: 'Comic Sans MS', 'Segoe Print', 'Trebuchet MS', sans-serif; }}
    .box {{ position:absolute; border:2.5px solid #1e1e1e; border-radius:10px;
           display:flex; align-items:center; justify-content:center; text-align:center;
           font-size:{17}px; line-height:1.25; color:#1e1e1e; padding:8px; box-sizing:border-box;
           white-space:pre-wrap; }}
    .ttl {{ position:absolute; font-size:26px; font-weight:bold; color:#1e1e1e; }}
    svg {{ position:absolute; left:0; top:0; }}
    .lab {{ font-size:15px; fill:#1e1e1e; font-family:inherit; }}
    </style></head><body>
    <div class="ttl" style="left:40px;top:6px">{TITLE}</div>
    <svg width="{W}" height="{H}"><defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 z" fill="#1e1e1e"/></marker></defs>"""]
    for ar in ARROWS:
        a, b, sfp, efp, label, dashed = ar
        ba = next(x for x in BOXES if x[0] == a)
        bb = next(x for x in BOXES if x[0] == b)
        x1, y1 = ba[1] + ba[3] * sfp[0], ba[2] + ba[4] * sfp[1]
        x2, y2 = bb[1] + bb[3] * efp[0], bb[2] + bb[4] * efp[1]
        dash = ' stroke-dasharray="7 6"' if dashed else ""
        html.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#1e1e1e" stroke-width="2" marker-end="url(#m)"{dash}/>')
        if label:
            html.append(f'<text class="lab" x="{(x1+x2)/2}" y="{(y1+y2)/2 - 6}" text-anchor="middle">{label}</text>')
    html.append("</svg>")
    for i, x, y, w, h, fill, label, fs in BOXES:
        html.append(f'<div class="box" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{fill};font-size:{fs}px">{label}</div>')
    html.append("</body></html>")
    (OUT / "_render.html").write_text("".join(html), encoding="utf-8")
    print("geschrieben:", OUT / "_render.html")

if __name__ == "__main__":
    main()
