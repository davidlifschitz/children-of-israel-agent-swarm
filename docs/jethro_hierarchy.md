# Jethro Hierarchy — Architecture Reference

The Jethro Hierarchy is the orchestration backbone of the Children of Israel Agent Swarm.
It is derived from Exodus 18, where Jethro advises Moses to delegate judgment across a
tiered structure rather than handling all cases himself.

This document is the canonical architecture reference for the 5-tier orchestration model.

---

## The Five Tiers

```
                          ┌───────────────┐
                          │     MOSES      │  ← Root (Human-in-the-loop)
                          └───────────────┘
                                 │
           ┌───────────────────┴──────────────────┐
           │                   Tier 1                    │
           │     Judah  │  Joseph  │  Dan  │  Levi        │
           │     (Cmd)  │ (Vision) │ (Judge)│ (Memory)    │
           └───────────────────┬──────────────────┘
                                   │
           ┌───────────────────┴──────────────────┐
           │                   Tier 2                    │
           │                  Simeon                     │
           │              (Compliance Audit)              │
           └───────────────────┬──────────────────┘
                                   │
      ┌───────────────────────┴───────────────────────┐
      │                       Tier 3                          │
      │   Issachar (Research)  │  Zebulun (Coord)  │  Asher*  │
      └───────────────────────┬───────────────────────┘
                                   │
┌─────────────────────────┴─────────────────────────┐
│                         Tier 4                               │
│  Reuben*  │  Naphtali*  │  Gad  │  Benjamin  │  Hermes**  │
└───────────────────────────────────────────────────┘

* Hermes eligible (optional branch available)
** Hermes is attempted for eligible tribes when configured, then explicitly falls back to the normal tribal backend if unavailable or failed.
```

---

## Tier Descriptions

### Root — Moses
- **Role:** Human-in-the-loop. Single point of entry and exit.
- **Responsibilities:** Issue mission mandate, receive final summary, enforce OL-004 (Silence of Moses).
- **SLA:** 300 seconds. Silence triggers conservative fallback (Theme 5 — Information Integrity).
- **Implementation:** `coi_orchestrator` entrypoints plus mandate validation in `coi_law_engine`.

### Tier 1 — Commanders of Thousands
Senior judges. Handle major domain clusters and receive all unresolved escalations from Tier 2.

| Tribe | Role | Key Law |
|-------|------|---------|
| Judah | Default entry from Moses. Decomposes mission and dispatches to Tier 3. | C1, C4 |
| Joseph | Strategic advisor. Produces long-range forecasts and first concrete steps. | C1, C5, C8 |
| Dan | Judge/Arbitrator. Issues rulings and sets OL-002 precedents. | C5, C6 |
| Levi | Cross-tier memory steward. Maintains faithful records for all tiers. | C2, C7 |

### Tier 2 — Commanders of Hundreds
Compliance enforcement layer. All swarm output passes through Simeon before reaching Tier 1.

| Tribe | Role | Key Law |
|-------|------|---------|
| Simeon | Audits every output against the law layer. Blocks violations. | C2, C7 |

### Tier 3 — Commanders of Fifties
First compression layer. Aggregates Tier 4 raw outputs into structured reports for Tier 2.

| Tribe | Role | Key Law |
|-------|------|---------|
| Issachar | Deep research and pattern recognition. Dispatches to Reuben for scouting. | C2, C5, C8 |
| Zebulun | Inter-tribal coordination and resource routing. | C3, C4, C5 |
| Asher | Output refinement and polishing (final pass). Hermes eligible. | C5, C7, C8 |

### Tier 4 — Commanders of Tens
Leaf executors. Fully parallel. Gad auto-replaces failures. Hermes is an optional branch for eligible tribes and falls back to the normal tribal backend when unavailable.

| Tribe | Role | Hermes Eligible | Key Law |
|-------|------|-----------------|----------|
| Reuben | First-pass scouting and exploration. | ✅ | C2, C3, C8 |
| Naphtali | Speed-critical real-time delivery. | ✅ | C2, C5, C6 |
| Gad | Error recovery. Auto-replaces failed nodes. | ❌ | C6, C8, C9 |
| Benjamin | Security and trust verification. | ❌ | C2, C3, C9 |

---

## Escalation Paths

All escalations follow **OL-003 (Proportional Escalation)** — depth of escalation must be proportional to decision impact.

```
Tier 4 failure  →  Gad (recovery attempt)
Gad failure     →  Tier 3 judge (Issachar or Zebulun)
Tier 3 conflict →  Simeon (compliance check)
Simeon block    →  Dan (ruling)
Dan ruling      →  "escalate_to_moses" if mission-critical
Moses silence   →  OL-004: conservative action, Theme 5 default
```

**Hermes-specific escalation:**
```
Hermes C3/C8 violation  →  escalate=True →  Dan
Hermes timeout/error    →  runtime.fallback event → original tribal backend
```

---

## Oral Law Integration

| Rule | Name | Where Applied |
|------|------|---------------|
| OL-001 | Context Over Code | Tier 1 judges may suspend a directive for a specific instance |
| OL-002 | The Dan Precedent | Dan logs all rulings as precedent; lower tiers defer to them |
| OL-003 | Proportional Escalation | Escalation depth matches decision impact |
| OL-004 | Silence of Moses | 300s SLA; silence triggers Theme 5 conservative fallback |

---

## Data Flow — Typical Session

```
1. Human input → Moses → mandate issued
2. Moses → Judah (Tier 1) → mission decomposed, task dispatched
3. Judah → Issachar (Tier 3) → research task
4. Issachar → Reuben (Tier 4) → first-pass scouting
   4a. [Optional Hermes branch] Reuben eligible → Hermes adapter is attempted if configured
   4b. On success: Hermes output becomes worker output
   4c. On failure/unavailable: `runtime.fallback` event is logged and the normal tribal backend runs
5. Reuben output → Issachar (Tier 3) → analytical report compiled
6. Issachar → Zebulun (Tier 3) → routed to Asher for refinement
7. Asher (Tier 3, Hermes eligible) → refined output
8. Asher → Simeon (Tier 2) → compliance audit
9. Simeon → Tier 1 judge (Dan or Judah) → final ruling
10. Tier 1 → Levi (memory record) + Moses (final summary)
```

---

## Key Implementation Files

| File | Purpose |
|------|---------|
| `packages/orchestrator/src/coi_orchestrator/` | Run lifecycle, routing, Hermes fallback, compliance and memory stages |
| `packages/contracts/src/coi_contracts/` | Shared run, worker, event, law, and storage contracts |
| `packages/runtime/src/coi_runtime/` | Mock, Ollama, and Hermes backend adapters |
| `packages/law_engine/src/coi_law_engine/` | Law/config artifact loading and verdict evaluation |
| `packages/storage/src/coi_storage/` | In-memory and file-backed repositories |
| `skills/tribes/` | All 12 tribal persona skills |
| `law/constitution.yaml` | Ten Commandments (hard constraints) |
| `law/commandments.yaml` | 600+ granular directives |
| `law/oral_law.yaml` | BMAD meta-rules (OL-001 to OL-004) |
| `config/mission.yaml` | SLAs, model routing per tribe |
| `config/hermes_pipeline.yaml` | Hermes integration config |
