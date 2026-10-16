"""Readiness trust gate — SOURCE_PRESENT ≠ SOURCE_TRUSTED ≠ AUTHORIZED."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swi_beagle.readiness import assess_readiness


def _base(**over):
    p = {
        "repositories": [],
        "structure": {"status": "MISSING"},
        "dependencies": {"status": "MISSING"},
        "device": {"status": "DETECTED"},
        "binding": {"binding_state": "OBSERVED"},
        "build": {"status": "NOT_RUN"},
        "tests": {"status": "NOT_RUN"},
        "evidence": {},
    }
    p.update(over)
    return p


def test_empty_repos_not_pipeline_ready():
    r = assess_readiness(_base(repositories=[]))
    assert r["dimensions"]["SOURCE_READY"] == "FAIL"
    assert r["PIPELINE_READY"] is False
    assert r["AUTHORIZED"] is False


def test_untrusted_source_not_pipeline_ready():
    r = assess_readiness(_base(repositories=[{
        "path": "/tmp/x",
        "origin": {"status": "UNTRUSTED_SOURCE", "allowed": False},
    }]))
    assert r["dimensions"]["SOURCE_PRESENT"] == "PASS"
    assert r["dimensions"]["SOURCE_READY"] == "FAIL"
    assert r["dimensions"]["DEVICE_READY"] == "PASS"
    assert r["PIPELINE_READY"] is False
    assert r["AUTHORIZED"] is False


def test_unknown_trust_not_pipeline_ready():
    r = assess_readiness(_base(repositories=[{
        "path": "/tmp/x",
        "origin": {"status": "UNKNOWN"},
    }]))
    assert r["dimensions"]["SOURCE_READY"] == "UNKNOWN"
    assert r["PIPELINE_READY"] is False


def test_missing_origin_metadata_unknown():
    r = assess_readiness(_base(repositories=[{"path": "/tmp/x"}]))
    assert r["dimensions"]["SOURCE_READY"] == "UNKNOWN"
    assert r["PIPELINE_READY"] is False


def test_approved_source_and_device_pipeline_ready_not_authorized():
    r = assess_readiness(_base(repositories=[{
        "path": "/tmp/x",
        "origin": {"status": "APPROVED_SOURCE", "allowed": True},
    }]))
    assert r["dimensions"]["SOURCE_READY"] == "PASS"
    assert r["dimensions"]["DEVICE_READY"] == "PASS"
    assert r["PIPELINE_READY"] is True
    assert r["AUTHORIZED"] is False
    assert r["PROVEN"] is False
    assert r["PRODUCTION_AUTHORIZED"] is False
    assert r["dimensions"]["AUTHORIZATION_READY"] == "FAIL"


def test_device_detected_unknown_source_not_ready():
    r = assess_readiness(_base(
        repositories=[{"path": "/tmp/x", "origin": {}}],
        device={"status": "DETECTED"},
    ))
    assert r["dimensions"]["DEVICE_READY"] == "PASS"
    assert r["PIPELINE_READY"] is False
