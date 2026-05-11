# Migration Map

The current repository is skills-first. Older docs and local branches referenced a Python package named `children_of_israel/`; the foundations implementation now uses explicit package ownership under `packages/`.

| Legacy Concept | Current Home |
| --- | --- |
| `children_of_israel/agent_state.py` | `coi_contracts` run, worker, event, law, and storage contracts |
| `children_of_israel/llm.py` | `coi_runtime` backend adapters and tier profiles |
| `children_of_israel/hermes_node.py` | `coi_runtime.HermesRuntimeAdapter` plus orchestrator fallback events |
| `children_of_israel/composer.py` | `coi_orchestrator.SwarmOrchestrator` |
| `children_of_israel/moses.py` | Orchestrator entrypoint plus `mandate` validation in the law engine |
| Law prompt-only checks | `coi_law_engine` typed verdicts over existing `law/` YAML |
| In-memory runtime state | `coi_storage` in-memory and file-backed repositories |

The old package is not restored as the canonical runtime. New code should import the package that owns the behavior listed above.

