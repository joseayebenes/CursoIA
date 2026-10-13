#!/usr/bin/env python3
"""What each model of the server supports, to know which demos of the notebook work.

    python scripts/check_gateway.py                         # the profile's three models
    python scripts/check_gateway.py gemma-4 gpt-oss-120b    # these models

For each model: a plain answer, logprobs, several answers in one request (n), tools (the
call and the answer with its result), JSON with a schema, and reasoning_effort "none" and
"low". Then the embeddings, including the trap of the similar IDs. About 8 requests per
model, always live (never from the cache) and spaced by CURSO_RPM.

The result goes to resultados/<profile>.md and resultados/<profile>.json, without the URL
or the key. The configuration is that of curso.llm (CURSO_PROFILE, CURSO_BASE_URL...).
"""
from __future__ import annotations

import difflib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openai

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from curso import data, llm  # noqa: E402

DEFAULT_MODELS = {
    "gateway": ["gemma-4", "gpt-oss-120b", "devstral"],
    "openrouter": ["google/gemma-4-26b-a4b-it", "openai/gpt-oss-120b",
                   "mistralai/devstral-2512"],
}

SRS_0004 = ("SRS-0004: The software shall delete a track within 2 s when no report has "
            "been received for that track for 10 s.")

GET_REQUIREMENT = {
    "type": "function",
    "function": {
        "name": "get_requirement",
        "description": "The official text of a requirement, by its ID.",
        "parameters": {
            "type": "object",
            "properties": {"id": {"type": "string", "description": "e.g. SRS-0001"}},
            "required": ["id"],
        },
    },
}

REQUIREMENT_SCHEMA = {
    "type": "object",
    "properties": {"id": {"type": "string"}, "seconds": {"type": "number"}},
    "required": ["id", "seconds"],
    "additionalProperties": False,
}


def call(**request):
    """One live request (never from the cache): the response and the seconds it took."""
    return llm.send(lambda: llm.client().chat.completions.create(**request))


def reasoning_tokens(response) -> int:
    details = response.usage.completion_tokens_details if response.usage else None
    return (details.reasoning_tokens or 0) if details else 0


def text_of(response) -> str:
    """The answer, with the Unicode spaces some models use (2\u202fs) as plain spaces."""
    text = response.choices[0].message.content or ""
    return re.sub(r"[\u00a0\u2009\u202f]", " ", text).strip()


# --- checks: each returns (ok, note) -----------------------------------------------------

def check_chat(model):
    r, t = call(model=model, max_tokens=1000,
                messages=[{"role": "user", "content": "Reply with exactly one word: OK"}])
    note = f"{text_of(r)[:20]!r}, {t:.1f} s, {r.usage.prompt_tokens}+{r.usage.completion_tokens} tokens"
    if reasoning_tokens(r) or llm.reasoning(r):
        note += f", reasons by default ({reasoning_tokens(r)} reasoning tokens)"
    return "OK" in text_of(r).upper(), note


def check_logprobs(model):
    r, _ = call(model=model, max_tokens=1000, temperature=0, logprobs=True, top_logprobs=5,
                messages=[{"role": "user", "content": "Complete with one number, nothing "
                           "else: The software shall delete a track within"}])
    logprobs = r.choices[0].logprobs
    if not logprobs or not logprobs.content:
        return False, f"no logprobs in the answer {text_of(r)[:30]!r}"
    first = logprobs.content[0]
    alternatives = ", ".join(f"{a.token!r} {math.exp(a.logprob):.2f}"
                             for a in first.top_logprobs or [])
    return bool(first.top_logprobs), f"first token {first.token!r}; alternatives: {alternatives}"


def check_n(model):
    r, _ = call(model=model, max_tokens=1000, temperature=1.0, n=3,
                messages=[{"role": "user", "content": "Name one colour. One word."}])
    answers = [(c.message.content or "").strip()[:15] for c in r.choices]
    return len(r.choices) == 3, f"{len(r.choices)} answers: {', '.join(answers)}"


def check_tools(model):
    messages = [{"role": "user", "content": "What does requirement SRS-0004 say? Use the tool."}]
    r, _ = call(model=model, max_tokens=2000, tools=[GET_REQUIREMENT], messages=messages)
    message = r.choices[0].message
    if not message.tool_calls:
        return False, f"no tool call; it answered {text_of(r)[:60]!r}"
    tool_call = message.tool_calls[0]
    args = json.loads(tool_call.function.arguments or "{}")
    messages.append({"role": "assistant", "content": message.content or "",
                     "tool_calls": [{"id": tool_call.id, "type": "function",
                                     "function": {"name": tool_call.function.name,
                                                  "arguments": tool_call.function.arguments}}]})
    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": SRS_0004})
    r2, _ = call(model=model, max_tokens=2000, tools=[GET_REQUIREMENT], messages=messages)
    uses_result = re.search(r"\b2 ?(s\b|sec)", text_of(r2)) is not None
    ok = tool_call.function.name == "get_requirement" and args.get("id") == "SRS-0004"
    return ok and uses_result, (f"called {tool_call.function.name}({args}); "
                                f"the answer uses the result: {'yes' if uses_result else 'no'}")


def check_json_schema(model):
    r, _ = call(model=model, max_tokens=2000,
                response_format={"type": "json_schema", "json_schema": {
                    "name": "requirement", "schema": REQUIREMENT_SCHEMA, "strict": True}},
                messages=[{"role": "user", "content": "Extract the requirement ID and its "
                           f"time limit in seconds: {SRS_0004}"}])
    text = text_of(r)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return False, f"not JSON: {text[:60]!r}"
    return obj.get("id") == "SRS-0004" and obj.get("seconds") == 2, text[:80]


def check_reasoning(model, effort):
    r, t = call(model=model, max_tokens=4000, reasoning_effort=effort,
                messages=[{"role": "user", "content": "A track is deleted at most 2 s after "
                           "it has gone 10 s without reports. At most how many seconds pass "
                           "from its last report to its deletion? One number."}])
    answer = text_of(r)
    return "12" in answer, (f"{answer[:20]!r}, {reasoning_tokens(r)} reasoning tokens, "
                            f"{t:.1f} s")


CHECKS = [
    ("plain answer", check_chat),
    ("logprobs", check_logprobs),
    ("n = 3", check_n),
    ("tools", check_tools),
    ("json_schema", check_json_schema),
    ("reasoning none", lambda m: check_reasoning(m, "none")),
    ("reasoning low", lambda m: check_reasoning(m, "low")),
]


def run(check, model) -> dict:
    try:
        ok, note = check(model)
    except openai.APIStatusError as e:
        ok, note = False, f"HTTP {e.status_code}: {e.message}"
    except Exception as e:  # noqa: BLE001 - a failed check must not stop the others
        ok, note = False, llm.diagnose(e) or f"{type(e).__name__}: {e}"
    return {"ok": ok, "note": " ".join(str(note).split())[:200]}


# --- embeddings --------------------------------------------------------------------------

def check_embeddings() -> dict:
    s = llm.settings()
    requirements = {r["id"]: f"{r['id']}: {r['text']}" for r in data.requirements()}
    texts = ["¿Cuánto tarda en borrarse una traza?",
             "The worst-case time from the moment a track becomes stale to its removal "
             "from the display is below 1.1 s.",
             "The software shall raise an alarm on the HMI within 500 ms.",
             "Receta de tortilla de patatas",
             "SRS-0004", *requirements.values()]
    try:
        response, _ = llm.send(lambda: llm.client().embeddings.create(model=s.embed_model,
                                                                      input=texts))
    except openai.APIStatusError as e:
        return {"model": s.embed_model, "ok": False, "note": f"HTTP {e.status_code}: {e.message}"}
    except Exception as e:  # noqa: BLE001
        return {"model": s.embed_model, "ok": False,
                "note": llm.diagnose(e) or f"{type(e).__name__}: {e}"}
    v = np.array([d.embedding for d in sorted(response.data, key=lambda d: d.index)])
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    question = v[0] @ v[1:4].T
    by_id = v[4] @ v[5:].T
    ids = list(requirements)
    ranking = [f"{ids[i]} {by_id[i]:.3f}" for i in np.argsort(-by_id)[:3]]
    return {
        "model": s.embed_model, "ok": True, "dimensions": int(v.shape[1]),
        "multilingual": {"stale track (en)": round(float(question[0]), 3),
                         "alarm (en)": round(float(question[1]), 3),
                         "recipe (es)": round(float(question[2]), 3)},
        "closest_to_SRS-0004": ranking,
        "note": (f"{v.shape[1]} dimensions; the Spanish question is closer to the stale "
                 f"track sentence: {'yes' if question[0] > question[1:].max() else 'NO'}; "
                 f"'SRS-0004' alone is closest to {', '.join(ranking)}"),
    }


# --- report ------------------------------------------------------------------------------

def report(result: dict) -> str:
    models = list(result["models"])
    lines = [f"# What each model supports: {result['profile']}", "",
             f"Checked on {result['date']} with `scripts/check_gateway.py`.", ""]
    if result.get("offered") is not None:
        lines += [f"Models offered by the server: {', '.join(result['offered'])}", ""]
    lines += ["| Check | " + " | ".join(f"`{m}`" for m in models) + " |",
              "|---" * (len(models) + 1) + "|"]
    for name, _ in CHECKS:
        cells = []
        for m in models:
            r = result["models"][m].get(name)
            cells.append("—" if r is None else ("yes" if r["ok"] else "**no**"))
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    for m in models:
        lines += ["", f"## `{m}`", ""]
        if "missing" in result["models"][m]:
            lines.append(f"- {result['models'][m]['missing']}")
            continue
        lines += [f"- {name}: {'yes' if r['ok'] else 'NO'}, {r['note']}"
                  for name, r in result["models"][m].items()]
    e = result["embeddings"]
    lines += ["", f"## Embeddings: `{e['model']}`", "", f"- {'yes' if e['ok'] else 'NO'}, {e['note']}"]
    if e.get("multilingual"):
        lines.append("- cosine with '¿Cuánto tarda en borrarse una traza?': "
                     + ", ".join(f"{k} {v}" for k, v in e["multilingual"].items()))
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    s = llm.settings()
    models = argv or DEFAULT_MODELS[s.profile]
    result = {"profile": s.profile,
              "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
              "offered": None, "models": {}}
    print(llm.describe())
    try:
        offered = llm.models()
    except openai.NotFoundError:
        offered = []                       # some servers do not list their models
    except Exception as e:  # noqa: BLE001 - without a connection there is nothing to check
        print(f"\ncannot reach the server: {type(e).__name__}: {str(e)[:200]}", file=sys.stderr)
        if llm.diagnose(e):
            print(f"  -> {llm.diagnose(e)}", file=sys.stderr)
        return 1
    if s.profile == "gateway":
        result["offered"] = offered
        print("models offered:", ", ".join(offered) or "(none listed)")
    for model in models:
        if offered and model not in offered:
            close = difflib.get_close_matches(model, offered, n=3, cutoff=0.3)
            result["models"][model] = {"missing": f"not offered; similar: {', '.join(close) or '-'}"}
            print(f"\n{model}: not offered (similar: {', '.join(close) or '-'})")
            continue
        print(f"\n{model}")
        result["models"][model] = {}
        for name, check in CHECKS:
            r = run(check, model)
            result["models"][model][name] = r
            print(f"  {name:15} {'yes' if r['ok'] else 'NO ':3}  {r['note']}")
    print("\nembeddings")
    result["embeddings"] = check_embeddings()
    print("  " + result["embeddings"]["note"])
    out = Path(__file__).resolve().parent.parent / "resultados"
    out.mkdir(exist_ok=True)
    (out / f"{s.profile}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                          "utf-8")
    (out / f"{s.profile}.md").write_text(report(result), "utf-8")
    print(f"\nwritten: resultados/{s.profile}.md and .json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
