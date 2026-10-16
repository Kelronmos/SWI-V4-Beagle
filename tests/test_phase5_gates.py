"""Phase 5 break tests — refuse unsafe transitions. Keep fixtures small.

Test-contract note: 0 collected tests is NOT treated as PASS (ZERO_TESTS_NOT_PASS).
Fixtures use real temporary Git repositories so identity checks are valid.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swi_beagle.build_engine import isolated_build, scan_for_secrets, scan_path_for_secrets


def _git_init_commit(path: Path, origin_url: str) -> Path:
    """Create a real temporary Git repo with one commit and configured origin."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", origin_url],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert len(head) == 40
    return path


def _mini_v2(tmp: Path, origin: str | None = None) -> Path:
    pkg = tmp / "swi_v2"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("# mini\n")
    (tmp / "requirements.txt").write_text("# none\n")
    url = origin or "https://github.com/Kelronmos/SWI-V2-Modules-11-22.git"
    return _git_init_commit(tmp, url)


def test_unknown_source_blocks_build(tmp_path):
    r = isolated_build(tmp_path / "nope", ROOT, skip_source_check=True)
    assert r["status"] == "BLOCKED"
    assert r["tests"]["status"] == "NOT_RUN"
    assert r["authorized"] is False


def test_unapproved_origin_blocks_build(tmp_path):
    src = _mini_v2(tmp_path / "v2", origin="https://github.com/other/untrusted.git")
    r = isolated_build(src, ROOT)
    assert r["status"] == "BLOCKED"
    assert r["failure_reason"] == "UNTRUSTED_OR_UNKNOWN_ORIGIN"
    assert r["authorized"] is False


def test_forced_build_fail_skips_tests(tmp_path):
    src = _mini_v2(tmp_path / "v2")
    r = isolated_build(src, ROOT, force_fail=True)
    assert r["status"] == "FAIL"
    assert r["tests"]["status"] == "NOT_RUN"
    assert r["authorized"] is False


def test_authorization_never_true_on_fail_path(tmp_path):
    src = _mini_v2(tmp_path / "v2")
    r = isolated_build(src, ROOT, force_fail=True)
    assert r.get("authorized") is False
    assert r.get("proven") is False
    assert r.get("sealed") is False
    assert r.get("production_authorized") is False
    ready = r.get("readiness") or {}
    assert ready.get("AUTHORIZED") is False
    assert ready.get("PRODUCTION_READY") is False


def test_secret_scan_detects_fake_private_key(tmp_path):
    f = tmp_path / "leak.txt"
    f.write_text("-----BEGIN RSA PRIVATE KEY-----\nFAKE\n-----END RSA PRIVATE KEY-----\n")
    assert scan_for_secrets(f.read_text())
    assert scan_path_for_secrets(tmp_path)["status"] == "FAIL"


def test_secret_scan_clean_on_empty(tmp_path):
    (tmp_path / "ok.txt").write_text("hello public identity material\n")
    assert scan_path_for_secrets(tmp_path)["status"] == "PASS"


def test_mini_build_zero_tests_is_not_pass(tmp_path):
    """Intentional contract correction: 0 tests ≠ PASS."""
    src = _mini_v2(tmp_path / "v2")
    r = isolated_build(src, ROOT)
    assert r["tests"]["status"] == "NOT_RUN"
    assert r["tests"].get("collected", 0) == 0
    assert r["status"] in ("BLOCKED", "FAIL")
    assert r["authorized"] is False
    assert r.get("proven") is False
    assert r["failure_reason"] in ("ZERO_TESTS_NOT_PASS", "ZERO_TESTS")


def test_dirty_worktree_blocks(tmp_path):
    src = _mini_v2(tmp_path / "v2")
    (src / "extra_dirty.txt").write_text("uncommitted\n")
    r = isolated_build(src, ROOT)
    assert r["status"] == "BLOCKED"
    assert r["failure_reason"] == "DIRTY_WORKTREE"
    assert r["authorized"] is False


def test_authorization_false_on_all_paths(tmp_path):
    cases = [
        isolated_build(tmp_path / "missing", ROOT),
        isolated_build(_mini_v2(tmp_path / "a"), ROOT, force_fail=True),
        isolated_build(_mini_v2(tmp_path / "b"), ROOT),
    ]
    for r in cases:
        assert r["authorized"] is False
        assert r["proven"] is False
        assert r["sealed"] is False
        assert r["production_authorized"] is False
        assert (r.get("replay") or {}).get("status") == "NOT_RUN" if isinstance(r.get("replay"), dict) else r.get("replay") == "NOT_RUN"
