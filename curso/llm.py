"""Access to the course models: one OpenAI-compatible client ready for the corporate
network, a request limit and a disk cache.

Every model call in the notebook goes through chat() or embed(). A call already made is
read from cache/ and costs nothing, so the session depends neither on the gateway being up,
nor on its quota, nor on the model answering the same thing twice.

Configuration, from the environment only (the key and the passwords never go in a file):

  Server and models
    CURSO_PROFILE      gateway (default) or openrouter (for development)
    CURSO_BASE_URL     the API URL, ending in /v1 (preset for openrouter)
    CURSO_API_KEY      the API key (with openrouter, OPENROUTER_API_KEY also works)
    CURSO_MODEL        the chat model (gateway: gemma-4)
    CURSO_MODELS       the chat models to compare, comma-separated (gateway: gemma-4,
                       gpt-oss-120b, devstral)
    CURSO_EMBED_MODEL  the embeddings model (gateway: embeddinggemma)

  Corporate network
    CURSO_PROXY        the proxy, with its credentials if it asks for them:
                       http://user:password@proxy:8080. By default HTTPS_PROXY,
                       https_proxy, HTTP_PROXY or http_proxy
    CURSO_NO_PROXY     hosts that go direct, comma-separated: an internal gateway may not
                       need the proxy. By default NO_PROXY, or localhost
    CURSO_CA_CERT      "system" (default): the system certificate store (Windows, macOS),
                       where the corporate root CA already is, needed when the proxy
                       inspects TLS; a PEM file or folder with the corporate CA, added to
                       the usual CAs; or "default": only the usual CAs. If it is not set,
                       SSL_CERT_FILE or REQUESTS_CA_BUNDLE are used
    CURSO_CLIENT_CERT  client certificate (PEM), if the server asks for one (mutual TLS)
    CURSO_CLIENT_KEY   its private key, if it is not in the same file;
                       CURSO_CLIENT_KEY_PASSWORD if the key has a password
    CURSO_TIMEOUT      seconds per request (default 600)

  Quota and cache
    CURSO_RPM          requests per minute at most (default 28)
    CURSO_MAX_WAIT     seconds to keep waiting while the server rejects for the quota (409
                       or 429) before giving up (default 900)
    CURSO_CACHE        on (default): use the cache; refresh: call again and overwrite;
                       off: no cache
    CURSO_CACHE_DIR    where the cache is (default cache/)

    python -m curso.llm

shows the effective configuration, with the secrets masked, and makes one real request to
the chat and one to the embeddings: the first thing to try on a new computer.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import ssl
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Callable, TypeVar
from urllib.parse import urlparse

import httpx
import numpy as np
import openai
from openai import DefaultHttpxClient, OpenAI
from openai.types import CreateEmbeddingResponse
from openai.types.chat import ChatCompletion

ROOT = Path(__file__).resolve().parent.parent

PROFILES = {
    "gateway": {"base_url": "", "model": "gemma-4", "embed_model": "embeddinggemma",
                "models": "gemma-4,gpt-oss-120b,devstral"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1",
                   "model": "google/gemma-4-26b-a4b-it", "embed_model": "baai/bge-m3",
                   "models": "google/gemma-4-26b-a4b-it,openai/gpt-oss-120b,"
                             "mistralai/devstral-2512"},
}

MAX_RETRIES = 5
"""Retries on 5xx and on connection failures; the quota rejections do not count."""

last: dict = {}
"""The last call: seconds it took (when it was really made), whether it came from the
cache, and the token usage."""

T = TypeVar("T")


@dataclass(frozen=True)
class Settings:
    profile: str
    base_url: str
    api_key: str
    model: str
    embed_model: str
    models: tuple[str, ...]
    proxy: str
    no_proxy: str
    ca_cert: str
    client_cert: str
    client_key: str
    timeout: float
    rpm: float
    max_wait: float
    cache: str
    cache_dir: Path


def _env(*names: str, default: str = "") -> str:
    for name in names:
        if os.environ.get(name):
            return os.environ[name]
    return default


def settings() -> Settings:
    """The configuration, read from the environment on every call."""
    profile = _env("CURSO_PROFILE", default="gateway")
    if profile not in PROFILES:
        raise ValueError(f"CURSO_PROFILE={profile!r}: use one of {', '.join(PROFILES)}")
    preset = PROFILES[profile]
    key_names = ["CURSO_API_KEY"] + (["OPENROUTER_API_KEY"] if profile == "openrouter" else [])
    return Settings(
        profile=profile,
        base_url=_env("CURSO_BASE_URL", default=preset["base_url"]).rstrip("/"),
        api_key=_env(*key_names),
        model=_env("CURSO_MODEL", default=preset["model"]),
        embed_model=_env("CURSO_EMBED_MODEL", default=preset["embed_model"]),
        models=tuple(m.strip() for m in _env("CURSO_MODELS", default=preset["models"])
                     .split(",") if m.strip()),
        proxy=_env("CURSO_PROXY", "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"),
        no_proxy=_env("CURSO_NO_PROXY", "NO_PROXY", "no_proxy", default="localhost,127.0.0.1,::1"),
        ca_cert=_env("CURSO_CA_CERT", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", default="system"),
        client_cert=_env("CURSO_CLIENT_CERT"),
        client_key=_env("CURSO_CLIENT_KEY"),
        timeout=float(_env("CURSO_TIMEOUT", default="600")),
        rpm=float(_env("CURSO_RPM", default="28")),
        max_wait=float(_env("CURSO_MAX_WAIT", default="900")),
        cache=_env("CURSO_CACHE", default="on"),
        cache_dir=Path(_env("CURSO_CACHE_DIR", default=str(ROOT / "cache"))),
    )


# --- corporate network: proxy and certificates ------------------------------------------

def _mask_url(url: str) -> str:
    """A URL without the password (or user) it may carry."""
    return re.sub(r"//[^/@]+@", "//***@", url or "")


def _mask_key(key: str) -> str:
    return "" if not key else (key[:3] + "***" if len(key) > 8 else "***")


def _bypasses_proxy(host: str, no_proxy: str) -> bool:
    host = host.lower()
    for pattern in (p.strip().lower().lstrip(".") for p in no_proxy.split(",")):
        if pattern and (pattern == "*" or host == pattern or host.endswith("." + pattern)):
            return True
    return False


def effective_proxy(s: Settings | None = None) -> str:
    """The proxy the requests go through, or "" if they go direct."""
    s = s or settings()
    host = urlparse(s.base_url).hostname or ""
    return s.proxy if s.proxy and not _bypasses_proxy(host, s.no_proxy) else ""


def ssl_context(s: Settings | None = None) -> ssl.SSLContext:
    """The TLS context: which CAs are trusted and, if there is one, the client certificate."""
    s = s or settings()
    if s.ca_cert.lower() == "system":
        import truststore
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    else:
        ctx = ssl.create_default_context()      # on Windows it already has the system store
        # Python 3.13 turned on VERIFY_X509_STRICT, which rejects certificates without an
        # Authority Key Identifier, as some TLS-inspecting proxies issue them. The chain and
        # the host name are still verified, as curl and the system store do.
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        try:
            import certifi
            ctx.load_verify_locations(cafile=certifi.where())
        except ImportError:
            pass
        if s.ca_cert.lower() != "default":
            path = Path(s.ca_cert).expanduser()
            if not path.exists():
                raise FileNotFoundError(f"CURSO_CA_CERT: {path} does not exist")
            if path.is_dir():
                ctx.load_verify_locations(capath=str(path))
            else:
                ctx.load_verify_locations(cafile=str(path))
    if s.client_cert:
        ctx.load_cert_chain(str(Path(s.client_cert).expanduser()),
                            str(Path(s.client_key).expanduser()) if s.client_key else None,
                            password=os.environ.get("CURSO_CLIENT_KEY_PASSWORD") or None)
    return ctx


_clients: dict[tuple, OpenAI] = {}


def client() -> OpenAI:
    """The OpenAI client of the current configuration. It does not retry by itself: send()
    does, waiting on the quota as long as it takes."""
    s = settings()
    key = (s.base_url, s.api_key, s.proxy, s.no_proxy, s.ca_cert, s.client_cert,
           s.client_key, s.timeout)
    if key not in _clients:
        if not s.base_url:
            raise RuntimeError("CURSO_BASE_URL is not set: the gateway URL, ending in /v1")
        if not s.api_key:
            raise RuntimeError("CURSO_API_KEY is not set, and the call is not in the cache")
        proxy = effective_proxy(s)
        transport = httpx.HTTPTransport(verify=ssl_context(s),
                                        proxy=httpx.Proxy(proxy) if proxy else None)
        http = DefaultHttpxClient(transport=transport, trust_env=False,
                                  timeout=httpx.Timeout(s.timeout, connect=30.0))
        _clients[key] = OpenAI(base_url=s.base_url, api_key=s.api_key, http_client=http,
                               timeout=s.timeout, max_retries=0)
    return _clients[key]


def diagnose(error: BaseException) -> str:
    """What to change for the connection errors typical of a corporate network, or ""."""
    chain, e = [], error
    while e is not None and len(chain) < 10:
        chain.append(e)
        e = e.__cause__ or e.__context__
    text = " | ".join(f"{type(c).__name__}: {c}" for c in chain)
    names = {type(c).__name__ for c in chain}
    if "CERTIFICATE_VERIFY_FAILED" in text or "SSLCertVerificationError" in names:
        return ("the server certificate is not trusted. If the proxy inspects TLS, the "
                "corporate root CA is needed: CURSO_CA_CERT=system (the system store, where "
                "it usually is) or the path of its PEM file.")
    if re.search(r"\b407\b", text):
        return ("the proxy asks for credentials: "
                "CURSO_PROXY=http://user:password@proxy:port")
    if "PEM lib" in text or "bad decrypt" in text.lower():
        return ("the client certificate or its key cannot be read: check CURSO_CLIENT_CERT, "
                "CURSO_CLIENT_KEY and CURSO_CLIENT_KEY_PASSWORD")
    if "CERTIFICATE_REQUIRED" in text or "certificate required" in text.lower() \
            or "HANDSHAKE_FAILURE" in text:
        return "the server asks for a client certificate: CURSO_CLIENT_CERT and CURSO_CLIENT_KEY"
    if names & {"RateLimitError", "ConflictError"}:
        return ("the server kept rejecting for the quota for CURSO_MAX_WAIT seconds; it may "
                "be an hourly or daily quota. Wait, or lower CURSO_RPM.")
    if "AuthenticationError" in names:
        return "the key was rejected: check CURSO_API_KEY"
    if "PermissionDeniedError" in names:
        return "the key has no access to this model or endpoint"
    if "NotFoundError" in names:
        return "path or model not found: does CURSO_BASE_URL end in /v1? is the model name right?"
    if "ProxyError" in names:
        return "cannot connect through the proxy: check CURSO_PROXY and CURSO_NO_PROXY"
    if names & {"ConnectError", "ConnectTimeout", "APIConnectionError", "APITimeoutError"}:
        return ("cannot connect. If the gateway is internal it may not need the proxy (add "
                "its host to CURSO_NO_PROXY); if it is external, it may need one (CURSO_PROXY).")
    return ""


def _no_retry(error: BaseException) -> bool:
    """Connection errors that will not go away by trying again."""
    hint = diagnose(error)
    return any(word in hint for word in ("certificate", "credentials", "client certificate"))


def _add_hint(error: BaseException) -> None:
    hint = diagnose(error)
    if hint:
        if hasattr(error, "add_note"):               # Python 3.11+
            error.add_note(f"curso.llm: {hint}")
        else:
            _log(hint)


def _log(message: str) -> None:
    print(f"[curso.llm] {message}", file=sys.stderr, flush=True)


def describe() -> str:
    """The effective configuration, with the secrets masked."""
    s = settings()
    if s.ca_cert.lower() == "system":
        tls = "system certificate store"
    elif s.ca_cert.lower() == "default":
        tls = "usual CAs (Python and certifi)"
    else:
        tls = f"usual CAs + {s.ca_cert}"
    proxy = effective_proxy(s)
    return "\n".join([
        f"profile {s.profile}: {_mask_url(s.base_url) or '(CURSO_BASE_URL not set)'}",
        f"  chat {s.model}, embeddings {s.embed_model or '-'}, "
        f"key {_mask_key(s.api_key) or 'NOT SET'}",
        f"  to compare: {', '.join(s.models)}",
        f"  proxy: {_mask_url(proxy) if proxy else 'direct'}"
        + (f" (configured {_mask_url(s.proxy)}, but the host is in no_proxy)"
           if s.proxy and not proxy else ""),
        f"  TLS: {tls}" + (f"; client certificate {s.client_cert}" if s.client_cert else ""),
        f"  {s.rpm:g} requests/min; on 409/429 waits up to {s.max_wait / 60:g} min; "
        f"timeout {s.timeout:g} s; cache {s.cache} in {_shown_path(s.cache_dir)}/",
    ])


def _shown_path(path: Path) -> str:
    """A path relative to the repository when it is inside it: it ends up in the notebook
    outputs, and the user's home folder has no business there."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


# --- request limit and retries -----------------------------------------------------------

class _Limiter:
    """Spaces the requests so that there are at most rpm per minute, and pauses them all
    when the server rejects for the quota."""

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

    def pause(self, seconds: float) -> None:
        with self._lock:
            self._next = max(self._next, time.monotonic() + seconds)


limiter = _Limiter()


def _retry_after(response: httpx.Response | None) -> float:
    """Seconds the server asks to wait (Retry-After, x-ratelimit-reset-*), or 0."""
    if response is None:
        return 0.0
    value = response.headers.get("retry-after", "")
    if value:
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                return max(0.0, (parsedate_to_datetime(value)
                                 - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError):
                pass
    for name in ("x-ratelimit-reset-requests", "x-ratelimit-reset-tokens", "x-ratelimit-reset"):
        m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m(?!s))?(?:([\d.]+)s?)?",
                         response.headers.get(name, ""))
        if m and any(m.groups()):
            h, mi, sec = (float(g) if g else 0.0 for g in m.groups())
            return h * 3600 + mi * 60 + sec
    return 0.0


def send(request: Callable[[], T]) -> tuple[T, float]:
    """Makes one request (a call to the client) within the request limit, and returns its
    result and the seconds it took. On 409 or 429 (the quota) it waits what the server says,
    or longer each time, up to CURSO_MAX_WAIT; 5xx and connection failures are retried
    MAX_RETRIES times, but not certificate or proxy credential errors. An error that goes
    up carries a hint of what to change (diagnose)."""
    s = settings()
    waited, retries, rejections = 0.0, 0, 0
    while True:
        limiter.wait(s.rpm)
        t0 = time.perf_counter()
        try:
            return request(), time.perf_counter() - t0
        except openai.APIStatusError as e:
            if e.status_code in (409, 429):
                rejections += 1
                delay = _retry_after(e.response) or min(60.0, 5.0 * 2 ** (rejections - 1))
                if waited + delay > s.max_wait:
                    _add_hint(e)
                    raise
                _log(f"HTTP {e.status_code} (quota): waiting {delay:.0f} s")
            elif e.status_code >= 500 and retries < MAX_RETRIES:
                retries += 1
                delay = min(60.0, 2.0 ** retries)
                _log(f"HTTP {e.status_code}: retry {retries}/{MAX_RETRIES} in {delay:.0f} s")
            else:
                _add_hint(e)
                raise
        except openai.APIConnectionError as e:          # also timeouts
            if _no_retry(e) or retries >= MAX_RETRIES:
                _add_hint(e)
                raise
            retries += 1
            delay = min(60.0, 2.0 ** retries)
            _log(f"no connection: retry {retries}/{MAX_RETRIES} in {delay:.0f} s")
        limiter.pause(delay)
        waited += delay


def models() -> list[str]:
    """The model names the server offers."""
    page, _ = send(lambda: client().models.list())
    return sorted(m.id for m in page)


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
    response, seconds = send(lambda: client().chat.completions.create(**payload))
    seconds = round(seconds, 2)
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
        response: CreateEmbeddingResponse
        response, took = send(lambda: client().embeddings.create(
            model=model, input=[texts[i] for i in chunk]))
        seconds += took
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


# --- connection check --------------------------------------------------------------------

def check() -> bool:
    """Shows the configuration and makes one real request to the chat and one to the
    embeddings, without the cache. True if both work."""
    s = settings()
    print(describe())
    requests = [
        # reasoning models think before answering, within max_tokens: not too few
        ("chat", lambda: client().chat.completions.create(
            model=s.model, max_tokens=512,
            messages=[{"role": "user", "content": "Reply with exactly one word: OK"}])),
        ("embeddings", lambda: client().embeddings.create(model=s.embed_model, input=["ok"])),
    ]
    ok = True
    for name, request in requests:
        try:
            response, seconds = send(request)
        except Exception as e:  # noqa: BLE001 - shown to the user, with the hint
            ok = False
            print(f"{name}: FAILED: {type(e).__name__}: {str(e)[:200]}")
            if diagnose(e):
                print(f"  -> {diagnose(e)}")
            continue
        if name == "chat":
            detail = repr((response.choices[0].message.content or "").strip()[:30])
        else:
            detail = f"{len(response.data[0].embedding)} dimensions"
        print(f"{name}: OK, {detail}, {seconds:.1f} s")
    return ok


if __name__ == "__main__":
    sys.exit(0 if check() else 1)
