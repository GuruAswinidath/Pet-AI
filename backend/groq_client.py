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


def _unwrap_accidental_json(text: str) -> str:
    """Some models occasionally wrap a plain-text answer in a JSON object
    (e.g. {"reply": "..."}) even when no response_format was requested.
    If that happens, pull the actual message back out rather than passing
    raw JSON through to the user as if it were prose."""
    stripped = text.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return text
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return text
    if not isinstance(parsed, dict):
        return text

    string_values = [v for v in parsed.values() if isinstance(v, str)]
    if len(string_values) == 1:
        return string_values[0]
    for key in ("reply", "response", "answer", "message", "text", "content"):
        if isinstance(parsed.get(key), str):
            return parsed[key]
    return text


def _supports_reasoning_effort(model: str) -> bool:
    """The "gpt-oss" model family (all of this app's current agents, per
    config.py) does hidden reasoning before its visible/JSON answer, and
    that reasoning draws from the same max_tokens budget - confirmed via
    completion_tokens_details.reasoning_tokens on a live call. Left
    uncapped, that consumption is unpredictable enough to have caused two
    real, observed failures: the Safety/Note Agents' response_format
    json_object calls returning invalid or truncated JSON, and the
    Conversation Agent's plain-text reply itself getting cut off
    mid-sentence. `reasoning_effort` is gpt-oss-specific - passing it to a
    model that doesn't support it is a hard 400, so this must stay gated
    rather than sent unconditionally regardless of the *_MODEL env vars."""
    return "gpt-oss" in model


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
    if _supports_reasoning_effort(model):
        # Every agent in this app wants a fast, concise, or strictly
        # schema-conforming answer, never an extended "thinking out loud"
        # pass - "low" keeps reasoning token usage small and predictable
        # instead of letting it silently crowd out the visible/JSON output.
        kwargs["extra_body"] = {"reasoning_effort": "low"}

    completion = client.chat.completions.create(**kwargs)
    content = completion.choices[0].message.content or ""
    if json_mode:
        return content
    return _unwrap_accidental_json(content)


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
