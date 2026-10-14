"""Builds the notebook preview page from cells.json (the real outputs of run.py)."""
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELLS = json.loads((HERE / "cells.json").read_text("utf-8"))
OUT = HERE / "notebook-curso-ia.html"

BLOCKS = {
    "0": ("Gancho", "0–5", "Las dos caras del modelo en cinco minutos."),
    "1": ("Qué es un modelo de lenguaje", "5–22",
          "Por qué inventa: una función de texto a texto, sin memoria, que da probabilidades."),
    "2": ("Nuestros modelos", "22–32", "Qué tenemos y por qué gemma-4 por defecto."),
    "3": ("Que sepa lo nuestro", "32–55", "Cómo se le da el conocimiento que no tiene."),
    "4": ("Preguntar con fuentes", "65–78", "Responder solo con lo encontrado, citando."),
    "5": ("Lo que no es semántico", "78–88", "Trazabilidad sin depender de que el modelo acierte."),
    "6": ("Agentes", "88–103", "Un agente es un bucle. Qué le pasa con Ada."),
    "7": ("Límites y hacia dónde ir", "103–120", "Qué usar ya, qué no y qué pedir."),
}
KINDS = {"cualquier modelo": "any", "nuestros modelos": "ours", "nuestra infraestructura": "infra"}
FIXES = {"any": "Software: fuentes, grafo, herramientas; compilar y probar fuera del modelo",
         "ours": "Modelos más capaces para programar",
         "infra": "Capacidad, acceso a las fuentes e integración en el editor"}
GROUPS = {"manual_operador.md": ("Manual (es)", "g1"), "tms_sdd.md": ("Diseño (en)", "g2"),
          "requisitos": ("Requisitos (en)", "g3"), "pregunta": ("La pregunta", "g4")}

e = html.escape


def collapsible(inner: str, text: str, lines: int = 22) -> str:
    if text.count("\n") <= lines:
        return inner
    return f'<div class="fold">{inner}<button class="more" type="button">Ver todo</button></div>'


def render_output(o: dict) -> str:
    t = o["type"]
    if t in ("stream", "result"):
        text = o["text"].rstrip("\n")
        return collapsible(f'<pre class="out-text">{e(text)}</pre>', text)
    if t == "error":
        return f'<pre class="out-text out-error">{e(o["text"])}</pre>'
    if t == "table":
        head = "".join(f"<th>{e(c)}</th>" for c in o["columns"])
        rows = "".join("<tr>" + "".join(f"<td>{e(v)}</td>" for v in r) + "</tr>" for r in o["rows"])
        return f'<div class="scroll"><table class="out-table"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    if t == "bars":
        top = max(v for _, v in o["items"])
        items = "".join(
            f'<div class="bar-row"><code class="bar-label">«{e(label)}»</code>'
            f'<div class="bar-track"><div class="bar-fill{" lead" if v == top else ""}" style="width:{v * 100:.1f}%"></div></div>'
            f'<span class="bar-value">{v * 100:.1f} %</span></div>' for label, v in o["items"])
        return f'<div class="bars" role="img" aria-label="Probabilidad de cada siguiente token">{items}</div>'
    if t == "scatter":
        return render_scatter(o["points"])
    if t == "columns":
        cards = "".join(
            f'<article class="model-card"><header><span class="model-name">{e(it["title"])}</span>'
            f'<span class="model-time">{it["seconds"]:.1f} s</span></header>'
            f'<pre class="out-text">{e(it["text"].strip())}</pre></article>' for it in o["items"])
        return f'<div class="model-grid">{cards}</div>'
    if t == "step":
        args = ", ".join(f"{k}={v!r}" for k, v in o["args"].items())
        result = o["result"].replace("\\n", "\n")
        return (f'<details class="step"><summary><span class="step-arrow">→</span>'
                f'<code>{e(o["name"])}({e(args)})</code></summary>'
                f'<pre class="out-text">{e(result)}</pre></details>')
    if t == "mermaid":
        text = o["text"] + ("\n  classDef target stroke-width:3px\n  classDef req stroke-dasharray:4 3"
                            "\n  classDef test stroke-dasharray:1 3")
        return f'<div class="scroll"><pre class="mermaid">{e(text)}</pre></div>'
    if t == "limit":
        k = KINDS[o["kind"]]
        return (f'<div class="limit-chip k-{k}"><span class="limit-plus">+ lista de límites</span>'
                f'<span class="limit-text">{e(o["text"])}</span><span class="limit-kind">{e(o["kind"])}</span></div>')
    if t == "limits":
        cols = []
        for kind, k in KINDS.items():
            items = "".join(f"<li>{e(text)}</li>" for text, kk in o["items"] if kk == kind)
            n = sum(1 for _, kk in o["items"] if kk == kind)
            cols.append(f'<section class="limit-col k-{k}"><h4>De {e(kind)} <span class="count">{n}</span></h4>'
                        f'<ul>{items}</ul><p class="fix"><span>Lo arregla</span>{e(FIXES[k])}</p></section>')
        return f'<div class="limit-board">{"".join(cols)}</div>'
    return f'<pre class="out-text">{e(json.dumps(o, ensure_ascii=False))}</pre>'


def render_scatter(points):
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    w, h, pad = 640, 380, 34
    def sx(x): return pad + (x - min(xs)) / (max(xs) - min(xs)) * (w - 2 * pad)
    def sy(y): return h - pad - (y - min(ys)) / (max(ys) - min(ys)) * (h - 2 * pad)
    labelled = {"3 Las trazas", "4 Borrar una traza", "4.4 Purge of stale tracks", "SRS-0004",
                "5 Alarmas", "SRS-0007"}
    dots, labels = [], []
    for p in points:
        cls = GROUPS[p["group"]][1]
        x, y = sx(p["x"]), sy(p["y"])
        r = 7 if p["group"] == "pregunta" else 4.5
        dots.append(f'<circle class="dot {cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"><title>{e(p["label"])}</title></circle>')
        if p["group"] == "pregunta" or p["label"] in labelled:
            anchor = "end" if x > w * 0.7 else "start"
            dx = -9 if anchor == "end" else 9
            weight = ' font-weight="600"' if p["group"] == "pregunta" else ""
            labels.append(f'<text class="dot-label" x="{x + dx:.1f}" y="{y + 4:.1f}" text-anchor="{anchor}"{weight}>{e(p["label"])}</text>')
    legend = "".join(f'<span class="legend-item"><span class="swatch {c}"></span>{e(n)}</span>'
                     for n, c in GROUPS.values())
    return (f'<figure class="scatter"><div class="scroll"><svg viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="Mapa en dos dimensiones de los trozos y la pregunta">'
            f'<rect class="plot-bg" x="0" y="0" width="{w}" height="{h}" rx="6"/>'
            f'{"".join(dots)}{"".join(labels)}</svg></div>'
            f'<figcaption>{legend}<span class="legend-note">Pasa el ratón por un punto para ver su sección.</span></figcaption></figure>')


TRAFFIC = [
    ("go", "Verde: útil ya", ["Explicar código ajeno", "Buscar y preguntar a la documentación, con citas",
                               "Resumir y redactar"]),
    ("wait", "Ámbar: con revisión", ["Escribir pruebas y código pequeño, un encargo cada vez",
                                      "Comprobar un requisito contra un documento", "Revisar un cambio"]),
    ("stop", "Rojo: nunca solo", ["Fiarse de «compila» o «pasa» sin haberlo ejecutado",
                                   "Dejarle arreglar la prueba que falla", "Encargos grandes sin supervisión"]),
]

DIAGRAM = """flowchart LR
  Q(["Pregunta"]) --> RW["Reescribir con glosario"]
  RW --> H{{"Búsqueda híbrida (RRF)"}}
  DOC[("Requisitos, diseño, manual")] --> T["Trozos por sección"]
  T --> ID["IDs exactos"] & V["Vectores"] & B["BM25"]
  ID & V & B --> H
  H --> F["Fuentes numeradas"] --> M["Modelo"] --> A(["Respuesta con citas"])
  ADA[("Código Ada")] --> G["Grafo: Req, llamadas"]
  G --> TR["Traza, impacto, huecos"]
  AG["Agente: un bucle"] --> TOOLS["search, get_requirement, read_file, trace"]
  TOOLS -.-> H
  TOOLS -.-> G
  TOOLS -.-> ED["El editor, por MCP"]"""


def render_cell(c: dict) -> str:
    k = c["kind"]
    if k == "md":
        return f'<div class="cell md">{c["src"]}</div>'
    if k == "chat":
        return (f'<aside class="cell chat"><span class="chat-label">Pregunta al chat</span>'
                f'<p>{e(c["src"])}</p></aside>')
    if k == "traffic":
        rows = "".join(f'<section class="light {cls}"><h4><span class="lamp"></span>{e(title)}</h4>'
                       f'<ul>{"".join(f"<li>{e(i)}</li>" for i in items)}</ul></section>'
                       for cls, title, items in TRAFFIC)
        return f'<div class="cell md"><h2>El semáforo</h2><div class="traffic">{rows}</div></div>'
    if k == "diagram":
        return f'<div class="cell md"><div class="scroll"><pre class="mermaid">{e(DIAGRAM)}</pre></div></div>'
    outputs = "".join(render_output(o) for o in c.get("outputs", []))
    has_out = bool(c.get("outputs"))
    return (f'<div class="cell code"><div class="in"><span class="prompt">[{c["n"]}]</span>'
            f'<pre class="src"><code class="language-python">{e(c["src"])}</code></pre></div>'
            + (f'<div class="outs"><span class="prompt out-prompt" aria-hidden="true"></span><div class="out-body">{outputs}</div></div>' if has_out else "")
            + "</div>")


def build():
    body, current = [], None
    for c in CELLS:
        if c["block"] != current:
            if current is not None:
                body.append("</section>")
            if c["block"] == "4":
                body.append('<div class="break" id="descanso"><span>Descanso</span><span class="mins">min 55–65</span></div>')
            current = c["block"]
            title, mins, goal = BLOCKS[current]
            body.append(f'<section class="block" id="b{current}" data-block="{current}">'
                        f'<header class="block-head"><span class="block-num">Bloque {current}</span>'
                        f'<h2 class="block-title">{e(title)}</h2><span class="mins">min {mins}</span>'
                        f'<p class="block-goal">{e(goal)}</p></header>')
        body.append(render_cell(c))
    body.append("</section>")
    rail = "".join(f'<li><a href="#b{b}" data-block="{b}"><span class="rail-num">{b}</span>'
                   f'<span class="rail-title">{e(t)}</span><span class="rail-mins">{m}</span></a></li>'
                   + ('<li class="rail-break"><span>Descanso</span><span class="rail-mins">55–65</span></li>' if b == "3" else "")
                   for b, (t, m, _) in BLOCKS.items())
    n_limits = sum(1 for c in CELLS for o in c.get("outputs", []) if o["type"] == "limit")
    page = TEMPLATE.replace("{{RAIL}}", rail).replace("{{BODY}}", "\n".join(body)).replace(
        "{{NLIMITS}}", str(n_limits)).replace("{{NCELLS}}", str(sum(1 for c in CELLS if c["kind"] == "code")))
    OUT.write_text(page, "utf-8")
    print(OUT, len(page) // 1024, "KB")


TEMPLATE = (HERE / "template.html").read_text("utf-8")

if __name__ == "__main__":
    build()
