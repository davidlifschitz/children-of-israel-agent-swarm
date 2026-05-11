# Package Ownership

| Package | Owns | May Import |
| --- | --- | --- |
| `coi_contracts` | Shared dataclass contracts and repository protocols | stdlib only |
| `coi_runtime` | Runtime backend interfaces, mock/Ollama/Hermes adapters, tier profiles | `coi_contracts` |
| `coi_law_engine` | Law/config YAML artifact loading and verdict evaluation | `coi_contracts` |
| `coi_storage` | In-memory and file-backed repositories | `coi_contracts` |
| `coi_orchestrator` | Run lifecycle, routing, compliance stage, memory stage, summaries | contracts, runtime, law engine, storage |
| `coi_api` | Local HTTP control plane | contracts, orchestrator |
| `coi_integrations` | ScheduleOS-facing adapter and shell result shape | orchestrator |

`scripts/check_import_boundaries.py` enforces this map.

