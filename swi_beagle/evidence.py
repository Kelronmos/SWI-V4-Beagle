from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, obj: Any, classification: str = "EVIDENCE") -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=2, default=str).encode("utf-8")
    path.write_bytes(data)
    return {
        "artifact": path.name,
        "path": str(path),
        "sha256": sha256_bytes(data),
        "size": len(data),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": classification,
    }


def export_bundle(export_dir: Path, pipeline: dict[str, Any]) -> dict[str, Any]:
    export_dir.mkdir(parents=True, exist_ok=True)
    eid = pipeline.get("execution_id", "UNKNOWN")
    artifacts = []

    mapping = {
        "audit.json": "audit",
        "structure.json": "structure",
        "device.json": "device",
        "binding.json": "binding",
        "dependencies.json": "dependencies",
        "build.json": "build",
        "tests.json": "tests",
        "diagnosis.json": "diagnosis",
        "readiness.json": "readiness",
        "evidence.json": None,
    }
    for fname, key in mapping.items():
        if key is None:
            continue
        payload = pipeline.get(key)
        if payload is None:
            payload = {"status": "NOT_RUN", "execution_id": eid}
        meta = write_json(export_dir / fname, payload)
        meta["execution_id"] = eid
        artifacts.append(meta)

    dossier = _dossier(pipeline)
    (export_dir / "dossier.md").write_text(dossier, encoding="utf-8")
    artifacts.append(
        {
            "artifact": "dossier.md",
            "path": str(export_dir / "dossier.md"),
            "sha256": sha256_bytes(dossier.encode()),
            "size": len(dossier.encode()),
            "classification": "REPORT",
            "execution_id": eid,
        }
    )

    manifest = {
        "execution_id": eid,
        "algorithm": "SHA-256",
        "artifacts": artifacts,
        "PROVEN": False,
        "SEALED": False,
        "AUTHORIZED": False,
    }
    m = write_json(export_dir / "manifest.json", manifest, "EVIDENCE")
    artifacts.append(m)

    write_json(export_dir / "evidence.json", {"execution_id": eid, "artifacts": artifacts})

    return {"export_dir": str(export_dir), "artifacts": artifacts, "authorized": False}


def _dossier(p: dict[str, Any]) -> str:
    r = p.get("readiness") or {}
    dims = r.get("dimensions") or {}
    lines = [
        "# SWI V4 Beagle Dossier",
        "",
        f"**Execution ID:** `{p.get('execution_id')}`",
        "",
        "## What did Beagle find?",
        "",
        f"Repositories: {len(p.get('repositories') or [])}",
        "",
        "## Source / commit",
        "",
    ]
    for repo in p.get("repositories") or []:
        lines.append(
            f"- `{repo.get('path')}` HEAD=`{repo.get('head')}` "
            f"origin={((repo.get('origin') or {}).get('status'))}"
        )
    lines.extend(
        [
            "",
            "## Structure / missing",
            "",
            f"Status: {(p.get('structure') or {}).get('status', 'NOT_RUN')}",
            f"Missing: {(p.get('structure') or {}).get('missing', [])}",
            "",
            "## Device / binding",
            "",
            f"Device: {(p.get('device') or {}).get('status')} "
            f"{(p.get('device') or {}).get('platform_class')}",
            f"Binding: {(p.get('binding') or {}).get('binding_state')}",
            "",
            "## Build / test",
            "",
            f"Build: {(p.get('build') or {}).get('status', 'NOT_RUN')}",
            f"Tests: {(p.get('tests') or {}).get('status', 'NOT_RUN')}",
            "",
            "## Readiness dimensions",
            "",
        ]
    )
    for k, v in dims.items():
        lines.append(f"- {k}: {v}")
    lines.extend(
        [
            "",
            f"**PIPELINE_READY:** {r.get('PIPELINE_READY')}",
            "",
            "## Authorization (separate)",
            "",
            "```",
            "PROVEN = NO",
            "SEALED = NO",
            "AUTHORIZED = NO",
            "PRODUCTION_AUTHORIZED = NO",
            "```",
            "",
            "Beagle does not say ready-because-build-worked.",
            "It reports findings, failures, evidence, and unknowns.",
            "",
        ]
    )
    return "\n".join(lines)
