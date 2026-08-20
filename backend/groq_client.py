"""Single Groq client wrapper shared by every LLM agent.

README section 2.1: since the Orchestrator, Intake, Conversation, Safety,
and Note agents are all on Groq, they run through one client/SDK with
just the model name changing per call. This module is that one client.
"""

import json
from typing import Any, Optional

from groq import Groq

import config

_client: Optional[Groq] = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        config.require_groq_key()
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


def chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    *,
    json_mode: bool = False,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """Single-turn chat call. Returns raw text content."""
    client = _get_client()
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    completion = client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content or ""


def chat_json(
    model: str,
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """Chat call that enforces + parses a JSON object response. Raises
    ValueError with the raw text attached if the model didn't return
    parseable JSON, so callers can decide how to fall back."""
    raw = chat(
        model,
        system_prompt,
        user_prompt,
        json_mode=True,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {raw!r}") from exc
