# CLAUDE.md — Children of Israel Agent Swarm

This file is read by Claude Code at the start of every session.

---

## Pre-PR Health Check

Run this before every pull request. All checks must pass.

```bash
# 1. Tests — must be 33 passed, 0 failed, 0 xfail
pytest tests/ -v

# 2. Law layer — YAML must parse and have all 6 themes + 630 directives
python3 -c "
import yaml
data = yaml.safe_load(open('law/commandments.yaml').read())
themes = data['themes']
total = sum(sum(len(sc['directives']) for sc in t['subcategories']) for t in themes)
assert len(themes) == 6, f'Expected 6 themes, got {len(themes)}'
assert total >= 600, f'Expected 600+ directives, got {total}'
print(f'OK — {len(themes)} themes, {total} directives')
"

# 3. Core imports — all key modules must be importable without error
python3 -c "
from children_of_israel.constitution_enforcer import enforcer
from children_of_israel.oral_law_engine import oral_law_engine
from children_of_israel.precedent_store import precedent_store
from children_of_israel.commandment_advisor import advisor
from children_of_israel.checkpointing import get_checkpointer
from children_of_israel.observability import get_logger
print('OK — all core modules import cleanly')
"

# 4. Graph builds — LangGraph graph must compile without error
python3 -c "
from children_of_israel.composer import build_graph
g = build_graph()
print(f'OK — graph compiled: {type(g).__name__}')
"

# 5. CLI help — entry point must be runnable
python3 run_swarm.py --help

# 6. No uncommitted changes
git status --short && echo 'OK — working tree clean'
```

### Expected output summary

| Check | Expected |
|-------|----------|
| `pytest tests/` | `33 passed` |
| Law layer | `6 themes, 630 directives` |
| Core imports | `OK — all core modules import cleanly` |
| Graph build | `OK — graph compiled: CompiledStateGraph` |
| CLI help | Usage text printed, exit 0 |
| Git status | No output (clean) |

---

## Repository Structure

```
children_of_israel/       # Core Python package
├── agent_state.py        # Shared AgentState TypedDict
├── composer.py           # LangGraph graph assembly + routing
├── moses.py              # Root human-in-the-loop node
├── llm.py                # Provider-agnostic LLM wrapper
├── hermes_node.py        # Hermes parallel pipeline executor
├── constitution_enforcer.py  # Runtime 10 Commandments enforcement
├── oral_law_engine.py    # Executable OL-001 to OL-004
├── precedent_store.py    # Dan's ruling precedents (data/precedents.jsonl)
├── commandment_advisor.py    # Per-tribe directive index for prompt injection
├── checkpointing.py      # memory / postgres / redis backend factory
├── observability.py      # structlog JSON logging
├── health.py             # FastAPI /health endpoint
└── tribes/               # 12 tribal agent nodes

law/
├── constitution.yaml     # 10 Commandments (hard constraints)
├── commandments.yaml     # 630 directives across 6 themes
└── oral_law.yaml         # OL-001 to OL-004 meta-rules

config/
├── mission.yaml          # SLAs, model routing, checkpointing backend
└── hermes_pipeline.yaml  # Hermes skill mapping

k8s/                      # Kubernetes manifests
tests/                    # pytest suite (33 tests)
run_swarm.py              # CLI entry point
```

## Running the Swarm

```bash
python run_swarm.py --mission "Your mission here"
python run_swarm.py --mission "..." --session-id my-session-001
python run_swarm.py --resume my-session-001
```

## Key Architectural Rules

- **Never bypass the Jethro hierarchy.** All escalations must follow tier order.
- **All tribe node functions must call `enforcer.enforce(state, result)` after the LLM call.** This enforces the 10 Commandments at runtime.
- **Dan is the only judge who writes precedents.** Use `oral_law_engine.log_precedent()` in `tribe_dan.py` only.
- **Levi writes the audit log.** `data/audit_log.jsonl` is append-only. Never truncate or overwrite it.
- **`data/` is gitignored.** Runtime files (audit logs, precedents) are never committed.
