"""python -m swi_beagle"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from swi_beagle.pipeline import print_result, run_audit_pipeline


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="SWI V4 Beagle — deployment/diagnostic control plane")
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("audit", help="Discover, structure, device, binding, readiness (default)")
    a.add_argument("--roots", nargs="*", default=[str(ROOT.parent)])
    a.add_argument("--no-export", action="store_true")

    b = sub.add_parser("build", help="Isolated build + test gate (Phase 5)")
    b.add_argument("--source", required=True, help="Path to allowlisted SWI source checkout")
    b.add_argument("--force-fail", action="store_true", help="Break-test: force BUILD=FAIL")

    sub.add_parser("status", help="Show ceiling")

    d = sub.add_parser("dashboard", help="Local dashboard (visualization only)")
    d.add_argument("--host", default="127.0.0.1")
    d.add_argument("--port", default="8777")

    args = p.parse_args(argv)
    if not args.cmd:
        args = p.parse_args(["audit"])

    if args.cmd == "status":
        print("SWI V4 Beagle")
        print("PROVEN=NO SEALED=NO AUTHORIZED=NO PRODUCTION_AUTHORIZED=NO")
        print("Role: deployment/diagnostic layer — not V1–V3 replacement")
        return 0

    if args.cmd == "dashboard":
        from swi_beagle.dashboard_server import serve

        serve(args.host, int(args.port), ROOT)
        return 0

    if args.cmd == "build":
        from swi_beagle.build_engine import isolated_build

        src = Path(args.source).resolve()
        print(f"BEAGLE BUILD GATE — source={src}")
        print("PROVEN=NO SEALED=NO AUTHORIZED=NO (ceiling fixed)")
        try:
            result = isolated_build(src, ROOT, force_fail=args.force_fail)
        except Exception as exc:
            print(json.dumps({
                "status": "FAIL",
                "diagnosis": f"ENGINE_EXCEPTION: {type(exc).__name__}",
                "AUTHORIZED": False,
                "PROVEN": False,
                "SEALED": False,
                "PRODUCTION_AUTHORIZED": False,
                "note": "CLI is diagnostic only; ceilings forced false",
            }, indent=2))
            print()
            print("PROVEN = NO")
            print("SEALED = NO")
            print("AUTHORIZED = NO")
            print("PRODUCTION_AUTHORIZED = NO")
            return 1

        def _stage_status(val):
            """Normalize stage field: dict with status, plain str, or missing."""
            if val is None:
                return None
            if isinstance(val, dict):
                return val.get("status")
            if isinstance(val, str):
                return val
            return None

        # Malformed engine payload must not crash or grant authority
        if not isinstance(result, dict):
            print(json.dumps({
                "status": "FAIL",
                "diagnosis": "ENGINE_RESULT_NOT_DICT",
                "AUTHORIZED": False,
                "PROVEN": False,
                "SEALED": False,
                "PRODUCTION_AUTHORIZED": False,
                "note": "CLI is diagnostic only; ceilings forced false",
            }, indent=2))
            print()
            print("PROVEN = NO")
            print("SEALED = NO")
            print("AUTHORIZED = NO")
            print("PRODUCTION_AUTHORIZED = NO")
            return 1

        source = result.get("source") or {}
        if not isinstance(source, dict):
            source = {}
        # Map engine identity keys; do not invent evidence
        source_commit = source.get("commit") or source.get("SOURCE_COMMIT")
        worktree_state = None
        if "dirty" in source:
            worktree_state = "DIRTY" if source.get("dirty") else "CLEAN"
        worktree_state = source.get("WORKTREE_STATE") or worktree_state

        # Authorization ceilings are NOT copied from engine output.
        # Engine fields named authorized/proven are observational claims only;
        # the CLI forces them false so forged results cannot create a trusted claim.
        print(json.dumps({
            "execution_id": result.get("execution_id"),  # may be absent; never fabricated
            "status": result.get("status"),
            "diagnosis": result.get("diagnosis") or result.get("failure_reason"),
            "SOURCE_COMMIT": source_commit,
            "WORKTREE_STATE": worktree_state,
            "BUILD": _stage_status(result.get("build")),
            "TESTS": _stage_status(result.get("tests")),
            "REPLAY": _stage_status(result.get("replay")),
            "SECURITY": _stage_status(result.get("security")),
            "AUTHORIZED": False,
            "PROVEN": False,
            "SEALED": False,
            "PRODUCTION_AUTHORIZED": False,
            "run_dir": result.get("run_dir"),
            "engine_authorized_claim": result.get("authorized"),
            "engine_proven_claim": result.get("proven"),
            "note": "Ceilings forced false; engine_*_claim is unverified observation only",
        }, indent=2))
        print()
        print("PROVEN = NO")
        print("SEALED = NO")
        print("AUTHORIZED = NO")
        print("PRODUCTION_AUTHORIZED = NO")
        return 0 if result.get("status") in ("PASS", "BLOCKED") else 1

    roots = [Path(r).resolve() for r in args.roots]
    pipeline = run_audit_pipeline(roots, ROOT, export=not args.no_export)
    print_result(pipeline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
