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
        result = isolated_build(src, ROOT, force_fail=args.force_fail)
        print(json.dumps({
            "execution_id": result.get("execution_id"),
            "status": result.get("status"),
            "diagnosis": result.get("diagnosis"),
            "SOURCE_COMMIT": (result.get("source") or {}).get("SOURCE_COMMIT"),
            "WORKTREE_STATE": (result.get("source") or {}).get("WORKTREE_STATE"),
            "BUILD": (result.get("build") or {}).get("status"),
            "TESTS": (result.get("tests") or {}).get("status"),
            "REPLAY": (result.get("replay") or {}).get("status"),
            "SECURITY": (result.get("security") or {}).get("status"),
            "AUTHORIZED": result.get("authorized"),
            "PROVEN": result.get("proven"),
            "run_dir": result.get("run_dir"),
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
