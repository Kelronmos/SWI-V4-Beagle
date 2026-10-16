"""Independent readiness dimensions — never BUILD SUCCESS → AUTHORIZED."""
from __future__ import annotations

from typing import Any, Optional


def _source_trust_state(repositories: Any) -> Optional[bool]:
    """
    Evaluate source trust for readiness.

    Returns:
      True  — nonempty list and every entry is explicitly allowed/approved
      False — empty list, or any explicitly untrusted/disallowed entry
      None  — nonempty but trust metadata missing/unknown (UNKNOWN ≠ trusted)

    SOURCE_PRESENT ≠ SOURCE_TRUSTED ≠ SOURCE_VALIDATED ≠ AUTHORIZED
    """
    if not repositories:
        return False
    if not isinstance(repositories, list):
        return False

    saw_unknown = False
    for repo in repositories:
        if not isinstance(repo, dict):
            return False
        origin = repo.get("origin")
        if origin is None:
            saw_unknown = True
            continue
        if not isinstance(origin, dict):
            return False
        allowed = origin.get("allowed")
        status = (origin.get("status") or "").upper()
        if allowed is False or status in (
            "UNTRUSTED_SOURCE",
            "UNTRUSTED",
            "DENIED",
            "REJECTED",
        ):
            return False
        if allowed is True or status in ("APPROVED_SOURCE", "TRUSTED", "ALLOWED"):
            continue
        # allowed missing/None and status not approved → unknown
        saw_unknown = True
    if saw_unknown:
        return None
    return True


def assess_readiness(pipeline: dict[str, Any]) -> dict[str, Any]:
    def dim(key: str, ok: bool | None) -> str:
        if ok is True:
            return "PASS"
        if ok is False:
            return "FAIL"
        return "UNKNOWN"

    repos = pipeline.get("repositories")
    source_trust = _source_trust_state(repos)
    # SOURCE_READY requires explicit trust, not mere presence
    source_ok = source_trust  # True/False/None

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
        "SOURCE_PRESENT": dim("PRESENT", bool(repos) if isinstance(repos, list) else False),
        "SOURCE_READY": dim("SOURCE", source_ok),
        "STRUCTURE_READY": dim("STRUCTURE", structure_ok if structure else None),
        "DEPENDENCY_READY": dim("DEP", deps_ok if deps else None),
        "BUILD_READY": dim("BUILD", build_ok if build else None),
        "TEST_READY": dim("TEST", test_ok if tests else None),
        "DEVICE_READY": dim("DEVICE", device_ok if device else None),
        "BINDING_READY": dim("BIND", binding_ready if binding else None),
        "EVIDENCE_READY": dim("EVIDENCE", evidence_ok if evidence else None),
        "REPLAY_READY": "NOT_RUN",
        "AUTHORIZATION_READY": "FAIL",  # never inferred from observation
    }

    # PIPELINE_READY requires trusted source + device — not presence alone
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
        "note": (
            "PIPELINE_READY ≠ AUTHORIZATION; "
            "SOURCE_PRESENT ≠ SOURCE_TRUSTED; "
            "BUILD PASS ≠ AUTHORIZATION; "
            "UNKNOWN trust ≠ trusted"
        ),
    }
