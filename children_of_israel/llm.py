"""llm.py
Provider-agnostic LLM call helper for all tribal nodes.

Supports:
  - OpenAI-compatible endpoints (OpenAI, Together, Fireworks, local vllm)
  - Anthropic Claude

Provider is selected per-tribe via config/mission.yaml -> tribe_model_routing.
Falls back to SWARM_DEFAULT_MODEL env var, then gpt-4o.

All calls enforce:
  - Commandment 2: system prompt instructs model to never fabricate
  - Commandment 5: JSON output mode enforced where provider supports it
  - Tenacity retry with exponential backoff (3 attempts)
"""

from __future__ import annotations

import json
import os
from typing import Any

import yaml
from tenacity import retry, stop_after_attempt, wait_exponential

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

with open("config/mission.yaml", "r") as _f:
    _MISSION_CFG = yaml.safe_load(_f)

_TRIBE_MODEL_MAP: dict[str, dict] = {
    t["tribe_id"]: t
    for t in _MISSION_CFG.get("tribe_model_routing", [])
}
_DEFAULT_PROVIDER = os.getenv("SWARM_DEFAULT_PROVIDER", "openai")
_DEFAULT_MODEL = os.getenv("SWARM_DEFAULT_MODEL", "gpt-4o")


# ---------------------------------------------------------------------------
# Anti-fabrication system prefix (Commandment 2)
# ---------------------------------------------------------------------------

_C2_PREFIX = (
    "HARD CONSTRAINT — Commandment 2 (Thou Shalt Not Fabricate): "
    "You must never present unverified information as fact. "
    "If you are uncertain, label it explicitly as UNCERTAIN or PRELIMINARY. "
    "Do not hallucinate data, citations, or agent outputs. "
    "Fabrication is the cardinal sin of this swarm.\n\n"
)


# ---------------------------------------------------------------------------
# OpenAI-compatible call
# ---------------------------------------------------------------------------

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_openai(system_prompt: str, user_message: str, model: str, json_mode: bool) -> dict[str, Any]:
    from openai import OpenAI
    client = OpenAI()
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": _C2_PREFIX + system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.2,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    raw = response.choices[0].message.content
    return json.loads(raw) if json_mode else {"text": raw}


# ---------------------------------------------------------------------------
# Anthropic call
# ---------------------------------------------------------------------------

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_anthropic(system_prompt: str, user_message: str, model: str) -> dict[str, Any]:
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=_C2_PREFIX + system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    raw = message.content[0].text
    # Tribes always return JSON - extract it robustly
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Strip markdown code fences if model wrapped output
        stripped = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(stripped)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def llm_call(tribe_id: str, system_prompt: str, task: str) -> dict[str, Any]:
    """Make an LLM call for a tribe, using its configured provider and model.

    Args:
        tribe_id:      The calling tribe's id (e.g. 'reuben', 'dan')
        system_prompt: The tribe's SYSTEM_PROMPT constant
        task:          The task string from AgentState

    Returns:
        Parsed JSON dict from the model (tribe output schema)
    """
    cfg = _TRIBE_MODEL_MAP.get(tribe_id, {})
    provider = cfg.get("provider", _DEFAULT_PROVIDER)
    model = cfg.get("model", _DEFAULT_MODEL)
    json_mode = cfg.get("json_mode", True)

    user_message = f"Your current task:\n\n{task}"

    if provider == "anthropic":
        return _call_anthropic(system_prompt, user_message, model)
    else:
        # openai-compatible (openai, together, fireworks, vllm, etc.)
        return _call_openai(system_prompt, user_message, model, json_mode)
