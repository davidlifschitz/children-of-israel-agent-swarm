# Children of Israel - Agent Swarm

A massive AI agent swarm structured around the organizational and legal framework of the Children of Israel. Jewish tradition serves as architectural inspiration - not literal implementation - for governance, agent personas, and orchestration.

## Project Vision

We are building a swarm of potentially hundreds of thousands of agents organized into a hierarchical, law-governed system. The architecture draws from:

- The Ten Commandments: Universal agent constitution (hard constraints, every agent, always)
- The 613 Commandments: Granular behavioral directives organized across 6 themes
- The Oral Law: Interpretive conflict resolution layer (BMAD-style meta-rules)
- The 12 Tribes: Tribal agent archetypes with distinct personalities and domains
- The Jethro Hierarchy: The Exodus organizational model as the orchestration tree

Tech Stack: Python, LangGraph, Model-agnostic LLM backend, Postgres/Redis checkpointing

---

## Repository Structure

```
children_of_israel/
|-- moses.py                  # Root human-in-the-loop node
|-- composer.py               # Runtime assembly of tribal subgraphs
|-- agent_state.py            # Typed AgentState schema
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
    `-- mission.yaml
```

---

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

---

## The 12 Tribes

| Tribe | Archetype | Primary Domain | Jethro Tier |
|---|---|---|---|
| Reuben | Pioneer / Scout | Exploration, first-pass analysis | Leaf |
| Simeon | Zealot / Enforcer | Compliance, auditing, rule enforcement | Mid |
| Levi | Priest / Steward | Memory, system integrity, record-keeping | Senior (cross-tier) |
| Judah | Commander / Leader | Command coordination, execution, ownership | Senior |
| Issachar | Scholar / Analyst | Deep research, pattern recognition | Mid |
| Zebulun | Merchant / Connector | Resource exchange, inter-tribal coordination | Mid (tribal boundary) |
| Dan | Judge / Arbitrator | Conflict resolution, edge case adjudication | Senior |
| Naphtali | Messenger / Swift | Speed-critical tasks, real-time delivery | Leaf |
| Gad | Warrior / Resilience | Error recovery, fault tolerance, adversarial handling | Leaf + Mid |
| Asher | Optimizer / Enricher | Output quality, refinement, polishing | Mid (final pass) |
| Joseph | Visionary / Planner | Strategic forecasting, long-range planning | Senior (advises top) |
| Benjamin | Guardian / Protector | Security, trust verification, agent protection | Leaf + Senior |

---

## The Jethro Hierarchy (5-Tier Orchestration)

| Tier | Name | Tribes | Responsibility |
|---|---|---|---|
| Root | Moses | - | Human-in-the-loop. Issues mission, receives final summary |
| Tier 1 | Commanders of Thousands | Judah, Joseph, Dan, Levi | Senior judges. Oversee major domain clusters |
| Tier 2 | Commanders of Hundreds | Mid-senior agents | Aggregate from Tier 3. Handle unresolved escalations |
| Tier 3 | Commanders of Fifties | Issachar, Zebulun, Simeon, Asher | First compression layer. Summarizes raw leaf outputs |
| Tier 4 | Commanders of Tens | Reuben, Naphtali, Gad, Benjamin | Leaf executors. Fully parallel. Gad auto-replaces failures |

---

## Session Roadmap

| Session | Topic | Status |
|---|---|---|
| Session 1 | The Law Layer - Ten Commandments + 613 subcategory structure | Complete |
| Session 2 | The 12 Tribes - tribal personas and archetypes | Complete |
| Session 3 | The Jethro Hierarchy - LangGraph orchestration architecture | Complete |
| Session 4 | Write the full 613 directives (6 themes x ~100) | In Progress |
| Session 5 | The Oral Law layer - BMAD + conflict resolution | Pending |
| Session 6 | Integration - wiring law layer into LangGraph agent nodes | Pending |
| Session 7 | Scaling - Kubernetes / distributed infrastructure | Pending |

---

## Getting Started

```bash
git clone https://github.com/davidlifschitz/children-of-israel-agent-swarm.git
cd children-of-israel-agent-swarm
pip install -r requirements.txt
```

---

Children of Israel Agent Swarm - Session 4 in progress
