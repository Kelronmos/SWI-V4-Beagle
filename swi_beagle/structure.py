"""Structural audit of a local checkout — PRESENT/MISSING/UNKNOWN."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Optional


def _sha256_file(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def structure_audit(path: Path, expected: Optional[list[str]] = None) -> dict[str, Any]:
    expected = expected or []
    if not path.exists():
        return {
            "stage": "STRUCTURE",
            "status": "MISSING",
            "path": str(path),
            "components": {},
            "failure_reason": "PATH_MISSING",
        }

    components: dict[str, Any] = {}
    for name in expected:
        p = path / name
        if p.exists():
            components[name] = {
                "status": "PRESENT",
                "type": "dir" if p.is_dir() else "file",
                "sha256": _sha256_file(p) if p.is_file() else None,
            }
        else:
            components[name] = {"status": "MISSING"}

    top = []
    for child in sorted(path.iterdir()):
        if child.name.startswith(".git"):
            continue
        top.append({"name": child.name, "type": "dir" if child.is_dir() else "file"})

    modules = []
    for pattern in ("swi_v1", "swi_v2", "swi_v3", "swi_beagle"):
        mp = path / pattern
        if mp.is_dir():
            modules.append(
                {
                    "module_id": pattern.upper().replace("_", "-"),
                    "name": pattern,
                    "path": str(mp),
                    "status": "PRESENT",
                    "proven": False,
                }
            )

    missing = [k for k, v in components.items() if v.get("status") == "MISSING"]
    status = "PASS" if expected and not missing else ("OBSERVED" if top else "UNKNOWN")
    if expected and missing:
        status = "INCOMPLETE"

    return {
        "stage": "STRUCTURE",
        "status": status,
        "path": str(path.resolve()),
        "expected": expected,
        "components": components,
        "missing": missing,
        "top_level": top[:80],
        "modules": modules,
        "note": "MISSING ≠ NOT REQUIRED unless requirement explicitly says so",
    }
