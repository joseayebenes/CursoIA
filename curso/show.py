"""How the notebook shows things: tables, bars, the embeddings map, the models side by side,
the agent steps, the call graph, the diagrams and the list of limits.

Each helper displays HTML (with inline SVG for the figures) and plain text for frontends
that cannot show HTML; outside a notebook it prints the text. The colours are mid tones
and the text takes the colour of the frontend, so the figures read in light and dark
themes alike. No dependencies beyond IPython, which comes with ipykernel.
"""
from __future__ import annotations

import itertools
import json
import os
from html import escape

BLUE, ORANGE, PURPLE, RED, GREEN = "#3d85c6", "#d9822b", "#9b6bcc", "#d0453a", "#4a9c5d"
PALETTE = [BLUE, ORANGE, PURPLE, RED, GREEN]
LINE = 'stroke="currentColor" stroke-opacity="0.45"'
FONT = "font-family=\"system-ui, -apple-system, 'Segoe UI', sans-serif\""
MONO = "font-family=\"ui-monospace, Menlo, Consolas, monospace\""
_ids = itertools.count(1)


def _uid(name: str) -> str:
    """An id unique in the page: every output of the notebook shares one document."""
    return f"{name}-{os.getpid()}-{next(_ids)}"


def _display(html: str, text: str) -> None:
    try:
        from IPython import get_ipython
        from IPython.display import display
    except ImportError:
        print(text)
        return
    if get_ipython() is None:
        print(text)
    else:
        display({"text/html": html, "text/plain": text}, raw=True)


def _svg(width: float, height: float, body: str, label: str, max_width: int) -> str:
    return (f'<svg viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="{escape(label)}" '
            f'style="width:100%;max-width:{max_width}px;height:auto;color:inherit" {FONT}>'
            f'{body}</svg>')


# --- tables and bars ---------------------------------------------------------------------

def table(rows: list[dict]) -> None:
    """A list of dicts as a table, one column per key of the first row."""
    if not rows:
        _display("<p><i>(ninguna fila)</i></p>", "(ninguna fila)")
        return
    columns = list(rows[0])
    head = "".join(f'<th style="text-align:left">{escape(str(c))}</th>' for c in columns)
    body = "".join("<tr>" + "".join(f'<td style="text-align:left">{escape(str(r[c]))}</td>'
                                    for c in columns) + "</tr>" for r in rows)
    widths = [max(len(str(c)), *(len(str(r[c])) for r in rows)) for c in columns]
    lines = ["  ".join(str(c).ljust(w) for c, w in zip(columns, widths))]
    lines += ["  ".join(str(r[c]).ljust(w) for c, w in zip(columns, widths)) for r in rows]
    _display(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>",
             "\n".join(lines))


def bars(items: list[tuple[str, float]]) -> None:
    """Probabilities (0 to 1) as horizontal bars: (label, value) pairs."""
    top = max(v for _, v in items)
    rows = "".join(
        f'<div style="display:flex;align-items:center;gap:10px;margin:3px 0">'
        f'<code style="width:7em;text-align:right">«{escape(label)}»</code>'
        f'<div style="flex:1;max-width:420px;background:rgba(128,128,128,.15);border-radius:3px">'
        f'<div style="width:{v * 100:.1f}%;height:16px;border-radius:3px;'
        f'background:{ORANGE if v == top else BLUE}"></div></div>'
        f'<span style="width:4.5em;font-variant-numeric:tabular-nums">{v * 100:.1f} %</span></div>'
        for label, v in items)
    _display(f"<div>{rows}</div>",
             "\n".join(f"«{label}»  {v * 100:5.1f} %" for label, v in items))


# --- the embeddings map ------------------------------------------------------------------

def scatter(xy, labels: list[str], groups: list[str], highlight=()) -> None:
    """Points in 2D coloured by group. Every point shows its label on hover; the ones in
    `highlight` (indexes) show it always."""
    w, h, pad = 720, 420, 30
    xs, ys = [float(p[0]) for p in xy], [float(p[1]) for p in xy]
    def sx(x): return pad + (x - min(xs)) / ((max(xs) - min(xs)) or 1) * (w - 2 * pad)
    def sy(y): return h - pad - (y - min(ys)) / ((max(ys) - min(ys)) or 1) * (h - 2 * pad)
    colour = {g: PALETTE[i % len(PALETTE)] for i, g in enumerate(dict.fromkeys(groups))}
    highlight = [int(i) for i in highlight]
    dots, marks = [], []
    for i, (x, y, label, group) in enumerate(zip(xs, ys, labels, groups)):
        r = 6.5 if i in highlight else 4.5
        dots.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="{r}" fill="{colour[group]}" '
                    f'fill-opacity="0.85"><title>{escape(label)} ({escape(group)})</title></circle>')
    placed: list[tuple[float, float, str]] = []
    for i in sorted(highlight, key=lambda i: sy(ys[i])):
        x, y = sx(xs[i]), sy(ys[i]) + 4
        while any(abs(y - py) < 14 and abs(x - px) < 160 for px, py, _ in placed):
            y += 14                                    # do not write over another label
        placed.append((x, y, labels[i]))
    for x, y, label in placed:
        end = x > w * 0.62
        marks.append(f'<text x="{x - 10 if end else x + 10:.1f}" y="{y:.1f}" font-size="12.5" '
                     f'fill="currentColor" text-anchor="{"end" if end else "start"}">'
                     f'{escape(label)}</text>')
    frame = f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="6" fill="none" {LINE} stroke-opacity="0.2"/>'
    legend = "".join(f'<span style="margin-right:16px;white-space:nowrap"><span style="display:inline-block;'
                     f'width:10px;height:10px;border-radius:50%;background:{c};margin-right:6px">'
                     f'</span>{escape(g)}</span>' for g, c in colour.items())
    html = (_svg(w, h, frame + "".join(dots) + "".join(marks), "Mapa en dos dimensiones", w)
            + f'<div style="font-size:13px;margin-top:6px">{legend}'
              f'<span style="opacity:.7">Pasa el ratón por un punto para ver qué es.</span></div>')
    text = "\n".join(f"({xs[i]:+.2f}, {ys[i]:+.2f})  {labels[i]}  [{groups[i]}]" for i in highlight)
    _display(html, text or f"{len(xs)} puntos")


# --- models side by side and agent steps -------------------------------------------------

def side_by_side(answers: dict[str, tuple[str, float]]) -> None:
    """Answers of several models: {model: (text, seconds)}."""
    cards = "".join(
        f'<div style="border:1px solid rgba(128,128,128,.35);border-radius:8px;padding:10px 12px">'
        f'<div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:6px">'
        f'<b>{escape(model)}</b><span style="opacity:.7">{seconds:.1f} s</span></div>'
        f'<div style="white-space:pre-wrap;font-size:13px;line-height:1.45">{escape(text.strip())}</div></div>'
        for model, (text, seconds) in answers.items())
    _display(f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));'
             f'gap:12px">{cards}</div>',
             "\n\n".join(f"== {m} ({s:.1f} s)\n{t.strip()}" for m, (t, s) in answers.items()))


def tool(name: str, description: str, **params: str) -> dict:
    """The JSON schema of a tool whose parameters are all strings: {name: description}."""
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "required": list(params),
                       "properties": {p: {"type": "string", "description": d}
                                      for p, d in params.items()}}}}


def step(name: str, args: dict, result, limit: int = 2000) -> None:
    """One step of an agent: the tool it asked for and what it got back (folded)."""
    text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=1)
    text = text if len(text) <= limit else text[:limit] + " …"
    call = f"{name}({', '.join(f'{k}={v!r}' for k, v in args.items())})"
    _display(f'<details><summary>→ <code>{escape(call)}</code></summary>'
             f'<pre style="white-space:pre-wrap;font-size:12px;max-height:320px;overflow:auto">'
             f'{escape(text)}</pre></details>',
             f"→ {call}\n" + "\n".join("    " + line for line in text[:300].splitlines()))


# --- the call graph ----------------------------------------------------------------------

def graph(subs: list[dict], target: str) -> None:
    """Who calls `target` among `subs` (dicts with name, calls, reqs and test), callers on
    the left, with the requirements of each subprogram under its name."""
    by_name = {s["name"]: s for s in subs}
    edges = [(s["name"], c) for s in subs for c in sorted(s["calls"]) if c in by_name]
    depth: dict[str, int] = {}

    def level(name: str, seen=()) -> int:            # longest path down to the target
        if name not in depth:
            callees = [c for c in by_name[name]["calls"] if c in by_name and c not in seen]
            depth[name] = 0 if name == target else 1 + max(
                (level(c, seen + (name,)) for c in callees), default=0)
        return depth[name]

    for name in by_name:
        level(name)
    # an arrow that skips columns goes through a waypoint in each of them, so that it
    # passes between the boxes and not over them
    chains = {(a, b): [a] + [("via", a, b, d) for d in range(depth[a] - 1, depth[b], -1)] + [b]
              for a, b in edges}
    columns: list[list] = [[] for _ in range(max(depth.values()) + 1)]
    for name in sorted(by_name):
        columns[depth[name]].append(name)
    for chain in chains.values():
        for via in chain[1:-1]:
            columns[via[3]].append(via)
    below: dict = {}                                  # each item and what it leads to
    for chain in chains.values():
        for a, b in zip(chain, chain[1:]):
            below.setdefault(a, []).append(b)
    char, gap, pad = 7.3, 70, 12
    label = {n: ", ".join(by_name[n]["reqs"]) or "—" for n in by_name}
    widths = [max([len(n) * char + 2 * pad for n in col if isinstance(n, str)]
                  + [len(label[n]) * 6.3 + 2 * pad for n in col if isinstance(n, str)] + [40])
              for col in columns]
    xs = [sum(widths[d + 1:]) + gap * (len(columns) - 1 - d) + 10 for d in range(len(columns))]
    centre: dict = {}
    heights = []
    for d, col in enumerate(columns):                 # order by the height of what they call
        if d:
            col.sort(key=lambda n: sum(centre[b] for b in below[n]) / len(below[n]))
        y = 0.0
        for n in col:
            slot = 62 if isinstance(n, str) else 22
            centre[n] = y + slot / 2
            y += slot
        heights.append(y)
    for d, col in enumerate(columns):                 # every column centred vertically
        for n in col:
            centre[n] += 20 + (max(heights) - heights[d]) / 2
    def left(n): return xs[depth[n] if isinstance(n, str) else n[3]]
    def right(n): return left(n) + widths[depth[n] if isinstance(n, str) else n[3]]
    arrow = _uid("arrow")
    paths, nodes = [], []
    for chain in chains.values():
        d = ""
        for a, b in zip(chain, chain[1:]):
            x1, y1, x2, y2 = right(a), centre[a], left(b), centre[b]
            xm = (x1 + x2) / 2
            d += (f"M{left(a):.0f},{y1:.0f} " if not isinstance(a, str) else f"M{x1:.0f},{y1:.0f} ")
            d += f"L{x1:.0f},{y1:.0f} C{xm:.0f},{y1:.0f} {xm:.0f},{y2:.0f} {x2 - 4:.0f},{y2:.0f} "
        paths.append(f'<path d="{d.strip()}" fill="none" {LINE} marker-end="url(#{arrow})"/>')
    for name in by_name:
        x, y = left(name), centre[name] - 19
        stroke = (f'stroke="{ORANGE}" stroke-width="2"' if name == target
                  else LINE + (' stroke-dasharray="4 3"' if by_name[name]["test"] else ""))
        nodes.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{widths[depth[name]]:.0f}" height="38" '
                     f'rx="6" fill="currentColor" fill-opacity="0.04" {stroke}/>'
                     f'<text x="{x + pad:.0f}" y="{y + 16:.0f}" font-size="12" {MONO} '
                     f'fill="currentColor">{escape(name)}</text>'
                     f'<text x="{x + pad:.0f}" y="{y + 31:.0f}" font-size="11" fill="{BLUE}">'
                     f'{escape(label[name])}</text>')
    defs = (f'<defs><marker id="{arrow}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="currentColor" '
            'fill-opacity="0.6"/></marker></defs>')
    note = ('<div style="font-size:13px;opacity:.75;margin-top:4px">Cada flecha va de quien llama '
            'a quien es llamado; en azul, los requisitos de cada uno; con borde discontinuo, las '
            'pruebas.</div>')
    width = sum(widths) + gap * (len(columns) - 1) + 20
    _display(_svg(width, max(heights) + 40, defs + "".join(paths) + "".join(nodes),
                  f"Quién llama a {target}", int(width)) + note,
             "\n".join(f"{a} -> {b}" for a, b in edges))


# --- diagrams ----------------------------------------------------------------------------

DIAGRAMS = {
    # boxes: id -> (column, row, text, kind); edges: (from, to, style, label)
    "mcp": {
        "boxes": {
            "editor": (0, 0, "El editor\nVS Code, OpenCode…", "process"),
            "server": (1, 0, "Servidor MCP del proyecto\nsearch · get_requirement\nread_file · trace", "tools"),
            "data": (2, 0, "Requisitos, documentos\ny código Ada", "data"),
            "model": (0, 1, "El modelo de la empresa", "model"),
        },
        "edges": [("editor", "server", "<->", "MCP"), ("server", "data", "->", ""),
                  ("editor", "model", "<->", "chat")],
    },
    "sesion": {
        "boxes": {
            "question": (0, 0, "Pregunta", "process"),
            "rewrite": (1, 0, "Reescribir\ncon glosario", "process"),
            "hybrid": (2, 0, "Búsqueda híbrida\n(RRF)", "process"),
            "sources": (3, 0, "Fuentes\nnumeradas", "process"),
            "model": (4, 0, "Modelo", "model"),
            "answer": (5, 0, "Respuesta\ncon citas [n]", "process"),
            "docs": (0, 1, "Requisitos,\ndiseño, manual", "data"),
            "chunks": (1, 1, "Trozos\npor sección", "process"),
            "search": (2, 1, "IDs exactos,\nvectores, BM25", "process"),
            "code": (0, 2, "Código Ada", "data"),
            "graph": (1, 2, "Grafo de llamadas\ny de «Req:»", "process"),
            "trace": (2, 2, "Traza, impacto,\nhuecos", "process"),
            "tools": (3, 2, "Herramientas", "tools"),
            "agent": (4, 2, "Agente:\nun bucle", "process"),
            "editor": (3, 3, "El editor,\npor MCP", "process"),
        },
        "edges": [("question", "rewrite", "->", ""), ("rewrite", "hybrid", "->", ""),
                  ("hybrid", "sources", "->", ""), ("sources", "model", "->", ""),
                  ("model", "answer", "->", ""), ("docs", "chunks", "->", ""),
                  ("chunks", "search", "->", ""), ("search", "hybrid", "->", ""),
                  ("code", "graph", "->", ""), ("graph", "trace", "->", ""),
                  ("agent", "tools", "->", ""), ("tools", "trace", "-->", ""),
                  ("tools", "search", "-->", ""), ("agent", "model", "<->", ""),
                  ("tools", "editor", "-->", "")],
    },
}
_FILL = {"process": ("currentColor", 0.04), "data": (BLUE, 0.16), "model": (ORANGE, 0.2),
         "tools": (PURPLE, 0.16)}


def diagram(name: str) -> None:
    """One of the diagrams of the session: "mcp" or "sesion"."""
    spec = DIAGRAMS[name]
    bw, bh, gx, gy = (200, 58, 70, 40) if name == "mcp" else (150, 58, 34, 34)
    def box(key):
        c, r, *_ = spec["boxes"][key]
        return 10 + c * (bw + gx), 10 + r * (bh + gy)
    head, tail = _uid("head"), _uid("tail")
    parts = []
    for a, b, style, label in spec["edges"]:
        (xa, ya), (xb, yb) = box(a), box(b)
        if ya == yb:                                      # same row: side to side
            x1, x2 = (xa + bw, xb) if xb > xa else (xa, xb + bw)
            y1 = y2 = ya + bh / 2
        elif xa == xb:                                    # same column: top to bottom
            x1 = x2 = xa + bw / 2
            y1, y2 = (ya + bh, yb) if yb > ya else (ya, yb + bh)
        else:                                             # diagonal: corner to corner
            x1, x2 = (xa, xb + bw) if xb < xa else (xa + bw, xb)
            y1, y2 = (ya, yb + bh) if yb < ya else (ya + bh, yb)
        dash = ' stroke-dasharray="5 4"' if style == "-->" else ""
        start = f' marker-start="url(#{tail})"' if style == "<->" else ""
        parts.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" {LINE} '
                     f'stroke-width="1.5"{dash}{start} marker-end="url(#{head})"/>')
        if label:
            parts.append(f'<text x="{(x1 + x2) / 2 + (6 if x1 == x2 else 0):.0f}" '
                         f'y="{(y1 + y2) / 2 - 6 if y1 == y2 else (y1 + y2) / 2 + 4:.0f}" '
                         f'font-size="12" fill="currentColor" '
                         f'text-anchor="{"start" if x1 == x2 else "middle"}">{escape(label)}</text>')
    for key, (_, _, text, kind) in spec["boxes"].items():
        x, y = box(key)
        fill, opacity = _FILL[kind]
        lines = text.split("\n")
        parts.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="8" fill="{fill}" '
                     f'fill-opacity="{opacity}" {LINE}/>')
        for i, line in enumerate(lines):
            parts.append(f'<text x="{x + bw / 2:.0f}" y="{y + bh / 2 + (i - (len(lines) - 1) / 2) * 15 + 4.5:.0f}" '
                         f'font-size="12.5" fill="currentColor" text-anchor="middle">{escape(line)}</text>')
    defs = (f'<defs><marker id="{head}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="currentColor" '
            f'fill-opacity="0.7"/></marker><marker id="{tail}" viewBox="0 0 10 10" refX="1" refY="5" '
            'markerWidth="7" markerHeight="7" orient="auto"><path d="M10,0 L0,5 L10,10 z" '
            'fill="currentColor" fill-opacity="0.7"/></marker></defs>')
    columns = 1 + max(c for c, *_ in spec["boxes"].values())
    rows = 1 + max(r for _, r, *_ in spec["boxes"].values())
    width, height = 20 + columns * bw + (columns - 1) * gx, 20 + rows * bh + (rows - 1) * gy
    text = "\n".join(f"{spec['boxes'][a][2].replace(chr(10), ' ')} {s} "
                     f"{spec['boxes'][b][2].replace(chr(10), ' ')}" for a, b, s, _ in spec["edges"])
    _display(_svg(width, height, defs + "".join(parts), f"Diagrama: {name}", int(width)), text)


# --- the list of limits ------------------------------------------------------------------

KINDS = {"cualquier modelo": BLUE, "nuestros modelos": ORANGE, "nuestra infraestructura": PURPLE}
FIXES = {"cualquier modelo": "Software: fuentes, grafo, herramientas; compilar y probar fuera del modelo",
         "nuestros modelos": "Modelos más capaces para programar",
         "nuestra infraestructura": "Capacidad, acceso a las fuentes e integración en el editor"}


class Limits:
    """The list of limits, which grows during the session, each with its kind: "cualquier
    modelo", "nuestros modelos" or "nuestra infraestructura"."""

    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []

    def add(self, text: str, kind: str) -> None:
        if kind not in KINDS:
            raise ValueError(f"kind {kind!r}: use one of {', '.join(KINDS)}")
        if (text, kind) not in self.items:               # running a cell again adds nothing
            self.items.append((text, kind))
        _display(f'<div style="border-left:4px solid {KINDS[kind]};padding:4px 10px;margin:6px 0;'
                 f'background:rgba(128,128,128,.08)"><b>+ lista de límites</b> · {escape(text)} '
                 f'<span style="color:{KINDS[kind]};white-space:nowrap">({escape(kind)})</span></div>',
                 f"+ lista de límites: {text} ({kind})")

    def show(self) -> None:
        """The list in three columns, with what fixes each one."""
        cols, lines = [], []
        for kind, colour in KINDS.items():
            items = [t for t, k in self.items if k == kind]
            cols.append(f'<div style="border-top:4px solid {colour};padding:8px 10px;'
                        f'background:rgba(128,128,128,.06)"><b>De {escape(kind)}</b> '
                        f'<span style="opacity:.7">({len(items)})</span><ul style="padding-left:18px">'
                        + "".join(f"<li>{escape(t)}</li>" for t in items)
                        + f'</ul><div style="font-size:13px"><b style="color:{colour}">Lo arregla:</b> '
                          f'{escape(FIXES[kind])}</div></div>')
            lines += [f"De {kind} ({len(items)}):"] + [f"  - {t}" for t in items]
            lines += [f"  Lo arregla: {FIXES[kind]}", ""]
        _display(f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));'
                 f'gap:12px">{"".join(cols)}</div>', "\n".join(lines).rstrip())
