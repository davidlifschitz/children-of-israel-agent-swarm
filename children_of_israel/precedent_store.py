"""precedent_store.py
Persistent store for Dan's ruling precedents (OL-002).
Backed by data/precedents.jsonl — append-only, never overwrite.
"""

import json
from datetime import datetime
from pathlib import Path


class PrecedentStore:
    def __init__(self) -> None:
        self.store_path = Path(__file__).parent.parent / "data" / "precedents.jsonl"
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Create the data/ directory and file if they do not exist."""
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.touch(exist_ok=True)

    def write(self, precedent: dict) -> None:
        """Append a precedent record as a JSON line. Never overwrites existing data."""
        if "written_at" not in precedent:
            precedent["written_at"] = datetime.utcnow().isoformat()
        with open(self.store_path, "a") as fh:
            fh.write(json.dumps(precedent) + "\n")

    def lookup(self, conflict_type: str) -> list[dict]:
        """Return all records matching the given conflict_type."""
        if not self.store_path.exists():
            return []
        results: list[dict] = []
        with open(self.store_path, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if record.get("conflict_type") == conflict_type:
                        results.append(record)
                except json.JSONDecodeError:
                    continue
        return results

    def get_all(self) -> list[dict]:
        """Return every record in the store."""
        if not self.store_path.exists():
            return []
        records: list[dict] = []
        with open(self.store_path, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records


# Module-level singleton
precedent_store = PrecedentStore()
