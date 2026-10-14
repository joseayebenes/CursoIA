"""Runs the draft cells like a notebook kernel and saves every output to cells.json.

    python run.py            (with CURSO_PROFILE and the key in the environment)
"""
import ast
import json
import math
import pprint
import sys
import traceback
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))

from cells import CELLS  # noqa: E402

OUT: list = []


class Stream:
    def write(self, text):
        if not text:
            return 0
        if OUT and OUT[-1]["type"] == "stream":
            OUT[-1]["text"] += text
        else:
            OUT.append({"type": "stream", "text": text})
        return len(text)

    def flush(self):
        pass


def _short(value, limit=420):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + " …"


def table(rows):
    columns = list(rows[0].keys())
    OUT.append({"type": "table", "columns": columns,
                "rows": [[str(r[c]) for c in columns] for r in rows]})


def bars(items):
    OUT.append({"type": "bars", "items": [[str(label), float(v)] for label, v in items]})


def scatter(xy, labels, groups):
    OUT.append({"type": "scatter", "points": [
        {"x": float(x), "y": float(y), "label": label, "group": group}
        for (x, y), label, group in zip(xy, labels, groups)]})


def side_by_side(answers):
    OUT.append({"type": "columns", "items": [
        {"title": k, "text": v[0], "seconds": v[1]} for k, v in answers.items()]})


def step(name, args, result):
    OUT.append({"type": "step", "name": name, "args": args, "result": _short(result)})


def tool(name, doc, **params):
    return {"type": "function", "function": {
        "name": name, "description": doc,
        "parameters": {"type": "object", "required": list(params),
                       "properties": {p: {"type": "string", "description": d}
                                      for p, d in params.items()}}}}


def graph(subs, name):
    """Mermaid of who calls `name`, up to the top, with the requirements of each one."""
    by_name = {s["name"]: s for s in subs}
    seen, todo = {name}, [name]
    while todo:
        n = todo.pop()
        for s in subs:
            if n in s["calls"] and s["name"] not in seen:
                seen.add(s["name"])
                todo.append(s["name"])
    node = {n: f"n{i}" for i, n in enumerate(sorted(seen))}
    lines = ["flowchart RL"]
    for n in sorted(seen):
        style = ":::target" if n == name else (":::test" if by_name[n]["test"] else "")
        lines.append(f'  {node[n]}["{n}"]{style}')
    for n in sorted(seen):
        for callee in sorted(by_name[n]["calls"] & seen):
            lines.append(f"  {node[n]} --> {node[callee]}")
    reqs = sorted({r for n in seen for r in by_name[n]["reqs"]})
    for r in reqs:
        lines.append(f'  {r.replace("-", "_")}(["{r}"]):::req')
    for n in sorted(seen):
        for r in by_name[n]["reqs"]:
            lines.append(f"  {r.replace('-', '_')} -.- {node[n]}")
    OUT.append({"type": "mermaid", "text": "\n".join(lines)})


class Limits:
    def __init__(self):
        self.items = []

    def add(self, text, kind):
        self.items.append([text, kind])
        OUT.append({"type": "limit", "text": text, "kind": kind})

    def show(self):
        OUT.append({"type": "limits", "items": self.items})


show = types.ModuleType("curso.show")
for f in (table, bars, scatter, side_by_side, step, tool, graph, Limits):
    setattr(show, f.__name__, f)
sys.modules["curso.show"] = show


def run_cell(src, ns):
    tree = ast.parse(src)
    last = tree.body[-1] if tree.body and isinstance(tree.body[-1], ast.Expr) else None
    if last is not None:
        tree.body = tree.body[:-1]
    exec(compile(tree, "<cell>", "exec"), ns)
    if last is not None:
        value = eval(compile(ast.Expression(last.value), "<cell>", "eval"), ns)
        if value is not None:
            OUT.append({"type": "result", "text": pprint.pformat(value, width=88, sort_dicts=False)})


def main():
    ns = {"__name__": "__notebook__"}
    count = 0
    results = []
    stdout = sys.stdout
    for cell in CELLS:
        item = dict(cell, src=cell["src"].strip("\n"))
        if cell["kind"] == "code":
            count += 1
            item["n"] = count
            OUT.clear()
            sys.stdout = Stream()
            try:
                run_cell(item["src"], ns)
            except Exception:  # noqa: BLE001 - shown as the cell's output, like Jupyter
                OUT.append({"type": "error", "text": traceback.format_exc(limit=3)})
            finally:
                sys.stdout = stdout
            item["outputs"] = json.loads(json.dumps(OUT, default=str))
            print(f"[{count}] {item['src'].splitlines()[0][:70]}  -> "
                  f"{[o['type'] for o in OUT]}", flush=True)
            if any(o["type"] == "error" for o in OUT):
                print(OUT[-1]["text"], flush=True)
        results.append(item)
    text = json.dumps(results, ensure_ascii=False, indent=1)
    text = text.replace(str(Path.home()), "~")
    (HERE / "cells.json").write_text(text, "utf-8")


if __name__ == "__main__":
    main()
