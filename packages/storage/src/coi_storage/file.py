from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any

from coi_contracts import (
    CheckpointRecord,
    Event,
    PrecedentRecord,
    Run,
    event_from_dict,
    run_from_dict,
    to_jsonable,
)


@dataclass(slots=True)
class FileStorage:
    root: Path
    _lock: RLock = field(init=False, repr=False)

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._lock = RLock()
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def runs_path(self) -> Path:
        return self.root / "runs.json"

    @property
    def events_path(self) -> Path:
        return self.root / "events.jsonl"

    @property
    def checkpoints_path(self) -> Path:
        return self.root / "checkpoints.json"

    @property
    def precedents_path(self) -> Path:
        return self.root / "precedents.jsonl"

    def create(self, run: Run) -> Run:
        with self._lock:
            runs = self._read_runs()
            runs[run.run_id] = run
            self._write_json(self.runs_path, {key: to_jsonable(value) for key, value in runs.items()})
        return run

    def update(self, run: Run) -> Run:
        return self.create(run)

    def get(self, run_id: str) -> Run | None:
        with self._lock:
            return self._read_runs().get(run_id)

    def list(self) -> list[Run]:
        with self._lock:
            return sorted(self._read_runs().values(), key=lambda run: run.created_at)

    def append(self, event: Event) -> Event:
        with self._lock:
            with self.events_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(to_jsonable(event), sort_keys=True) + "\n")
        return event

    def list_by_run(self, run_id: str) -> list[Event]:
        with self._lock:
            if not self.events_path.exists():
                return []
            events: list[Event] = []
            for line in self.events_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                event = event_from_dict(json.loads(line))
                if event.run_id == run_id:
                    events.append(event)
            return events

    def save(self, record: CheckpointRecord | PrecedentRecord) -> CheckpointRecord | PrecedentRecord:
        with self._lock:
            if isinstance(record, CheckpointRecord):
                checkpoints = self._read_json(self.checkpoints_path, {})
                checkpoints.setdefault(record.run_id, []).append(to_jsonable(record))
                self._write_json(self.checkpoints_path, checkpoints)
                return record
            with self.precedents_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(to_jsonable(record), sort_keys=True) + "\n")
        return record

    def get_latest(self, run_id: str) -> CheckpointRecord | None:
        with self._lock:
            records = self._read_json(self.checkpoints_path, {}).get(run_id, [])
        if not records:
            return None
        data = records[-1]
        return CheckpointRecord(
            checkpoint_id=data["checkpoint_id"],
            run_id=data["run_id"],
            stage=data["stage"],
            state=data.get("state") or {},
            created_at=data["created_at"],
        )

    def list_by_rule(self, rule_id: str | None = None) -> list[PrecedentRecord]:
        with self._lock:
            if not self.precedents_path.exists():
                return []
            records = []
            for line in self.precedents_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                data = json.loads(line)
                if rule_id is None or data.get("rule_id") == rule_id:
                    records.append(
                        PrecedentRecord(
                            precedent_id=data["precedent_id"],
                            run_id=data["run_id"],
                            verdict_id=data["verdict_id"],
                            rule_id=data["rule_id"],
                            ruling=data["ruling"],
                            created_at=data["created_at"],
                        )
                    )
            return records

    def _read_runs(self) -> dict[str, Run]:
        data = self._read_json(self.runs_path, {})
        return {run_id: run_from_dict(run_data) for run_id, run_data in data.items()}

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
