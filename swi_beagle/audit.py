"""Source discovery and audit — read-only."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

from swi_beagle.journal import Journal


def load_sources(config: Path) -> dict[str, Any]:
    return json.loads(config.read_text(encoding="utf-8"))


def normalize_origin(url: str) -> str:
    u = url.strip().rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    m = re.match(r"git@github\.com:(.+)", u)
    if m:
        return f"https://github.com/{m.group(1)}"
    return u


def classify_origin(origin: Optional[str], sources: dict[str, Any]) -> dict[str, Any]:
    if not origin:
        return {"status": "UNKNOWN", "allowed": False, "matched": None}
    norm = normalize_origin(origin)
    for s in sources.get("sources", []):
        if normalize_origin(s["url"]) == norm:
            return {
                "status": "APPROVED_SOURCE",
                "allowed": True,
                "matched": s["repository"],
                "trust_class": s.get("trust_class"),
                "purpose": s.get("purpose"),
                "note": "APPROVED_SOURCE ≠ PROVEN ≠ AUTHORIZED",
            }
    return {
        "status": "UNTRUSTED_SOURCE",
        "allowed": False,
        "matched": None,
        "note": "Must not automatically enter rebuild",
    }


def _git(path: Path, *args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(
            ["git", *args],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
        return p.returncode, (p.stdout or "").strip()
    except Exception as e:
        return 1, str(e)


def identify_repo(path: Path, sources: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "status": "MISSING", "exists": False}
    if not (path / ".git").exists():
        return {"path": str(path), "status": "UNKNOWN", "exists": True, "is_git": False}

    rc_h, head = _git(path, "rev-parse", "HEAD")
    rc_b, branch = _git(path, "branch", "--show-current")
    rc_o, origin = _git(path, "remote", "get-url", "origin")
    rc_s, status = _git(path, "status", "--short")
    origin_cls = classify_origin(origin if rc_o == 0 else None, sources)

    return {
        "path": str(path.resolve()),
        "exists": True,
        "is_git": True,
        "head": head if rc_h == 0 else None,
        "branch": branch if rc_b == 0 else None,
        "worktree_clean": (status == "") if rc_s == 0 else None,
        "origin": origin_cls,
        "raw_origin": origin if rc_o == 0 else None,
        "status": "OBSERVED" if rc_h == 0 else "UNKNOWN",
        "classification": "ORIGINAL",
        "authorization": False,
    }


def discover_local_sources(
    roots: list[Path],
    sources_config: Path,
    journal: Optional[Journal] = None,
) -> dict[str, Any]:
    j = journal or Journal()
    sources = load_sources(sources_config)
    j.log("DISCOVER", "START", "OBSERVED", f"roots={[str(r) for r in roots]}")

    found = []
    for root in roots:
        if not root.exists():
            j.log("DISCOVER", "ROOT", "MISSING", str(root))
            continue
        candidates = []
        if (root / ".git").exists():
            candidates.append(root)
        else:
            for child in sorted(root.iterdir()):
                if child.is_dir() and (child / ".git").exists():
                    candidates.append(child)
        for c in candidates:
            ident = identify_repo(c, sources)
            found.append(ident)
            j.log(
                "IDENTIFY",
                ident.get("origin", {}).get("matched") or c.name,
                ident.get("origin", {}).get("status", ident.get("status", "UNKNOWN")),
                f"HEAD={ident.get('head')}",
            )

    j.log("AUDIT", "COMPLETE", "OBSERVED", f"repos={len(found)}")
    return {
        "execution_id": j.execution_id,
        "repositories": found,
        "source_manifest_count": len(sources.get("sources", [])),
        "events": [e.__dict__ for e in j.events],
        "authorization": False,
        "proven": False,
        "note": "DISCOVER/IDENTIFY only — no rebuild, no authorization",
    }
