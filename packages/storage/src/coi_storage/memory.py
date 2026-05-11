from __future__ import annotations

from dataclasses import dataclass, field

from coi_contracts import CheckpointRecord, Event, PrecedentRecord, Run


@dataclass(slots=True)
class InMemoryStorage:
    runs: dict[str, Run] = field(default_factory=dict)
    events: dict[str, list[Event]] = field(default_factory=dict)
    checkpoints: dict[str, list[CheckpointRecord]] = field(default_factory=dict)
    precedents: list[PrecedentRecord] = field(default_factory=list)

    def create(self, run: Run) -> Run:
        self.runs[run.run_id] = run
        return run

    def update(self, run: Run) -> Run:
        self.runs[run.run_id] = run
        return run

    def get(self, run_id: str) -> Run | None:
        return self.runs.get(run_id)

    def list(self) -> list[Run]:
        return sorted(self.runs.values(), key=lambda run: run.created_at)

    def append(self, event: Event) -> Event:
        self.events.setdefault(event.run_id, []).append(event)
        return event

    def list_by_run(self, run_id: str) -> list[Event]:
        return list(self.events.get(run_id, []))

    def save(self, checkpoint: CheckpointRecord | PrecedentRecord) -> CheckpointRecord | PrecedentRecord:
        if isinstance(checkpoint, CheckpointRecord):
            self.checkpoints.setdefault(checkpoint.run_id, []).append(checkpoint)
            return checkpoint
        self.precedents.append(checkpoint)
        return checkpoint

    def get_latest(self, run_id: str) -> CheckpointRecord | None:
        records = self.checkpoints.get(run_id, [])
        return records[-1] if records else None

    def list_by_rule(self, rule_id: str | None = None) -> list[PrecedentRecord]:
        if rule_id is None:
            return list(self.precedents)
        return [record for record in self.precedents if record.rule_id == rule_id]

