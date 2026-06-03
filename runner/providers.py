"""Provider-agnostic model client.

One env var, MEMEX_PROVIDER, switches the backend:

    anthropic   -> Anthropic Messages API   (pip install anthropic; ANTHROPIC_API_KEY)
    openai      -> OpenAI Chat Completions   (pip install openai;    OPENAI_API_KEY)
    local       -> any OpenAI-compatible local server (Ollama, vLLM, LM Studio, …)
                   (pip install openai; MEMEX_BASE_URL, default http://localhost:11434/v1)

Local and OpenAI share one code path because Ollama/vLLM/LM Studio all expose an
OpenAI-compatible /v1 endpoint — so "self-hosted model" vs "hosted API" is genuinely
a single env-var flip. The message format ([{role, content}, ...]) is identical for
both backends; only the system prompt placement differs, handled below.
"""
import os


def resolved():
    """Report the active config without making a network call (used by --dry-run)."""
    provider = os.environ.get("MEMEX_PROVIDER", "anthropic").lower()
    if provider == "anthropic":
        model = os.environ.get("MEMEX_MODEL", "claude-sonnet-4-5")
        endpoint = "Anthropic API"
    elif provider == "openai":
        model = os.environ.get("MEMEX_MODEL", "gpt-4o-mini")
        endpoint = os.environ.get("MEMEX_BASE_URL", "OpenAI API (default)")
    elif provider == "local":
        model = os.environ.get("MEMEX_MODEL", "llama3.1")
        endpoint = os.environ.get("MEMEX_BASE_URL", "http://localhost:11434/v1")
    else:
        model, endpoint = "?", "UNKNOWN PROVIDER"
    return {"provider": provider, "model": model, "endpoint": endpoint}


def complete(system, messages, max_tokens=1500):
    provider = os.environ.get("MEMEX_PROVIDER", "anthropic").lower()
    if provider == "anthropic":
        return _anthropic(system, messages, max_tokens)
    if provider in ("openai", "local"):
        return _openai_compatible(system, messages, max_tokens, provider)
    raise SystemExit(
        "Unknown MEMEX_PROVIDER={!r} (use anthropic | openai | local)".format(provider)
    )


def _anthropic(system, messages, max_tokens):
    try:
        from anthropic import Anthropic
    except ImportError:
        raise SystemExit("pip install anthropic  (and set ANTHROPIC_API_KEY)")
    model = os.environ.get("MEMEX_MODEL", "claude-sonnet-4-5")
    client = Anthropic()  # reads ANTHROPIC_API_KEY from env
    resp = client.messages.create(
        model=model, system=system, max_tokens=max_tokens, messages=messages,
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def _openai_compatible(system, messages, max_tokens, provider):
    try:
        from openai import OpenAI
    except ImportError:
        raise SystemExit("pip install openai")
    if provider == "local":
        base_url = os.environ.get("MEMEX_BASE_URL", "http://localhost:11434/v1")
        api_key = os.environ.get("MEMEX_API_KEY", "local")  # local servers ignore it
        model = os.environ.get("MEMEX_MODEL", "llama3.1")
    else:
        base_url = os.environ.get("MEMEX_BASE_URL") or None
        api_key = os.environ.get("OPENAI_API_KEY")
        model = os.environ.get("MEMEX_MODEL", "gpt-4o-mini")
    client = OpenAI(base_url=base_url, api_key=api_key)
    msgs = [{"role": "system", "content": system}] + messages
    resp = client.chat.completions.create(
        model=model, messages=msgs, max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""
