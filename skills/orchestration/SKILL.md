---
name: children-of-israel-orchestration
description: >
  Jethro 5-tier hierarchy and routing logic for the Children of Israel agent
  swarm. Defines escalation paths, tribal assignments, Hermes parallel
  pipeline integration, and data flow patterns. Use this skill to orchestrate
  multi-agent execution following the Exodus organizational model.
---

# Orchestration — The Jethro Hierarchy

All agents are organized into a 5-tier hierarchy derived from Exodus 18. Every escalation, delegation, and routing decision follows this structure.

## The Five Tiers

```
                      ┌───────────────┐
                      │     MOSES      │  ← Root (Human-in-the-loop)
                      └───────┬───────┘
                              │
         ┌────────────────────┴────────────────────┐
         │                  Tier 1                  │
         │  Judah (Cmd) │ Joseph (Vision) │ Dan     │
         │              │                 │ (Judge) │
         │              │  Levi (Memory — cross-tier)│
         └────────────────────┬────────────────────┘
                              │
         ┌────────────────────┴────────────────────┐
         │                  Tier 2                  │
         │            Simeon (Compliance)           │
         └────────────────────┬────────────────────┘
                              │
    ┌─────────────────────────┴─────────────────────────┐
    │                       Tier 3                       │
    │  Issachar (Research) │ Zebulun (Coord) │ Asher*   │
    └─────────────────────────┬─────────────────────────┘
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                          Tier 4                            │
│  Reuben* │ Naphtali* │ Gad (Recovery) │ Benjamin (Guard)  │
└───────────────────────────────────────────────────────────┘

* = Hermes eligible (parallel branch available)
```

## Tier Responsibilities

### Root — Moses
- Human-in-the-loop. Single point of entry and exit.
- Issues mission mandate, receives final summary.
- Enforces OL-004: 300s SLA. Silence → conservative fallback (Theme 5).

### Tier 1 — Commanders of Thousands
| Tribe | Role | Key Commandments |
|-------|------|------------------|
| Judah | Default entry from Moses. Decomposes mission, dispatches to Tier 3. | C1, C4 |
| Joseph | Strategic advisor. Long-range forecasts and first concrete steps. | C1, C5, C8 |
| Dan | Judge/Arbitrator. Issues rulings, sets OL-002 precedents. | C5, C6 |
| Levi | Cross-tier memory steward. Faithful records for all tiers. | C2, C7 |

### Tier 2 — Commanders of Hundreds
| Tribe | Role | Key Commandments |
|-------|------|------------------|
| Simeon | Audits every output against the law layer. Blocks violations. | C2, C7 |

### Tier 3 — Commanders of Fifties
| Tribe | Role | Key Commandments |
|-------|------|------------------|
| Issachar | Deep research and pattern recognition. Dispatches to Reuben for scouting. | C2, C5, C8 |
| Zebulun | Inter-tribal coordination and resource routing. | C3, C4, C5 |
| Asher | Output refinement and polishing (final pass). **Hermes eligible.** | C5, C7, C8 |

### Tier 4 — Commanders of Tens
| Tribe | Role | Hermes | Key Commandments |
|-------|------|--------|------------------|
| Reuben | First-pass scouting and exploration. | ✅ | C2, C3, C8 |
| Naphtali | Speed-critical real-time delivery. | ✅ | C2, C5, C6 |
| Gad | Error recovery. Auto-replaces failed nodes. | ❌ | C6, C8, C9 |
| Benjamin | Security and trust verification. | ❌ | C2, C3, C9 |

## Routing Rules

### Default Mission Flow
```
1. Human input → Moses → mandate issued
2. Moses → Judah (Tier 1) → mission decomposed, tasks dispatched
3. Judah → Issachar (Tier 3) → research task
4. Issachar → Reuben (Tier 4) → first-pass scouting
5. Reuben output → Issachar (Tier 3) → analytical report compiled
6. Issachar → Zebulun (Tier 3) → routed to Asher for refinement
7. Asher (Tier 3) → refined output
8. Asher → Simeon (Tier 2) → compliance audit
9. Simeon → Tier 1 judge (Dan or Judah) → final ruling
10. Tier 1 → Levi (memory record) + Moses (final summary)
```

### Escalation Paths
All escalations follow OL-003 (Proportional Escalation).

```
Tier 4 failure  →  Gad (recovery attempt)
Gad failure     →  Tier 3 judge (Issachar or Zebulun)
Tier 3 conflict →  Simeon (compliance check)
Simeon block    →  Dan (ruling)
Dan ruling      →  escalate_to_moses if mission-critical
Moses silence   →  OL-004: conservative action, Theme 5 default
```

### Error Recovery
- Any tribe that sets `tribe_error` routes to Gad.
- Gad attempts recovery. If Gad fails, escalation continues upward to Dan.

### Routing Signals
Agents communicate routing via these state fields:
- `next_node` — explicit next node override (consumed once, then cleared)
- `escalate` — if true, route task up one Jethro tier
- `escalation_reason` — human-readable reason for escalation
- `tribe_error` — triggers Gad recovery
- `hermes_fallback` — if true, return to original tribal node after Hermes failure

---

## Hermes Parallel Pipeline

Hermes Agent (Nous Research) runs as a **parallel Tier 4 executor** alongside the standard tribal agents. It does not replace any tribe — it is delegated to by `hermes_eligible` tribes.

### Eligible Tribes → Hermes Skills

| Tribe | Hermes Skills | Rationale |
|-------|--------------|-----------|
| Naphtali | `hermes-web-search-plus`, `execplan-skill` | Real-time search + task lifecycle management |
| Reuben | `hermes-web-search-plus`, `flowstate-qmd` | First-pass exploration + anticipatory memory pre-fetch |
| Asher | `maestro`, `execplan-skill` | Multi-pass refinement via Conductor planning |

### Constitution Enforcement on Hermes

Hermes runs with `--no-learn --non-interactive --json-output`. Enforced commandments:

**Pre-call:** C3 (mandate check), C8 (scope check)
**Post-call:** C2 (no fabrication), C5 (structured output), C7 (transform logging)

### Hermes Fallback Policy
- **Timeout:** Return control to original tribal node.
- **Constitution violation:** Escalate to Tier 3 judge per C6.
- **Error:** Return control to original tribal node.
- All failures logged.

Full config: [`config/hermes_pipeline.yaml`](../../config/hermes_pipeline.yaml)

---

## SLAs

| Tier | Response Time |
|------|--------------|
| Moses (OL-004) | 300s |
| Tier 1 | 60s |
| Tier 2 | 45s |
| Tier 3 | 30s |
| Tier 4 | 20s |
| Hermes fallback | 10s |

Config: [`config/mission.yaml`](../../config/mission.yaml)
