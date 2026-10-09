from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass
class Event:
    execution_id: str
    event_id: str
    timestamp: str
    sequence: int
    stage: str
    operation: str
    status: str
    message: str = ""
    command: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: Optional[float] = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def line(self) -> str:
        t = self.timestamp[11:19] if len(self.timestamp) > 19 else self.timestamp
        return f"[{t}] {self.stage}/{self.operation}: {self.status}" + (
            f" — {self.message}" if self.message else ""
        )


class Journal:
    def __init__(self) -> None:
        self.execution_id = (
            datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
        )
        self.events: list[Event] = []
        self._seq = 0
        self._t0 = time.perf_counter()
        self.started_at = _utc()

    def log(self, stage: str, operation: str, status: str, message: str = "", **kw: Any) -> Event:
        self._seq += 1
        ev = Event(
            execution_id=self.execution_id,
            event_id=f"E{self._seq:04d}",
            timestamp=_utc(),
            sequence=self._seq,
            stage=stage,
            operation=operation,
            status=status,
            message=message,
            command=kw.get("command"),
            exit_code=kw.get("exit_code"),
            duration_ms=kw.get("duration_ms"),
            evidence={k: v for k, v in kw.items() if k not in ("command", "exit_code", "duration_ms")},
        )
        self.events.append(ev)
        print(ev.line(), flush=True)
        return ev

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "execution_id": self.execution_id,
            "started_at": self.started_at,
            "ended_at": _utc(),
            "duration_ms": (time.perf_counter() - self._t0) * 1000,
            "events": [asdict(e) for e in self.events],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
