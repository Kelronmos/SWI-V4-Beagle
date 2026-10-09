"""Beagle pipeline — DISCOVER → … → READINESS. Default stops before rebuild."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from swi_beagle.audit import discover_local_sources, load_sources
from swi_beagle.binding import evaluate_binding
from swi_beagle.device import detect_device
from swi_beagle.evidence import export_bundle
from swi_beagle.journal import Journal
from swi_beagle.readiness import assess_readiness
from swi_beagle.structure import structure_audit


def run_audit_pipeline(
    roots: list[Path],
    root: Path,
    *,
    export: bool = True,
    allow_rebuild: bool = False,
) -> dict[str, Any]:
    j = Journal()
    sources_path = root / "config" / "sources.json"
    sources = load_sources(sources_path)

    j.log("PIPELINE", "START", "OBSERVED", "Beagle audit pipeline")
    audit = discover_local_sources(roots, sources_path, journal=j)
    repos = audit.get("repositories") or []

    structures = []
    for repo in repos:
        if not repo.get("exists"):
            continue
        expected = []
        matched = (repo.get("origin") or {}).get("matched")
        for s in sources.get("sources", []):
            if s["repository"] == matched:
                expected = s.get("expected_artifacts") or []
                break
        st = structure_audit(Path(repo["path"]), expected)
        structures.append(st)
        j.log("STRUCTURE", matched or Path(repo["path"]).name, st["status"], f"missing={st.get('missing')}")

    structure = structures[0] if len(structures) == 1 else {
        "stage": "STRUCTURE",
        "status": "OBSERVED" if structures else "MISSING",
        "repositories": structures,
    }

    deps_files = []
    for repo in repos:
        p = Path(repo.get("path") or "")
        for name in ("requirements.txt", "requirements-dev.txt", "pyproject.toml", "package.json"):
            if (p / name).exists():
                deps_files.append(str(p / name))
    dependencies = {
        "stage": "DEPENDENCIES",
        "status": "OBSERVED" if deps_files else "MISSING",
        "files": deps_files,
        "note": "File presence only — not installed/resolved",
    }
    j.log("DEPENDENCIES", "SCAN", dependencies["status"], f"files={len(deps_files)}")

    device = detect_device()
    j.log("DEVICE", "DETECT", device["status"], device.get("platform_class", ""))

    binding = evaluate_binding(device)
    j.log("BINDING", "EVAL", binding["binding_state"], binding.get("note", ""))

    build = {
        "stage": "BUILD",
        "status": "NOT_STARTED" if not allow_rebuild else "NOT_IMPLEMENTED",
        "note": "Isolated rebuild requires explicit allow_rebuild; default CHECK ONLY",
    }
    j.log("BUILD", "GATE", build["status"], build["note"])

    tests = {
        "stage": "TEST",
        "status": "NOT_RUN",
        "note": "Use explicit test phase; 0 tests ≠ PASS",
    }
    j.log("TEST", "GATE", "NOT_RUN", tests["note"])

    diagnosis = {
        "stage": "DIAGNOSIS",
        "status": "OBSERVED",
        "items": [],
    }
    for st in structures:
        for m in st.get("missing") or []:
            diagnosis["items"].append(
                {
                    "observation": f"Missing expected component: {m}",
                    "hypothesis": "Source tree incomplete or expected_artifacts over-specified",
                    "confidence": "MEDIUM",
                    "classification": "STRUCTURE_ERROR",
                    "recommended_next_step": "Verify against source commit; do not invent files",
                }
            )
    j.log("DIAGNOSIS", "RUN", "OBSERVED", f"items={len(diagnosis['items'])}")

    pipeline: dict[str, Any] = {
        "execution_id": j.execution_id,
        "role": "SWI V4 Beagle",
        "audit": audit,
        "repositories": repos,
        "structure": structure,
        "dependencies": dependencies,
        "device": device,
        "binding": binding,
        "build": build,
        "tests": tests,
        "diagnosis": diagnosis,
        "events": [e.__dict__ for e in j.events],
        "authorization": False,
        "proven": False,
        "sealed": False,
    }

    evidence_meta: dict[str, Any] = {}
    if export:
        export_dir = root / "exports" / f"RUN-{j.execution_id}"
        pipeline["evidence"] = {"artifacts": ["pending"]}
        readiness = assess_readiness(pipeline)
        pipeline["readiness"] = readiness
        j.log(
            "READINESS",
            "ASSESS",
            "PASS" if readiness.get("PIPELINE_READY") else "NOT_READY",
            f"PIPELINE_READY={readiness.get('PIPELINE_READY')}",
        )
        evidence_meta = export_bundle(export_dir, pipeline)
        pipeline["evidence"] = evidence_meta
        j.save(export_dir / "execution.json")
        (export_dir / "readiness.json").write_text(
            json.dumps(readiness, indent=2), encoding="utf-8"
        )
        j.log("REPORT", "EXPORT", "OBSERVED", str(export_dir))
    else:
        pipeline["readiness"] = assess_readiness(pipeline)

    j.log("PIPELINE", "END", "OBSERVED", "TRUE STATE > GREEN STATUS")
    pipeline["events"] = [e.__dict__ for e in j.events]
    return pipeline


def print_result(pipeline: dict[str, Any]) -> None:
    r = pipeline.get("readiness") or {}
    dims = r.get("dimensions") or {}
    print()
    print("=" * 60)
    print("SWI V4 BEAGLE RESULT")
    print("=" * 60)
    print(f"Execution ID:     {pipeline.get('execution_id')}")
    print(f"Repositories:     {len(pipeline.get('repositories') or [])}")
    print(f"Device:           {(pipeline.get('device') or {}).get('platform_class')}")
    print(f"Binding:          {(pipeline.get('binding') or {}).get('binding_state')}")
    print(f"Build:            {(pipeline.get('build') or {}).get('status')}")
    print(f"Tests:            {(pipeline.get('tests') or {}).get('status')}")
    print()
    for k, v in dims.items():
        print(f"  {k:20} {v}")
    print()
    print(f"PIPELINE_READY:   {r.get('PIPELINE_READY')}")
    print(f"READY_FOR_REVIEW: {r.get('READY_FOR_REVIEW')}")
    print()
    print("PROVEN = NO")
    print("SEALED = NO")
    print("AUTHORIZED = NO")
    print("PRODUCTION_AUTHORIZED = NO")
    print()
    print("TRUE STATE > GREEN STATUS")
    print("=" * 60)
