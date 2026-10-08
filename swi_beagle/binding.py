"""Device binding diagnostics — never elevates to human authority."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def evaluate_binding(device: dict[str, Any]) -> dict[str, Any]:
    """Bind observation record. Does not authorize."""
    detected = device.get("status") == "DETECTED"
    state = "DETECTED" if detected else "NOT_DETECTED"
    return {
        "stage": "BINDING",
        "status": state,
        "device_class": device.get("platform_class"),
        "os": device.get("os"),
        "architecture": device.get("architecture"),
        "runtime": device.get("python"),
        "binding_state": "OBSERVED" if detected else "NOT_DETECTED",
        "validated": False,
        "bound": False,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authorization": False,
        "human_authority": "NOT_ESTABLISHED",
        "note": "DEVICE_ID ≠ HUMAN_AUTHORITY; BOUND ≠ AUTHORIZED",
        "failure_reason": None if detected else "DEVICE_NOT_DETECTED",
    }
