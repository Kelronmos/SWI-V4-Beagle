"""Independent readiness dimensions — never BUILD SUCCESS → AUTHORIZED."""
from __future__ import annotations

from typing import Any


def assess_readiness(pipeline: dict[str, Any]) -> dict[str, Any]:
    def dim(key: str, ok: bool | None) -> str:
        if ok is True:
            return "PASS"
        if ok is False:
            return "FAIL"
        return "UNKNOWN"

    source_ok = bool(pipeline.get("repositories"))
    structure = pipeline.get("structure") or {}
    structure_ok = structure.get("status") in ("PASS", "OBSERVED", "INCOMPLETE")
    if structure.get("status") == "INCOMPLETE":
        structure_ok = False
    if structure.get("status") == "MISSING":
        structure_ok = False

    deps = pipeline.get("dependencies") or {}
    deps_ok = deps.get("status") in ("OBSERVED", "PASS")

    device = pipeline.get("device") or {}
    device_ok = device.get("status") == "DETECTED"

    binding = pipeline.get("binding") or {}
    binding_ready = binding.get("binding_state") in ("OBSERVED", "BOUND", "VALIDATED")

    build = pipeline.get("build") or {}
    build_ok = build.get("status") == "PASSED"

    tests = pipeline.get("tests") or {}
    test_ok = tests.get("status") == "PASSED"

    evidence = pipeline.get("evidence") or {}
    evidence_ok = bool(evidence.get("artifacts"))

    dims = {
        "SOURCE_READY": dim("SOURCE", source_ok),
        "STRUCTURE_READY": dim("STRUCTURE", structure_ok if structure else None),
        "DEPENDENCY_READY": dim("DEP", deps_ok if deps else None),
        "BUILD_READY": dim("BUILD", build_ok if build else None),
        "TEST_READY": dim("TEST", test_ok if tests else None),
        "DEVICE_READY": dim("DEVICE", device_ok if device else None),
        "BINDING_READY": dim("BIND", binding_ready if binding else None),
        "EVIDENCE_READY": dim("EVIDENCE", evidence_ok if evidence else None),
        "REPLAY_READY": "NOT_RUN",
    }

    required = ["SOURCE_READY", "DEVICE_READY"]
    pipeline_ready = all(dims[r] == "PASS" for r in required)

    return {
        "stage": "READINESS",
        "dimensions": dims,
        "PIPELINE_READY": pipeline_ready,
        "PROVEN": False,
        "SEALED": False,
        "AUTHORIZED": False,
        "PRODUCTION_AUTHORIZED": False,
        "READY_FOR_REVIEW": pipeline_ready and not pipeline.get("failures"),
        "note": "PIPELINE_READY ≠ AUTHORIZATION; BUILD PASS ≠ AUTHORIZATION",
    }
