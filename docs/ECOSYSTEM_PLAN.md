# Ecosystem Integration Plan

## Role in the ecosystem

[children-of-israel-agent-swarm](https://github.com/davidlifschitz/children-of-israel-agent-swarm) should be the heavy execution layer for the ecosystem: long-running missions, parallel work, structured verification, and artifact production.

## Connected repos

- [agentic-os](https://github.com/davidlifschitz/agentic-os) — defines task and artifact contracts
- [ScheduleOS](https://github.com/davidlifschitz/ScheduleOS) — operator shell that submits missions here
- [graphify](https://github.com/davidlifschitz/graphify) — context source to load before execution
- [autoresearch-genealogy](https://github.com/davidlifschitz/autoresearch-genealogy) — first domain skill pack / mission template
- [workout-planner](https://github.com/davidlifschitz/workout-planner) — target for generated planning artifacts
- [Bttr](https://github.com/davidlifschitz/Bttr) — target for structured outcome events
- [fastest-growing-finance-repos](https://github.com/davidlifschitz/fastest-growing-finance-repos) — reporting/publishing target for finance workflows

## How the swarm should connect

### 1. Accept standard task payloads

Consume:

- `agentic-os/schemas/task.schema.json`

Purpose:

- accept ecosystem work in one standard format
- allow multiple callers, especially [ScheduleOS](https://github.com/davidlifschitz/ScheduleOS), to submit jobs consistently

### 2. Emit standard artifacts

Produce:

- outputs matching `agentic-os/schemas/artifact.schema.json`

Purpose:

- make outputs reusable by downstream systems
- avoid bespoke parsing between repos

### 3. Load graph context before mission execution

Consume summaries produced by [graphify](https://github.com/davidlifschitz/graphify).

Purpose:

- understand repo structure before editing or analyzing
- reduce blind execution
- improve accuracy in code, research, and refactor missions

### 4. Use skill packs for domain-specific missions

Consume domain instructions from repos like [autoresearch-genealogy](https://github.com/davidlifschitz/autoresearch-genealogy).

Purpose:

- separate orchestration logic from domain knowledge
- allow reusable vertical mission packs

## Files to add next

- `integrations/task_contracts.py`
- `integrations/artifact_writer.py`
- `integrations/graphify_context.py`
- `missions/research_mission.py`
- `missions/implementation_mission.py`
- `missions/publishing_mission.py`
- `docs/integration.md`

## Example flows

### Repo execution flow

1. [ScheduleOS](https://github.com/davidlifschitz/ScheduleOS) submits a task
2. task is validated against the shared task schema from [agentic-os](https://github.com/davidlifschitz/agentic-os)
3. graph context is pulled from [graphify](https://github.com/davidlifschitz/graphify)
4. the proper mission template runs
5. outputs are emitted as standard artifacts
6. downstream systems consume those artifacts

### Research flow

1. domain skill pack from [autoresearch-genealogy](https://github.com/davidlifschitz/autoresearch-genealogy) defines workflow rules
2. the swarm executes the research mission
3. artifacts are returned to the calling system

## Acceptance criteria

- swarm can validate incoming ecosystem tasks
- swarm can emit standard artifacts
- swarm can load graph summaries before mission execution
- swarm can run domain-specific mission templates without hardcoding those rules into core orchestration
