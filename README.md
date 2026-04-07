# Children of Israel - Agent Swarm

A massive AI agent swarm structured around the organizational and legal framework of the Children of Israel. Jewish tradition serves as architectural inspiration - not literal implementation - for governance, agent personas, and orchestration.

## Project Vision

We are building a swarm of potentially hundreds of thousands of agents organized into a hierarchical, law-governed system. The architecture draws from:

- The Ten Commandments: Universal agent constitution (hard constraints, every agent, always)
- The 613 Commandments: Granular behavioral directives organized across 6 themes
- The Oral Law: Interpretive conflict resolution layer (BMAD-style meta-rules)
- The 12 Tribes: Tribal agent archetypes with distinct personalities and domains
- The Jethro Hierarchy: The Exodus organizational model as the orchestration tree
- Hermes Agent: Parallel pipeline executor for hermes_eligible tribes (Reuben, Naphtali, Asher)

Tech Stack: Python, LangGraph, Hermes Agent (Nous Research), Model-agnostic LLM backend, Postgres/Redis checkpointing

## Repository Structure

```
children_of_israel/
|-- moses.py                   # Root human-in-the-loop node
|-- composer.py                # Runtime assembly of tribal subgraphs
|-- agent_state.py             # Typed AgentState schema
|-- hermes_node.py             # Hermes parallel pipeline executor (Session 8)
|-- tribes/
|   |-- tribes.yaml
|   |-- tribe_reuben.py
|   |-- tribe_simeon.py
|   |-- tribe_levi.py
|   |-- tribe_judah.py
|   |-- tribe_issachar.py
|   |-- tribe_zebulun.py
|   |-- tribe_dan.py
|   |-- tribe_naphtali.py
|   |-- tribe_gad.py
|   |-- tribe_asher.py
|   |-- tribe_joseph.py
|   `-- tribe_benjamin.py
|-- law/
|   |-- constitution.yaml
|   |-- commandments.yaml
|   `-- oral_law.yaml
|-- docs/
|   `-- jethro_hierarchy.md
`-- config/
    |-- mission.yaml
    `-- hermes_pipeline.yaml   # Hermes integration config (Session 8)
```

## The Law Layer

### Three-Tier Architecture

| Layer | Description | Enforcement |
|---|---|---|
| Ten Commandments | Universal constitution | Hard constraints - non-negotiable, every agent, always |
| 613 Commandments | 6 themes x ~100 directives | Full set inherited; active enforcement depends on role/context |
| Oral Law | BMAD-style meta-rules | Conflict resolution - context first, escalate second |

### The 6 Themes of the 613 Commandments

| # | Theme | Description |
|---|---|---|
| 1 | Perception | What an agent receives shapes everything it does |
| 2 | Communication | How agents speak, report, and stay silent |
| 3 | Justice & Decision-Making | How agents reason, decide, and rule |
| 4 | Relationships & Delegation | How agents trust, assign, and collaborate |
| 5 | Integrity & Purity | How agents maintain honesty and data fidelity |
| 6 | Alignment & Mission | How agents stay true to the overarching goal |

## The 12 Tribes

| Tribe | Archetype | Primary Domain | Jethro Tier | Hermes Eligible |
|---|---|---|---|---|
| Reuben | Pioneer / Scout | Exploration, first-pass analysis | Leaf | ✅ |
| Simeon | Zealot / Enforcer | Compliance, auditing, rule enforcement | Mid | ❌ |
| Levi | Priest / Steward | Memory, system integrity, record-keeping | Senior (cross-tier) | ❌ |
| Judah | Commander / Leader | Command coordination, execution, ownership | Senior | ❌ |
| Issachar | Scholar / Analyst | Deep research, pattern recognition | Mid | ❌ |
| Zebulun | Merchant / Connector | Resource exchange, inter-tribal coordination | Mid (tribal boundary) | ❌ |
| Dan | Judge / Arbitrator | Conflict resolution, edge case adjudication | Senior | ❌ |
| Naphtali | Messenger / Swift | Speed-critical tasks, real-time delivery | Leaf | ✅ |
| Gad | Warrior / Resilience | Error recovery, fault tolerance, adversarial handling | Leaf + Mid | ❌ |
| Asher | Optimizer / Enricher | Output quality, refinement, polishing | Mid (final pass) | ✅ |
| Joseph | Visionary / Planner | Strategic forecasting, long-range planning | Senior (advises top) | ❌ |
| Benjamin | Guardian / Protector | Security, trust verification, agent protection | Leaf + Senior | ❌ |

## The Jethro Hierarchy (5-Tier Orchestration)

| Tier | Name | Tribes | Responsibility |
|---|---|---|---|
| Root | Moses | - | Human-in-the-loop. Issues mission, receives final summary |
| Tier 1 | Commanders of Thousands | Judah, Joseph, Dan, Levi | Senior judges. Oversee major domain clusters |
| Tier 2 | Commanders of Hundreds | Mid-senior agents | Aggregate from Tier 3. Handle unresolved escalations |
| Tier 3 | Commanders of Fifties | Issachar, Zebulun, Simeon, Asher | First compression layer. Summarizes raw leaf outputs |
| Tier 4 | Commanders of Tens | Reuben, Naphtali, Gad, Benjamin, **Hermes** | Leaf executors. Fully parallel. Gad auto-replaces failures. Hermes runs as parallel branch for eligible tribes |

## Hermes Pipeline (Session 8)

Hermes Agent (by Nous Research) runs as a **parallel Tier 4 executor** alongside the LangGraph tribal nodes. It does not replace any tribe — it is delegated to by `hermes_eligible` tribes when their task profile matches Hermes's strengths.

### Eligible Tribes

| Tribe | Hermes Skills | Rationale |
|---|---|---|
| Naphtali | `hermes-web-search-plus`, `execplan-skill` | Real-time search + task lifecycle management |
| Reuben | `hermes-web-search-plus`, `flowstate-qmd` | First-pass exploration + anticipatory memory pre-fetch |
| Asher | `maestro`, `execplan-skill` | Multi-pass refinement via Conductor planning |

### Constitution Enforcement

Hermes runs with `--no-learn --non-interactive --json-output`. The following commandments are enforced as hard filters on every Hermes call:

- **Pre-call:** Commandment 3 (mandate check), Commandment 8 (scope check)
- **Post-call:** Commandment 2 (no fabrication), Commandment 5 (structured output), Commandment 7 (transform logging)

On failure, the fallback policy returns control to the original tribal LangGraph node.

See [`config/hermes_pipeline.yaml`](config/hermes_pipeline.yaml) and [`children_of_israel/hermes_node.py`](children_of_israel/hermes_node.py) for full implementation.

## Session Roadmap

| Session | Topic | Status |
|---|---|---|
| Session 1 | The Law Layer - Ten Commandments + 613 subcategory structure | Complete |
| Session 2 | The 12 Tribes - tribal personas and archetypes | Complete |
| Session 3 | The Jethro Hierarchy - LangGraph orchestration architecture | Complete |
| Session 4 | Write the full 613 directives (6 themes x ~100) | Complete |
| Session 5 | The Oral Law layer - BMAD + conflict resolution | Complete |
| Session 6 | Integration - wiring law layer into LangGraph agent nodes | Complete |
| Session 7 | Scaling - Kubernetes / distributed infrastructure | Complete |
| Session 8 | Hermes Integration - parallel pipeline, skill mapping, constitution enforcement | Complete |

## Prerequisites

This project uses [`uv`](https://github.com/astral-sh/uv) for Python dependency management. Hermes Agent is an **external system tool** installed separately — it is not a PyPI package.

### 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install Hermes Agent (Linux / macOS / WSL2)

```bash
make install-hermes
```

Or manually:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

> **Note:** Native Windows is not supported by Hermes Agent. Use WSL2 on Windows.

### 3. Install Python dependencies

```bash
uv sync           # install all runtime deps
uv sync --extra dev  # include pytest and dev tools
```

## Getting Started

```bash
git clone https://github.com/davidlifschitz/children-of-israel-agent-swarm.git
cd children-of-israel-agent-swarm
uv sync --extra dev
```

## Running the Swarm

```bash
# Run a mission
uv run python run_swarm.py --mission "Analyze the current state of our knowledge base"

# Run with a specific session ID (for checkpointing)
uv run python run_swarm.py --mission "..." --session-id my-session-001

# Resume a previous session
uv run python run_swarm.py --resume my-session-001
```

## Running Tests

```bash
uv run pytest tests/
uv run pytest tests/ -v    # verbose
uv run pytest tests/ -x    # stop on first failure
```

## Running in Production

### Docker

```bash
# Build and run locally
docker build -t children-of-israel-swarm .
docker compose up

# Run a mission via docker
docker compose run swarm --mission "Summarize the swarm state"
```

### Kubernetes

```bash
# Deploy to a cluster (requires kubectl configured)
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml   # copy from secrets-template.yaml first
kubectl apply -f k8s/swarm-deployment.yaml
kubectl apply -f k8s/tier4-hpa.yaml

# Check health
kubectl get pods -n children-of-israel
kubectl port-forward svc/swarm-service 8000:80 -n children-of-israel
curl http://localhost:8000/health
```

Children of Israel Agent Swarm - Session 8 complete
