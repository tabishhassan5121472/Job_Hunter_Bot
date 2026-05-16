"""Pluggable LLM provider for JobHunter.

Picks Cerebras (free 1M tokens/day, Llama 3.3 70B) when CEREBRAS_API_KEY is
set, otherwise falls back to Anthropic Claude. Returns None if neither is
configured so the calling pipeline can skip LLM features cleanly.

Both providers expose a chat-completion style API. We hide that behind a
single `complete(system, user, max_tokens, model_hint)` call.
"""
from __future__ import annotations
import os
import re
from typing import Optional


def is_configured() -> bool:
    return bool(os.environ.get("CEREBRAS_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


def provider_name() -> str:
    if os.environ.get("CEREBRAS_API_KEY"):
        return "cerebras"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "none"


def complete(
    system: str,
    user: str,
    *,
    max_tokens: int = 500,
    model_hint: str = "fast",
    temperature: float = 0.2,
) -> Optional[str]:
    """Run one chat completion. Returns the assistant text or None if no
    provider is configured. `model_hint` is 'fast' (short structured output,
    e.g. rerank JSON) or 'writing' (longer prose, e.g. cover letters)."""
    cerebras = os.environ.get("CEREBRAS_API_KEY")
    if cerebras:
        return _call_cerebras(system, user, max_tokens, temperature, cerebras)

    anth = os.environ.get("ANTHROPIC_API_KEY")
    if anth:
        return _call_anthropic(system, user, max_tokens, temperature, model_hint, anth)

    return None


def _call_cerebras(system, user, max_tokens, temperature, api_key) -> Optional[str]:
    try:
        from openai import OpenAI
    except ImportError:
        return None
    client = OpenAI(api_key=api_key, base_url="https://api.cerebras.ai/v1")
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b",
            max_completion_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[llm error (cerebras): {e}]"


def _call_anthropic(system, user, max_tokens, temperature, model_hint, api_key) -> Optional[str]:
    try:
        import anthropic
    except ImportError:
        return None
    client = anthropic.Anthropic(api_key=api_key)
    model = "claude-haiku-20240307" if model_hint == "fast" else "claude-sonnet-20241022"
    try:
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text
    except Exception as e:
        return f"[llm error (anthropic): {e}]"


JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def strip_json_fences(text: str) -> str:
    """Llama models sometimes wrap JSON in ```json ... ``` fences even when
    told not to. Strip them so json.loads() works."""
    if not text:
        return text
    m = JSON_FENCE_RE.search(text)
    if m:
        return m.group(1)
    return text.strip()
