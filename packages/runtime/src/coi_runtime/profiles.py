from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from coi_contracts import Tier


TRIBE_TIERS: dict[str, Tier] = {
    "judah": Tier.TIER_1,
    "levi": Tier.TIER_1,
    "dan": Tier.TIER_1,
    "joseph": Tier.TIER_1,
    "simeon": Tier.TIER_2,
    "issachar": Tier.TIER_3,
    "zebulun": Tier.TIER_3,
    "asher": Tier.TIER_3,
    "reuben": Tier.TIER_4,
    "naphtali": Tier.TIER_4,
    "gad": Tier.TIER_4,
    "benjamin": Tier.TIER_4,
}

JETHRO_TIERS: dict[str, Tier] = {
    "moses": Tier.ROOT,
    **TRIBE_TIERS,
}

DEFAULT_MODEL_CLASS_BY_TIER: dict[Tier, str] = {
    Tier.ROOT: "root_judge",
    Tier.TIER_1: "senior_judge",
    Tier.TIER_2: "compliance",
    Tier.TIER_3: "coordinator",
    Tier.TIER_4: "leaf_executor",
}

TIMEOUT_KEY_BY_TIER: dict[Tier, str] = {
    Tier.ROOT: "moses_ruling_seconds",
    Tier.TIER_1: "tier1_response_seconds",
    Tier.TIER_2: "tier2_response_seconds",
    Tier.TIER_3: "tier3_response_seconds",
    Tier.TIER_4: "tier4_response_seconds",
}


@dataclass(slots=True)
class ModelClassPolicy:
    model_class: str
    provider: str
    model: str
    json_mode: bool = True
    options: dict[str, Any] | None = None


@dataclass(slots=True)
class TierRuntimeProfile:
    tribe_id: str
    tier: Tier
    model_class: str
    provider: str
    model: str
    json_mode: bool
    timeout_seconds: int
    options: dict[str, Any] | None = None

    @property
    def profile_id(self) -> str:
        return f"{self.tribe_id}:{self.model_class}:{self.provider}:{self.model}"


def load_tier_profiles(config_path: str | Path) -> dict[str, TierRuntimeProfile]:
    path = Path(config_path)
    data: dict[str, Any] = yaml.safe_load(path.read_text()) or {}
    routing = _legacy_routing_by_tribe(data.get("tribe_model_routing") or [])
    model_classes = _load_model_classes(data.get("model_classes") or {})
    tier_model_classes = _load_tier_model_classes(data.get("tier_model_classes") or {})
    tribe_model_classes = _load_tribe_model_classes(data.get("tribe_model_classes") or {})
    sla = data.get("sla") or {}
    profiles: dict[str, TierRuntimeProfile] = {}

    profile_tiers = JETHRO_TIERS if model_classes else TRIBE_TIERS
    for tribe_id, tier in profile_tiers.items():
        legacy = routing.get(tribe_id) or {}
        model_class = str(
            legacy.get("model_class")
            or tribe_model_classes.get(tribe_id)
            or tier_model_classes.get(tier.value)
            or DEFAULT_MODEL_CLASS_BY_TIER[tier]
        )
        policy = model_classes.get(model_class)
        if policy is None:
            policy = ModelClassPolicy(
                model_class=model_class,
                provider=str(legacy.get("provider") or "ollama"),
                model=str(legacy.get("model") or "llama3.2"),
                json_mode=bool(legacy.get("json_mode", True)),
                options=_mapping_or_none(legacy.get("options")),
            )

        timeout_key = TIMEOUT_KEY_BY_TIER[tier]
        profiles[tribe_id] = TierRuntimeProfile(
            tribe_id=tribe_id,
            tier=tier,
            model_class=model_class,
            provider=policy.provider,
            model=policy.model,
            json_mode=bool(legacy.get("json_mode", policy.json_mode)),
            timeout_seconds=int(sla.get(timeout_key) or 30),
            options=policy.options,
        )
    missing = sorted(set(profile_tiers) - set(profiles))
    if missing:
        raise ValueError(f"Missing runtime profiles for tribes: {', '.join(missing)}")
    return profiles


def _legacy_routing_by_tribe(routing: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for item in routing:
        tribe_id = str(item["tribe_id"]).lower()
        if tribe_id not in JETHRO_TIERS:
            raise ValueError(f"Unknown tribe in runtime config: {tribe_id}")
        profiles[tribe_id] = item
    return profiles


def _load_model_classes(config: dict[str, Any]) -> dict[str, ModelClassPolicy]:
    policies: dict[str, ModelClassPolicy] = {}
    for name, item in config.items():
        if not isinstance(item, dict):
            raise ValueError(f"Invalid model class config for {name}")
        model_class = str(name)
        policies[model_class] = ModelClassPolicy(
            model_class=model_class,
            provider=str(item.get("provider") or "ollama"),
            model=str(item.get("model") or "llama3.2"),
            json_mode=bool(item.get("json_mode", True)),
            options=_mapping_or_none(item.get("options")),
        )
    return policies


def _load_tier_model_classes(config: dict[str, Any]) -> dict[str, str]:
    classes: dict[str, str] = {}
    valid_tiers = {tier.value for tier in Tier}
    for tier, model_class in config.items():
        tier_key = str(tier)
        if tier_key not in valid_tiers:
            raise ValueError(f"Unknown tier in model class config: {tier_key}")
        classes[tier_key] = str(model_class)
    return classes


def _load_tribe_model_classes(config: dict[str, Any]) -> dict[str, str]:
    classes: dict[str, str] = {}
    for tribe_id, model_class in config.items():
        tribe_key = str(tribe_id).lower()
        if tribe_key not in JETHRO_TIERS:
            raise ValueError(f"Unknown tribe in model class config: {tribe_key}")
        classes[tribe_key] = str(model_class)
    return classes


def _mapping_or_none(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("Model policy options must be a mapping")
    return dict(value)
