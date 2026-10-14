#!/usr/bin/env python3
"""Runs the notebook from top to bottom in a real kernel and saves its outputs in place,
like "Run All" and "Save", from the command line.

    python scripts/run_notebook.py                        # curso-ia.ipynb
    CURSO_CACHE=refresh python scripts/run_notebook.py    # every model call again

The configuration is that of curso.llm (CURSO_PROFILE, CURSO_BASE_URL...): the day before
the session, against the gateway, so that the session runs from the cache. Unlike "Run
All", it does not stop at an error: it runs every cell, lists the errors at the end and
exits with 1. Only needs ipykernel (jupyter_client comes with it).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from jupyter_client.manager import start_new_kernel

ROOT = Path(__file__).resolve().parent.parent


def lines(text: str) -> list[str]:
    """A text as the notebook format keeps it: a list of lines, each with its newline."""
    return text.splitlines(keepends=True)


def private(value):
    """The outputs without the user's home folder."""
    text = json.dumps(value, ensure_ascii=False)
    for home in {str(Path.home()), str(Path.home()).replace("\\", "\\\\")}:
        text = text.replace(home, "~")
    return json.loads(text)


def run(kc, source: str) -> tuple[list[dict], int | None]:
    """Executes one cell: its outputs in the notebook format and its execution count."""
    msg_id = kc.execute(source, store_history=True, allow_stdin=False)
    outputs: list[dict] = []
    while True:
        msg = kc.get_iopub_msg(timeout=None)
        if msg["parent_header"].get("msg_id") != msg_id:
            continue
        kind, content = msg["msg_type"], msg["content"]
        if kind == "status" and content["execution_state"] == "idle":
            break
        if kind == "stream":
            if outputs and outputs[-1]["output_type"] == "stream" \
                    and outputs[-1]["name"] == content["name"]:
                outputs[-1]["text"] += content["text"]
            else:
                outputs.append({"output_type": "stream", "name": content["name"],
                                "text": content["text"]})
        elif kind in ("display_data", "execute_result"):
            out = {"output_type": kind, "data": content["data"],
                   "metadata": content.get("metadata", {})}
            if kind == "execute_result":
                out["execution_count"] = content["execution_count"]
            outputs.append(out)
        elif kind == "error":
            outputs.append({"output_type": "error", "ename": content["ename"],
                            "evalue": content["evalue"], "traceback": content["traceback"]})
        elif kind == "clear_output":
            outputs.clear()
    reply = kc.get_shell_msg(timeout=None)
    while reply["parent_header"].get("msg_id") != msg_id:
        reply = kc.get_shell_msg(timeout=None)
    for out in outputs:                    # the notebook format keeps texts as lines
        if "text" in out:
            out["text"] = lines(out["text"])
        for mime, value in out.get("data", {}).items():
            if isinstance(value, str) and (mime.startswith("text/") or mime.endswith("+xml")):
                out["data"][mime] = lines(value)
    return private(outputs), reply["content"].get("execution_count")


def main(argv: list[str]) -> int:
    path = Path(argv[0]) if argv else ROOT / "curso-ia.ipynb"
    nb = json.loads(path.read_text("utf-8"))
    km, kc = start_new_kernel(kernel_name="python3", cwd=str(path.resolve().parent))
    errors = []
    try:
        cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
        for n, cell in enumerate(cells, 1):
            source = "".join(cell["source"])
            first = source.strip().splitlines()[0] if source.strip() else ""
            t0 = time.perf_counter()
            cell["outputs"], cell["execution_count"] = run(kc, source)
            took = time.perf_counter() - t0
            print(f"[{n}/{len(cells)}] {took:5.1f} s  {first[:70]}", flush=True)
            for out in cell["outputs"]:
                if out["output_type"] == "error":
                    errors.append((n, first))
                    print(re.sub(r"\x1b\[[0-9;]*m", "", "\n".join(out["traceback"][-3:])),
                          flush=True)
    finally:
        kc.stop_channels()
        km.shutdown_kernel(now=True)
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"\nsaved {path.name}" + (f"; errors in {len(errors)} cells: "
                                     + ", ".join(f"[{n}]" for n, _ in errors) if errors else ""))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
