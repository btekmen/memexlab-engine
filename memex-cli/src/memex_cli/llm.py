"""The provider layer — one small client, plain HTTP, no SDKs, zero markup.

Resolution order (first match wins; keys from the environment ONLY):
  1. MEMEX_MODEL_URL   any OpenAI-compatible local endpoint (llama.cpp, Ollama,
                       LM Studio) — the sovereign route, no key needed
  2. GLM_API_KEY       GLM via an OpenAI-compatible endpoint (default model glm-5.2;
                       endpoint override: GLM_API_URL)
  3. ANTHROPIC_API_KEY Anthropic Messages API (default model claude-sonnet-5)
  4. OPENAI_API_KEY    OpenAI chat completions

MEMEX_MODEL overrides the model id on any route. qa is the ONLY consumer of this
module — every deterministic command works with none of these set (invariant 4).
"""
from __future__ import annotations

import json
import os
import urllib.request

GLM_DEFAULT_URL = "https://api.z.ai/api/paas/v4"
GLM_DEFAULT_MODEL = "glm-5.2"
ANTHROPIC_URL = "https://api.anthropic.com/v1"
ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-5"
OPENAI_DEFAULT_URL = "https://api.openai.com/v1"
OPENAI_DEFAULT_MODEL = "gpt-5.2"

REFUSAL = ("qa needs a model; deterministic commands (search, view, ingest, lint) "
           "never do. Set MEMEX_MODEL_URL for a local endpoint, or one of "
           "GLM_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY.")


def resolve_provider(env: dict | None = None) -> dict:
    """→ {kind: 'openai'|'anthropic', url, key, model, route}. Raises if none."""
    e = os.environ if env is None else env
    model = (e.get("MEMEX_MODEL") or "").strip()
    if (e.get("MEMEX_MODEL_URL") or "").strip():
        return {"kind": "openai", "url": e["MEMEX_MODEL_URL"].strip().rstrip("/"),
                "key": "", "model": model or "default", "route": "local"}
    if (e.get("GLM_API_KEY") or "").strip():
        return {"kind": "openai",
                "url": (e.get("GLM_API_URL") or GLM_DEFAULT_URL).rstrip("/"),
                "key": e["GLM_API_KEY"].strip(),
                "model": model or GLM_DEFAULT_MODEL, "route": "glm"}
    if (e.get("ANTHROPIC_API_KEY") or "").strip():
        return {"kind": "anthropic", "url": ANTHROPIC_URL,
                "key": e["ANTHROPIC_API_KEY"].strip(),
                "model": model or ANTHROPIC_DEFAULT_MODEL, "route": "anthropic"}
    if (e.get("OPENAI_API_KEY") or "").strip():
        return {"kind": "openai", "url": OPENAI_DEFAULT_URL,
                "key": e["OPENAI_API_KEY"].strip(),
                "model": model or OPENAI_DEFAULT_MODEL, "route": "openai"}
    raise RuntimeError(REFUSAL)


def _post(url: str, headers: dict, payload: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def complete(provider: dict, system: str, user: str, max_tokens: int = 1000) -> dict:
    """→ {text, model, usage:{input, output}} — no retries: fail loud, stay cheap."""
    if provider["kind"] == "anthropic":
        data = _post(f"{provider['url']}/messages",
                     {"x-api-key": provider["key"],
                      "anthropic-version": "2023-06-01"},
                     {"model": provider["model"], "max_tokens": max_tokens,
                      "system": system,
                      "messages": [{"role": "user", "content": user}]})
        text = "".join(b.get("text", "") for b in data.get("content", []))
        usage = data.get("usage", {})
        return {"text": text, "model": data.get("model", provider["model"]),
                "usage": {"input": usage.get("input_tokens", 0),
                          "output": usage.get("output_tokens", 0)}}
    headers = {"Authorization": f"Bearer {provider['key']}"} if provider["key"] else {}
    data = _post(f"{provider['url']}/chat/completions", headers,
                 {"model": provider["model"], "max_tokens": max_tokens,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}]})
    choice = (data.get("choices") or [{}])[0]
    usage = data.get("usage", {})
    return {"text": (choice.get("message") or {}).get("content", "") or "",
            "model": data.get("model", provider["model"]),
            "usage": {"input": usage.get("prompt_tokens", 0),
                      "output": usage.get("completion_tokens", 0)}}
