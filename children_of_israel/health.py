"""health.py
Health check HTTP endpoint for the Children of Israel Agent Swarm.
Exposes GET /health for Kubernetes readiness/liveness probes.

Run with:
    python -m children_of_israel.health
"""
from __future__ import annotations

import yaml
from pathlib import Path

try:
    from fastapi import FastAPI
    import uvicorn
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from children_of_israel.checkpointing import DEFAULT_BACKEND


app = FastAPI(title="Children of Israel Swarm Health") if _FASTAPI_AVAILABLE else None

_TRIBES = [
    "reuben", "simeon", "levi", "judah", "issachar", "zebulun",
    "dan", "naphtali", "gad", "asher", "joseph", "benjamin"
]


def _check_law_layer() -> bool:
    """Return True if all three law layer files are present and non-empty."""
    law_dir = Path(__file__).parent.parent / "law"
    required = ["constitution.yaml", "commandments.yaml", "oral_law.yaml"]
    return all((law_dir / f).exists() and (law_dir / f).stat().st_size > 0 for f in required)


def _get_checkpointer_backend() -> str:
    try:
        cfg_path = Path(__file__).parent.parent / "config" / "mission.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        return cfg.get("checkpointing", {}).get("backend", DEFAULT_BACKEND)
    except Exception:
        return DEFAULT_BACKEND


if _FASTAPI_AVAILABLE and app is not None:
    @app.get("/health")
    async def health() -> dict:
        return {
            "status": "ok",
            "tribes_loaded": len(_TRIBES),
            "tribe_names": _TRIBES,
            "law_loaded": _check_law_layer(),
            "checkpointer": _get_checkpointer_backend(),
        }

    @app.get("/")
    async def root() -> dict:
        return {"service": "children-of-israel-swarm", "docs": "/docs"}


def main() -> None:
    if not _FASTAPI_AVAILABLE:
        print("FastAPI not installed. Run: pip install fastapi uvicorn")
        return
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
