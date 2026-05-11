# Children of Israel — Agent Swarm Skills

A skill pack and governance framework for AI agent swarms. Jewish tradition serves as architectural inspiration for agent personas, hierarchical orchestration, and a three-tier legal system.

The repo is still skills-first: the skills, laws, and configuration are the product source of truth. It also includes a minimal local execution layer so maintainers can validate contracts, run a mock bootstrap task, inspect events, and expose a small API without ScheduleOS, graphify, or live model services.

## Quick Start

Point your agent at this repo. The skills are self-describing and follow the [Caveman SKILL.md](https://github.com/JuliusBrussee/caveman) convention — each has YAML frontmatter (`name`, `description`) and structured instructions.

```
# Give the whole repo to your agent
"Read this repo. You are operating as the Children of Israel agent swarm.
 Follow the governance framework in skills/governance/ and adopt the
 tribal persona assigned to you from skills/tribes/."
```

## Repository Structure

```
skills/
├── governance/SKILL.md              # Three-tier law layer (Constitution + Oral Law)
├── orchestration/SKILL.md           # Jethro 5-tier hierarchy + Hermes pipeline
├── mission/SKILL.md                 # End-to-end mission execution spec
└── tribes/
    ├── reuben/SKILL.md              # Pioneer / Scout (Tier 4, Hermes eligible)
    ├── simeon/SKILL.md              # Zealot / Enforcer (Tier 2)
    ├── levi/SKILL.md                # Priest / Steward (Tier 1, cross-tier)
    ├── judah/SKILL.md               # Commander / Leader (Tier 1)
    ├── issachar/SKILL.md            # Scholar / Analyst (Tier 3)
    ├── zebulun/SKILL.md             # Merchant / Connector (Tier 3)
    ├── dan/SKILL.md                 # Judge / Arbitrator (Tier 1)
    ├── naphtali/SKILL.md            # Messenger / Swift (Tier 4, Hermes eligible)
    ├── gad/SKILL.md                 # Warrior / Resilience (Tier 4)
    ├── asher/SKILL.md               # Optimizer / Enricher (Tier 3, Hermes eligible)
    ├── joseph/SKILL.md              # Visionary / Planner (Tier 1)
    └── benjamin/SKILL.md            # Guardian / Protector (Tier 4)

law/
├── constitution.yaml                # Ten Commandments (hard constraints)
├── commandments.yaml                # 630 directives across 6 themes
├── oral_law.yaml                    # OL-001 to OL-004 meta-rules
└── tribes/tribes.yaml               # Tribal archetypes and config

config/
├── mission.yaml                     # SLAs, model routing, checkpointing
└── hermes_pipeline.yaml             # Hermes skill mapping + constitution enforcement

packages/
├── contracts/                       # Run, worker, event, law, storage contracts
├── runtime/                         # Mock, Ollama, and Hermes runtime adapters
├── orchestrator/                    # Local lifecycle owner and demo CLI
├── law_engine/                      # YAML artifact loader + verdict evaluator
├── storage/                         # In-memory and file-backed repositories
├── api/                             # Local HTTP control plane
└── integrations/                    # ScheduleOS-facing adapter

docs/
├── jethro_hierarchy.md              # Architecture reference
├── ECOSYSTEM_PLAN.md                # Ecosystem integration plan
└── integration.md                   # Delegated execution spec

missions/                            # Mission templates (extensible)
integrations/                        # Integration adapters (extensible)
```

## The Three-Tier Law Layer

| Layer | What | How |
|-------|------|-----|
| **Ten Commandments** | 10 universal hard constraints | Non-negotiable. Every agent. Always. |
| **630 Directives** | 6 themes × ~105 behavioral rules | Inherited by all; active enforcement depends on role/context. |
| **Oral Law** | 4 BMAD-style meta-rules | Context-first conflict resolution (OL-001 to OL-004). |

See [`skills/governance/SKILL.md`](skills/governance/SKILL.md) for the full framework.

## The 12 Tribes

| Tribe | Archetype | Tier | Hermes |
|-------|-----------|------|--------|
| Reuben | Pioneer / Scout | 4 | Yes |
| Simeon | Zealot / Enforcer | 2 | No |
| Levi | Priest / Steward | 1 | No |
| Judah | Commander / Leader | 1 | No |
| Issachar | Scholar / Analyst | 3 | No |
| Zebulun | Merchant / Connector | 3 | No |
| Dan | Judge / Arbitrator | 1 | No |
| Naphtali | Messenger / Swift | 4 | Yes |
| Gad | Warrior / Resilience | 4 | No |
| Asher | Optimizer / Enricher | 3 | Yes |
| Joseph | Visionary / Planner | 1 | No |
| Benjamin | Guardian / Protector | 4 | No |

Each tribe has its own SKILL.md in `skills/tribes/<name>/` with persona, constraints, output format, and routing rules.

## The Jethro Hierarchy (5-Tier Orchestration)

| Tier | Name | Tribes |
|------|------|--------|
| Root | Moses | Human-in-the-loop |
| 1 | Commanders of Thousands | Judah, Joseph, Dan, Levi |
| 2 | Commanders of Hundreds | Simeon |
| 3 | Commanders of Fifties | Issachar, Zebulun, Asher |
| 4 | Commanders of Tens | Reuben, Naphtali, Gad, Benjamin |

See [`skills/orchestration/SKILL.md`](skills/orchestration/SKILL.md) for the full hierarchy, routing rules, and Hermes pipeline.

## Ecosystem

This skill pack integrates with:
- [agentic-os](https://github.com/davidlifschitz/agentic-os) — task and artifact contracts
- [ScheduleOS](https://github.com/davidlifschitz/ScheduleOS) — operator shell that submits missions
- [graphify](https://github.com/davidlifschitz/graphify) — context source for pre-execution loading
- [autoresearch-genealogy](https://github.com/davidlifschitz/autoresearch-genealogy) — domain skill pack

See [`docs/ECOSYSTEM_PLAN.md`](docs/ECOSYSTEM_PLAN.md) for integration details.

## Local Execution

```bash
uv sync --extra dev
uv run python scripts/check_import_boundaries.py
uv run --extra dev pytest
uv run coi-demo --task examples/tasks/local_bootstrap.task.json --output-dir .coi-demo
```

The demo emits `task-run`, `execution-log`, `result-bundle`, and `summary.json` artifacts locally. See [`docs/development.md`](docs/development.md) for API, ScheduleOS adapter, and live Ollama commands.

## License

See [LICENSE](LICENSE).
