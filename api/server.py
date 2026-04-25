#!/usr/bin/env python3
"""Minimal OpenGRC API server for standards, programs, controls, and implementations."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse


API_TOKEN_ENV = "OPENGRC_API_TOKEN"
DEFAULT_API_TOKEN = "3|vln7XSv3QEYNJXxq7jfsLHGUICreFG6RtzF5E6Og86fe40dd"


@dataclass
class Store:
    lock: threading.Lock = field(default_factory=threading.Lock)
    counters: dict[str, int] = field(
        default_factory=lambda: {
            "standards": 0,
            "programs": 0,
            "controls": 0,
            "implementations": 0,
        }
    )
    standards: dict[int, dict[str, Any]] = field(default_factory=dict)
    programs: dict[int, dict[str, Any]] = field(default_factory=dict)
    controls: dict[int, dict[str, Any]] = field(default_factory=dict)
    implementations: dict[int, dict[str, Any]] = field(default_factory=dict)

    def next_id(self, table: str) -> int:
        self.counters[table] += 1
        return self.counters[table]


STORE = Store()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class OpenGRCHandler(BaseHTTPRequestHandler):
    server_version = "OpenGRC/0.1"

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            json_response(self, HTTPStatus.OK, {"status": "ok", "time": now_iso()})
            return

        if path == "/api/standards":
            json_response(self, HTTPStatus.OK, {"data": list(STORE.standards.values())})
            return

        if path == "/api/programs":
            json_response(self, HTTPStatus.OK, {"data": list(STORE.programs.values())})
            return

        if path == "/api/controls":
            json_response(self, HTTPStatus.OK, {"data": list(STORE.controls.values())})
            return

        if path == "/api/implementations":
            json_response(self, HTTPStatus.OK, {"data": list(STORE.implementations.values())})
            return

        json_response(self, HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        auth_error = self._check_bearer_auth()
        if auth_error:
            json_response(self, HTTPStatus.UNAUTHORIZED, auth_error)
            return

        payload, parse_error = self._read_json_body()
        if parse_error:
            json_response(self, HTTPStatus.BAD_REQUEST, parse_error)
            return

        if path == "/api/standards":
            self._create_standard(payload)
            return

        if path == "/api/programs":
            self._create_program(payload)
            return

        if path == "/api/controls":
            self._create_control(payload)
            return

        if path == "/api/implementations":
            self._create_implementation(payload)
            return

        json_response(self, HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def _check_bearer_auth(self) -> dict[str, str] | None:
        expected = os.environ.get(API_TOKEN_ENV, DEFAULT_API_TOKEN)
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return {"error": "Missing or invalid Authorization header"}
        token = auth.removeprefix("Bearer ").strip()
        if token != expected:
            return {"error": "Invalid token"}
        return None

    def _read_json_body(self) -> tuple[dict[str, Any], dict[str, str] | None]:
        content_length = self.headers.get("Content-Length")
        if not content_length:
            return {}, {"error": "Missing Content-Length"}

        try:
            length = int(content_length)
            raw = self.rfile.read(length)
            data = json.loads(raw)
        except ValueError:
            return {}, {"error": "Request body must be valid JSON"}

        if not isinstance(data, dict):
            return {}, {"error": "JSON body must be an object"}

        return data, None

    def _validate_required(self, payload: dict[str, Any], fields: list[str]) -> list[str]:
        missing: list[str] = []
        for key in fields:
            value = payload.get(key)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(key)
        return missing

    def _create_standard(self, payload: dict[str, Any]) -> None:
        missing = self._validate_required(payload, ["code", "title"])
        if missing:
            json_response(self, HTTPStatus.UNPROCESSABLE_ENTITY, {"error": f"Missing required field(s): {', '.join(missing)}"})
            return

        with STORE.lock:
            entry_id = STORE.next_id("standards")
            entry = {
                "id": entry_id,
                "code": payload["code"],
                "title": payload["title"],
                "description": payload.get("description", ""),
                "created_at": now_iso(),
            }
            STORE.standards[entry_id] = entry

        json_response(self, HTTPStatus.CREATED, {"data": entry})

    def _create_program(self, payload: dict[str, Any]) -> None:
        missing = self._validate_required(payload, ["code", "title"])
        if missing:
            json_response(self, HTTPStatus.UNPROCESSABLE_ENTITY, {"error": f"Missing required field(s): {', '.join(missing)}"})
            return

        with STORE.lock:
            entry_id = STORE.next_id("programs")
            entry = {
                "id": entry_id,
                "code": payload["code"],
                "title": payload["title"],
                "description": payload.get("description", ""),
                "created_at": now_iso(),
            }
            STORE.programs[entry_id] = entry

        json_response(self, HTTPStatus.CREATED, {"data": entry})

    def _create_control(self, payload: dict[str, Any]) -> None:
        required = ["code", "identifier", "title", "description", "status"]
        missing = self._validate_required(payload, required)
        if missing:
            json_response(self, HTTPStatus.UNPROCESSABLE_ENTITY, {"error": f"Missing required field(s): {', '.join(missing)}"})
            return

        with STORE.lock:
            entry_id = STORE.next_id("controls")
            entry = {
                "id": entry_id,
                "code": payload["code"],
                "identifier": payload["identifier"],
                "standard_id": payload.get("standard_id"),
                "program_id": payload.get("program_id"),
                "enforcement": payload.get("enforcement"),
                "type": payload.get("type"),
                "category": payload.get("category"),
                "title": payload["title"],
                "description": payload["description"],
                "discussion": payload.get("discussion", ""),
                "test_plan": payload.get("test_plan", ""),
                "status": payload["status"],
                "created_at": now_iso(),
            }
            STORE.controls[entry_id] = entry

        json_response(self, HTTPStatus.CREATED, {"data": entry})

    def _create_implementation(self, payload: dict[str, Any]) -> None:
        required = ["code", "identifier", "title", "description", "status", "control_id"]
        missing = self._validate_required(payload, required)
        if missing:
            json_response(self, HTTPStatus.UNPROCESSABLE_ENTITY, {"error": f"Missing required field(s): {', '.join(missing)}"})
            return

        with STORE.lock:
            control_id = int(payload["control_id"])
            if control_id not in STORE.controls:
                json_response(self, HTTPStatus.UNPROCESSABLE_ENTITY, {"error": f"Unknown control_id: {control_id}"})
                return

            entry_id = STORE.next_id("implementations")
            entry = {
                "id": entry_id,
                "code": payload["code"],
                "identifier": payload["identifier"],
                "title": payload["title"],
                "description": payload["description"],
                "status": payload["status"],
                "control_id": control_id,
                "standard_id": payload.get("standard_id"),
                "program_id": payload.get("program_id"),
                "created_at": now_iso(),
            }
            STORE.implementations[entry_id] = entry

        json_response(self, HTTPStatus.CREATED, {"data": entry})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        # Keep output concise while still visible in foreground runs.
        print(f"[{self.log_date_time_string()}] {self.address_string()} {format % args}")


def run() -> None:
    host = os.environ.get("OPENGRC_API_HOST", "0.0.0.0")
    port = int(os.environ.get("OPENGRC_API_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), OpenGRCHandler)
    print(f"OpenGRC API listening on http://{host}:{port}")
    print(f"Using token from {API_TOKEN_ENV} (or built-in default if unset)")
    server.serve_forever()


if __name__ == "__main__":
    run()
