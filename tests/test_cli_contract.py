"""CLI/engine result schema contract — no AttributeError on replay."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "swi_beagle", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": str(ROOT)},
    )


def test_cli_status_ok():
    p = _run_cli("status")
    assert p.returncode == 0
    assert "PROVEN=NO" in p.stdout


def test_cli_build_missing_source_no_traceback():
    p = _run_cli("build", "--source", "/tmp/swi-missing-path-xyz")
    assert "AttributeError" not in (p.stderr or "")
    assert "AttributeError" not in (p.stdout or "")
    # Engine BLOCKED → exit 0 per CLI contract
    assert p.returncode == 0
    assert '"status": "BLOCKED"' in p.stdout or '"status": "BLOCKED"' in p.stdout.replace(" ", "")
    assert "NOT_RUN" in p.stdout  # REPLAY


def test_cli_build_force_fail_exit_nonzero():
    # minimal real git fixture
    import tempfile
    td = Path(tempfile.mkdtemp())
    src = td / "src"
    (src / "swi_v2").mkdir(parents=True)
    (src / "swi_v2" / "__init__.py").write_text("#\n")
    subprocess.run(["git", "init"], cwd=src, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=src, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=src, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/Kelronmos/SWI-V2-Modules-11-22.git"],
        cwd=src, check=True, capture_output=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=src, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "c"], cwd=src, check=True, capture_output=True)
    p = _run_cli("build", "--source", str(src), "--force-fail")
    assert "AttributeError" not in (p.stderr or "")
    assert p.returncode == 1  # FAIL status
    assert "FAIL" in p.stdout


def test_cli_forged_authorized_cannot_appear_as_trusted():
    """Forged engine authorized=True must not become trusted CLI AUTHORIZED."""
    import io
    import sys
    from contextlib import redirect_stdout
    from unittest import mock
    import swi_beagle.__main__ as mainmod

    def fake_engine(source, beagle_root, *, force_fail=False, skip_source_check=False):
        return {
            "status": "PASS",
            "authorized": True,
            "proven": True,
            "sealed": True,
            "production_authorized": True,
            "source": {"commit": "abc"},
            "build": {"status": "PASSED"},
            "tests": {"status": "PASSED"},
            "replay": {"status": "NOT_RUN"},
            "security": {"status": "PASS"},
        }

    old = sys.argv
    sys.argv = ["swi_beagle", "build", "--source", "/tmp/x"]
    buf = io.StringIO()
    try:
        with mock.patch("swi_beagle.build_engine.isolated_build", fake_engine):
            with redirect_stdout(buf):
                rc = mainmod.main()
    finally:
        sys.argv = old
    out = buf.getvalue()
    assert rc == 0
    assert '"AUTHORIZED": false' in out or '"AUTHORIZED": false' in out.lower()
    assert '"PROVEN": false' in out
    # Must not present trusted true ceilings
    assert '"AUTHORIZED": true' not in out
    assert '"PROVEN": true' not in out
    assert "engine_authorized_claim" in out  # observation retained separately


def test_cli_non_dict_engine_result_is_fail():
    import io
    import sys
    from contextlib import redirect_stdout
    from unittest import mock
    import swi_beagle.__main__ as mainmod

    old = sys.argv
    sys.argv = ["swi_beagle", "build", "--source", "/tmp/x"]
    buf = io.StringIO()
    try:
        with mock.patch("swi_beagle.build_engine.isolated_build", lambda *a, **k: "PASS"):
            with redirect_stdout(buf):
                rc = mainmod.main()
    finally:
        sys.argv = old
    out = buf.getvalue()
    assert rc == 1
    assert "ENGINE_RESULT_NOT_DICT" in out or '"status": "FAIL"' in out
    assert '"AUTHORIZED": false' in out


def test_cli_engine_exception_is_fail_not_success():
    import io
    import sys
    from contextlib import redirect_stdout
    from unittest import mock
    import swi_beagle.__main__ as mainmod

    def boom(*a, **k):
        raise RuntimeError("boom")

    old = sys.argv
    sys.argv = ["swi_beagle", "build", "--source", "/tmp/x"]
    buf = io.StringIO()
    try:
        with mock.patch("swi_beagle.build_engine.isolated_build", boom):
            with redirect_stdout(buf):
                rc = mainmod.main()
    finally:
        sys.argv = old
    out = buf.getvalue()
    assert rc == 1
    assert "ENGINE_EXCEPTION" in out
    assert '"AUTHORIZED": false' in out
