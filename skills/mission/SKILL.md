---
name: children-of-israel-mission
description: >
  End-to-end mission execution spec for the Children of Israel agent swarm.
  Describes how to accept a mission, decompose it, execute through the
  Jethro hierarchy, enforce governance at every step, and return a
  structured summary. Hand this to any orchestrator agent.
---

# Mission Execution

This skill tells you how to run a complete mission through the Children of Israel swarm.

## Mission State Schema

Every mission maintains this shared state. All agents read from and write to it.

```
mission            — top-level mission string issued by Moses
mandate            — explicit task mandate for the current node (required by C3)
task               — concrete task string passed to the active node
current_tribe      — id of the tribe currently handling the task
next_node          — explicit next node override (consumed once, then cleared)
escalate           — if true, route task up the Jethro hierarchy
escalation_reason  — human-readable reason for escalation
output             — final output from the active node
tribe_output       — raw output from the tribal agent
tribe_error        — error string if tribal agent failed
hermes_output      — parsed JSON output from Hermes node
hermes_fallback    — true = Hermes failed, fall back to tribal node
hermes_error       — error string from Hermes node
jethro_tier        — tier of the current active node (0–4)
originating_tier   — tier where the task originated
session_id         — unique session identifier for checkpointing
constitution_violations — log of any commandment violations encountered
oral_law_precedents     — Dan precedent IDs applied this session (OL-002)
human_input        — raw human input at the Moses node
final_summary      — final summary returned to Moses at session end
```

## Execution Flow

### 1. Mission Intake (Moses)
- Receive human input.
- Validate: input must be non-empty and clear (C5).
- Issue mandate: `"MISSION ISSUED BY MOSES: {input}"`.
- Initialize state: `jethro_tier=0`, `escalate=false`, all error fields null.

### 2. Decomposition (Judah — Tier 1)
- Judah receives the mandate and decomposes into subtasks.
- Each subtask is dispatched to the appropriate Tier 3 tribe.
- Judah owns the execution plan and tracks completion.

### 3. Execution (Tiers 3 → 4)
For each subtask:
1. Tier 3 tribe (Issachar/Zebulun/Asher) receives task.
2. If research is needed: dispatch to Tier 4 (Reuben for scouting).
3. Tier 4 executes and returns output.
4. If Hermes-eligible: parallel Hermes branch runs simultaneously.
   - On Hermes success: use Hermes output.
   - On Hermes failure: fall back to tribal output.
5. Tier 3 compiles analytical report from raw outputs.
6. Asher refines output (final pass).

### 4. Compliance Audit (Simeon — Tier 2)
- Every output passes through Simeon before reaching Tier 1.
- Simeon audits against the law layer (constitution + directives).
- Violations: block and escalate.
- Clean outputs: pass through to Tier 1.

### 5. Final Ruling (Tier 1)
- Dan issues rulings on any conflicts or escalations.
- Levi records the session (audit log, precedents).
- A summarizer compiles the final output.

### 6. Summary (Moses)
- Moses receives `final_summary`.
- Present to human operator.
- Session ends.

## Per-Agent Checklist

Every agent, every step:
1. ✓ Verify mandate exists (C3)
2. ✓ Confirm tier assignment (C4)
3. ✓ Check task is within scope (C8)
4. ✓ Execute with tribal persona
5. ✓ Validate output structure (C5)
6. ✓ Check for fabrication (C2)
7. ✓ Ensure JSON-serializable (C7)
8. ✓ Log any violations
9. ✓ Clear `next_node` after consuming
10. ✓ Set `escalate=true` if you cannot resolve

## Output Format

Every tribal agent returns structured JSON:

```json
{
  "tribe": "<tribe_id>",
  "output_type": "<type>",
  "summary": "<one paragraph>",
  ...tribe-specific fields...,
  "escalate": false
}
```

The final session summary follows this format:

```json
{
  "final_summary": "<multi-paragraph summary>",
  "accomplished": ["<item 1>"],
  "unresolved": [],
  "recommended_next": "<string>"
}
```

## Error Recovery

```
Any tribe fails → tribe_error set → route to Gad
Gad attempts recovery → success: continue → failure: escalate to Tier 3
Hermes fails → hermes_fallback=true → return to original tribal node
Constitution violation → log + escalate per C6
```

## Ecosystem Integration

This swarm accepts standard task payloads from [agentic-os](https://github.com/davidlifschitz/agentic-os) and emits standard artifacts. It can be called by [ScheduleOS](https://github.com/davidlifschitz/ScheduleOS), load context from [graphify](https://github.com/davidlifschitz/graphify), and run domain-specific skill packs from repos like [autoresearch-genealogy](https://github.com/davidlifschitz/autoresearch-genealogy).

See [`docs/ECOSYSTEM_PLAN.md`](../../docs/ECOSYSTEM_PLAN.md) for full integration details.
