"""Phase 5 break tests — refuse unsafe transitions. Keep fixtures small."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swi_beagle.build_engine import isolated_build, scan_for_secrets, scan_path_for_secrets


def _mini_v2(tmp: Path) -> Path:
    pkg = tmp / "swi_v2"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("# mini\n")
    (tmp / "requirements.txt").write_text("# none\n")
    git = tmp / ".git"
    git.mkdir()
    (git / "HEAD").write_text("ref: refs/heads/main\n")
    (git / "refs" / "heads").mkdir(parents=True)
    (git / "refs" / "heads" / "main").write_text("deadbeef" * 5 + "\n")
    (git / "config").write_text(
        "[remote \"origin\"]\n\turl = https://github.com/Kelronmos/SWI-V2-Modules-11-22.git\n"
    )
    return tmp


def test_unknown_source_blocks_build(tmp_path):
    r = isolated_build(tmp_path / "nope", ROOT, skip_source_check=True)
    assert r["status"] == "BLOCKED"
    assert r["tests"]["status"] == "NOT_RUN"
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


def test_mini_build_pass_path(tmp_path):
    src = _mini_v2(tmp_path / "v2")
    r = isolated_build(src, ROOT)
    assert r["status"] == "PASS"
    assert r["authorized"] is False
    assert r.get("proven") is False
