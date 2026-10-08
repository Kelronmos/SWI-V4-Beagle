from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swi_beagle.audit import classify_origin, load_sources, normalize_origin
from swi_beagle.binding import evaluate_binding
from swi_beagle.device import detect_device
from swi_beagle.readiness import assess_readiness


def test_sources_count():
    s = load_sources(ROOT / "config" / "sources.json")
    assert len(s["sources"]) == 3


def test_allowlist_v3():
    s = load_sources(ROOT / "config" / "sources.json")
    r = classify_origin("https://github.com/Kelronmos/SWI-V3-Modules-11-22.git", s)
    assert r["allowed"] is True
    assert r["matched"] == "SWI-V3-Modules-11-22"


def test_untrusted():
    s = load_sources(ROOT / "config" / "sources.json")
    r = classify_origin("https://github.com/other/repo", s)
    assert r["allowed"] is False
    assert r["status"] == "UNTRUSTED_SOURCE"


def test_device_not_authorize():
    d = detect_device()
    assert d["authorization"] is False
    assert d["binding_state"] == "NOT_BOUND"


def test_binding_not_human_authority():
    d = detect_device()
    b = evaluate_binding(d)
    assert b["authorization"] is False
    assert b["human_authority"] == "NOT_ESTABLISHED"


def test_readiness_no_auth_promotion():
    r = assess_readiness(
        {
            "repositories": [{"x": 1}],
            "device": {"status": "DETECTED"},
            "binding": {"binding_state": "OBSERVED"},
            "build": {"status": "PASSED"},
            "tests": {"status": "PASSED"},
            "evidence": {"artifacts": ["a"]},
        }
    )
    assert r["PROVEN"] is False
    assert r["AUTHORIZED"] is False
    assert r["PRODUCTION_AUTHORIZED"] is False


def test_invariants_present():
    inv = json.loads((ROOT / "config" / "invariants.json").read_text())
    assert "BUILD PASS ≠ AUTHORIZATION" in inv["boundaries"]
