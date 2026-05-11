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


@dataclass(slots=True)
class TierRuntimeProfile:
    tribe_id: str
    tier: Tier
    provider: str
    model: str
    json_mode: bool
    timeout_seconds: int

    @property
    def profile_id(self) -> str:
        return f"{self.tribe_id}:{self.provider}:{self.model}"


def load_tier_profiles(config_path: str | Path) -> dict[str, TierRuntimeProfile]:
    path = Path(config_path)
    data: dict[str, Any] = yaml.safe_load(path.read_text()) or {}
    routing = data.get("tribe_model_routing") or []
    sla = data.get("sla") or {}
    profiles: dict[str, TierRuntimeProfile] = {}
    for item in routing:
        tribe_id = str(item["tribe_id"]).lower()
        tier = TRIBE_TIERS.get(tribe_id)
        if tier is None:
            raise ValueError(f"Unknown tribe in runtime config: {tribe_id}")
        timeout_key = {
            Tier.TIER_1: "tier1_response_seconds",
            Tier.TIER_2: "tier2_response_seconds",
            Tier.TIER_3: "tier3_response_seconds",
            Tier.TIER_4: "tier4_response_seconds",
        }.get(tier, "tier4_response_seconds")
        profiles[tribe_id] = TierRuntimeProfile(
            tribe_id=tribe_id,
            tier=tier,
            provider=str(item.get("provider") or "ollama"),
            model=str(item.get("model") or "llama3.2"),
            json_mode=bool(item.get("json_mode", True)),
            timeout_seconds=int(sla.get(timeout_key) or 30),
        )
    missing = sorted(set(TRIBE_TIERS) - set(profiles))
    if missing:
        raise ValueError(f"Missing runtime profiles for tribes: {', '.join(missing)}")
    return profiles

