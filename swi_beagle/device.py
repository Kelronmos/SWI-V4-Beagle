"""Device diagnostics — observation only. DEVICE_PRESENT ≠ AUTHORIZED."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from typing import Any


def _run(cmd: list[str], timeout: float = 5.0) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return p.returncode, (p.stdout or "").strip()
    except Exception as e:
        return 1, str(e)


def detect_device() -> dict[str, Any]:
    u = platform.uname()
    disk = shutil.disk_usage(".")
    git_rc, git_v = _run(["git", "--version"])
    py_rc, py_v = _run([sys.executable, "--version"])

    prefix = os.environ.get("PREFIX", "")
    is_termux = "com.termux" in prefix or bool(os.environ.get("TERMUX_VERSION"))
    is_android = is_termux or "ANDROID_ROOT" in os.environ

    os_name = u.system
    if is_android:
        platform_class = "ANDROID"
    elif os_name == "Windows":
        platform_class = "WINDOWS"
    elif os_name == "Darwin":
        platform_class = "MACOS"
    elif os_name == "Linux":
        platform_class = "LINUX"
    else:
        platform_class = "UNKNOWN"

    return {
        "stage": "DEVICE",
        "status": "DETECTED",
        "platform_class": platform_class,
        "os": os_name,
        "os_version": u.release,
        "architecture": u.machine,
        "cpu": u.processor or "UNKNOWN",
        "python": sys.version.split()[0],
        "python_ok": py_rc == 0,
        "git": git_v if git_rc == 0 else None,
        "git_ok": git_rc == 0,
        "disk_free_bytes": disk.free,
        "disk_total_bytes": disk.total,
        "is_termux": is_termux,
        "is_android": is_android,
        "binding_state": "NOT_BOUND",
        "supported_claim": {
            "IMPLEMENTED": True,
            "TESTED": False,
            "SUPPORTED": False,
            "note": "Detection exists; platform SUPPORT requires evidence suite per target",
        },
        "authorization": False,
        "note": "DEVICE_PRESENT ≠ AUTHORIZED; DEVICE_MATCH ≠ EXECUTE",
    }
