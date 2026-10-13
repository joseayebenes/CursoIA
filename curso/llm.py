"""Access to the course models: one OpenAI-compatible client, a request limit and a disk
cache.

Every model call in the notebook goes through chat() or embed(). A call already made is
read from cache/ and costs nothing, so the session depends neither on the gateway being up,
nor on its quota, nor on the model answering the same thing twice.

Configuration, from the environment only (the API key never goes in a file):

    CURSO_PROFILE      gateway (default) or openrouter (for development)
    CURSO_BASE_URL     the API URL, ending in /v1 (preset for openrouter)
    CURSO_API_KEY      the API key (with openrouter, OPENROUTER_API_KEY also works)
    CURSO_MODEL        the chat model (gateway: gemma-4)
    CURSO_EMBED_MODEL  the embeddings model (gateway: embeddinggemma)
    CURSO_RPM          requests per minute at most (default 28)
    CURSO_CA_CERT      "system" (default): the system certificate store, where the
                       corporate root is; a PEM file; or "certifi"
    CURSO_CACHE        on (default): use the cache; refresh: call again and overwrite;
                       off: no cache
    HTTPS_PROXY, NO_PROXY  the proxy, read by httpx as usual
"""
from __future__ import annotations

import hashlib
import json
import os
import ssl
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx
import numpy as np
from openai import OpenAI
from openai.types import CreateEmbeddingResponse
from openai.types.chat import ChatCompletion

ROOT = Path(__file__).resolve().parent.parent

PROFILES = {
    "gateway": {"base_url": "", "model": "gemma-4", "embed_model": "embeddinggemma"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1",
                   "model": "google/gemma-4-26b-a4b-it", "embed_model": "baai/bge-m3"},
}

last: dict = {}
"""The last call: seconds it took (when it was really made), whether it came from the
cache, and the token usage."""


@dataclass(frozen=True)
class Settings:
    profile: str
    base_url: str
    api_key: str
    model: str
    embed_model: str
    rpm: float
    ca_cert: str
    cache: str
    cache_dir: Path


def settings() -> Settings:
    """The configuration, read from the environment on every call."""
    profile = os.environ.get("CURSO_PROFILE", "gateway")
    if profile not in PROFILES:
        raise ValueError(f"CURSO_PROFILE={profile!r}: use one of {', '.join(PROFILES)}")
    preset = PROFILES[profile]
    key = os.environ.get("CURSO_API_KEY", "")
    if not key and profile == "openrouter":
        key = os.environ.get("OPENROUTER_API_KEY", "")
    return Settings(
        profile=profile,
        base_url=os.environ.get("CURSO_BASE_URL", preset["base_url"]).rstrip("/"),
        api_key=key,
        model=os.environ.get("CURSO_MODEL", preset["model"]),
        embed_model=os.environ.get("CURSO_EMBED_MODEL", preset["embed_model"]),
        rpm=float(os.environ.get("CURSO_RPM", "28")),
        ca_cert=os.environ.get("CURSO_CA_CERT", "system"),
        cache=os.environ.get("CURSO_CACHE", "on"),
        cache_dir=Path(os.environ.get("CURSO_CACHE_DIR", ROOT / "cache")),
    )


# --- client ------------------------------------------------------------------------------

_clients: dict[tuple, OpenAI] = {}


def _verify(ca_cert: str):
    if ca_cert == "system":
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if ca_cert == "certifi":
        return True
    return ssl.create_default_context(cafile=ca_cert)


def client() -> OpenAI:
    """The OpenAI client of the current configuration."""
    s = settings()
    key = (s.base_url, s.api_key, s.ca_cert)
    if key not in _clients:
        if not s.base_url:
            raise RuntimeError("CURSO_BASE_URL is not set: the gateway URL, ending in /v1")
        if not s.api_key:
            raise RuntimeError("CURSO_API_KEY is not set, and the call is not in the cache")
        http = httpx.Client(verify=_verify(s.ca_cert),
                            timeout=httpx.Timeout(300.0, connect=20.0))
        _clients[key] = OpenAI(base_url=s.base_url, api_key=s.api_key,
                               http_client=http, max_retries=5)
    return _clients[key]


def models() -> list[str]:
    """The model names the server offers."""
    return sorted(m.id for m in client().models.list())


# --- request limit -----------------------------------------------------------------------

class _Limiter:
    """Spaces the requests so that there are at most rpm per minute."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self, rpm: float) -> None:
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next)
            self._next = start + 60.0 / rpm
        if start > now:
            time.sleep(start - now)


limiter = _Limiter()


# --- cache -------------------------------------------------------------------------------

def _key(*parts) -> str:
    blob = json.dumps(parts, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:20]


def _read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text("utf-8"))
    except FileNotFoundError:
        return None


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- chat --------------------------------------------------------------------------------

def chat(messages: str | list[dict], *, model: str | None = None, **params) -> ChatCompletion:
    """One chat request, from the cache if it was already made.

    messages is a list of {"role", "content"} or just the text of the user message. params
    are those of the API: temperature, max_tokens, logprobs, top_logprobs, n, tools,
    response_format, reasoning_effort... (extra_body for anything the SDK does not know).
    """
    s = settings()
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    # an assistant message taken from a response (an agent loop) goes back as a dict
    messages = [m.model_dump(mode="json", exclude_none=True) if hasattr(m, "model_dump") else m
                for m in messages]
    payload = {"model": model or s.model, "messages": messages, **params}
    path = s.cache_dir / s.profile / "chat" / f"{_key(s.profile, payload)}.json"
    cached = _read(path) if s.cache == "on" else None
    if cached:
        response = ChatCompletion.model_validate(cached["response"])
        last.clear()
        last.update(seconds=cached["seconds"], cached=True, usage=cached["response"].get("usage"))
        return response
    limiter.wait(s.rpm)
    t0 = time.perf_counter()
    response = client().chat.completions.create(**payload)
    seconds = round(time.perf_counter() - t0, 2)
    data = response.model_dump(mode="json")
    if s.cache != "off":
        _write(path, {"date": _now(), "seconds": seconds, "request": payload, "response": data})
    last.clear()
    last.update(seconds=seconds, cached=False, usage=data.get("usage"))
    return response


def ask(prompt: str, *, system: str | None = None, **params) -> str:
    """The text of the answer to one question (see chat for params)."""
    messages = [{"role": "system", "content": system}] if system else []
    messages.append({"role": "user", "content": prompt})
    return chat(messages, **params).choices[0].message.content or ""


def reasoning(response: ChatCompletion) -> str:
    """The reasoning text of an answer, if the server returns it."""
    message = response.choices[0].message
    extra = message.model_extra or {}
    return extra.get("reasoning_content") or extra.get("reasoning") or ""


def to_json(response) -> str:
    """A response as the JSON that came over the wire, without empty fields."""
    return json.dumps(response.model_dump(mode="json", exclude_none=True),
                      ensure_ascii=False, indent=2)


# --- embeddings --------------------------------------------------------------------------

def embed(texts: str | list[str], *, model: str | None = None, batch: int = 64) -> np.ndarray:
    """The embeddings of some texts, one row per text.

    Each text is cached on its own, so changing how a document is split only embeds the
    new pieces; the missing ones go in batches of `batch` texts per request.
    """
    s = settings()
    if isinstance(texts, str):
        texts = [texts]
    model = model or s.embed_model
    folder = s.cache_dir / s.profile / "embeddings"
    paths = [folder / f"{_key(s.profile, model, t)}.json" for t in texts]
    vectors: dict[int, list[float]] = {}
    if s.cache == "on":
        for i, path in enumerate(paths):
            cached = _read(path)
            if cached:
                vectors[i] = cached["embedding"]
    missing = [i for i in range(len(texts)) if i not in vectors]
    seconds = 0.0
    for start in range(0, len(missing), batch):
        chunk = missing[start:start + batch]
        limiter.wait(s.rpm)
        t0 = time.perf_counter()
        response: CreateEmbeddingResponse = client().embeddings.create(
            model=model, input=[texts[i] for i in chunk])
        seconds += time.perf_counter() - t0
        for item in response.data:
            i = chunk[item.index]
            vectors[i] = item.embedding
            if s.cache != "off":
                _write(paths[i], {"model": model, "text": texts[i],
                                  "embedding": [round(x, 6) for x in item.embedding]})
    last.clear()
    last.update(seconds=round(seconds, 2), cached=not missing, texts=len(texts),
                requested=len(missing))
    return np.array([vectors[i] for i in range(len(texts))], dtype=np.float32)
