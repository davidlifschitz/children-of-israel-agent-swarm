from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from coi_contracts import to_jsonable
from coi_orchestrator import build_local_orchestrator


def create_handler(repo_root: str | Path, storage_root: str | Path):
    orchestrator = build_local_orchestrator(repo_root, storage_root=storage_root)

    class SwarmHandler(BaseHTTPRequestHandler):
        server_version = "ChildrenOfIsraelSwarm/0.1"

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler method name.
            path = urlparse(self.path).path
            if path == "/health":
                self._json(
                    {
                        "status": "ok",
                        "runtime": "mock",
                        "storage": "file",
                        "ready": True,
                    }
                )
                return
            parts = [part for part in path.split("/") if part]
            if len(parts) == 2 and parts[0] == "runs":
                run = orchestrator.get_run(parts[1])
                if run is None:
                    self._json({"error": "run_not_found"}, HTTPStatus.NOT_FOUND)
                    return
                self._json(to_jsonable(run))
                return
            if len(parts) == 3 and parts[0] == "runs" and parts[2] == "events":
                if orchestrator.get_run(parts[1]) is None:
                    self._json({"error": "run_not_found"}, HTTPStatus.NOT_FOUND)
                    return
                self._json({"events": [to_jsonable(event) for event in orchestrator.get_events(parts[1])]})
                return
            if len(parts) == 3 and parts[0] == "runs" and parts[2] == "summary":
                summary = orchestrator.get_summary(parts[1])
                if summary is None:
                    self._json({"error": "run_not_found"}, HTTPStatus.NOT_FOUND)
                    return
                self._json(summary)
                return
            self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path not in {"/runs", "/bootstrap"}:
                self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
                return
            task, error = self._read_json()
            if error is not None:
                self._json({"error": "bad_request", "message": error}, HTTPStatus.BAD_REQUEST)
                return
            if path == "/bootstrap":
                task.setdefault("task_type", "repo.bootstrap")
            summary = orchestrator.execute_task(task)
            self._json(summary, HTTPStatus.CREATED)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def _read_json(self) -> tuple[dict[str, Any], str | None]:
            try:
                length = int(self.headers.get("Content-Length") or "0")
            except ValueError:
                return {}, "Content-Length must be an integer."
            if length == 0:
                return {}, None
            try:
                raw = self.rfile.read(length).decode("utf-8")
            except UnicodeDecodeError:
                return {}, "Request body must be UTF-8 encoded."
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return {}, "Request body must be valid JSON."
            if not isinstance(data, dict):
                return {}, "Request body must be a JSON object."
            return data, None

        def _json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return SwarmHandler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local Children of Israel swarm API.")
    parser.add_argument("--repo-root", default=".", help="Repository root containing law/ and config/.")
    parser.add_argument("--storage-root", default=".coi-api", help="Directory for durable local API storage.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    handler = create_handler(args.repo_root, args.storage_root)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving Children of Israel swarm API on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
