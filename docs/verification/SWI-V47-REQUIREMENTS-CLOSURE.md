# SWI V4.7 Requirements Closure Record

**Record date (UTC):** 2026-10-10
**Target version:** SWI V4.7
**Repository:** [Kelronmos/SWI-V4-Beagle](https://github.com/Kelronmos/SWI-V4-Beagle)
**Public baseline assessed:** `2e8ced1e1c4beda7199b5e80ff84b5721186bce5`
**Record type:** Verification / requirements-closure evidence. **Not** historical source recovery, formal proof, or production authorization.

## 1. Purpose and scope

This document records evidence for:

1. The **public baseline** at the pinned commit (what is present and what fails).
2. A **reconstructed candidate** (`NEW_RECONSTRUCTION` / `RECONSTRUCTED_IMPLEMENTATION`) tested in isolation.

Candidate results **do not** repair or validate the public baseline.
`RECONSTRUCTED_IMPLEMENTATION` is **not** verified recovered historical source.

## 2. Distinctions preserved

```text
Named ≠ Implemented ≠ Tested ≠ Proven ≠ Sealed ≠ Authorized
Candidate PASS ≠ Public baseline repaired
RECONSTRUCTED_IMPLEMENTATION ≠ Recovered historical source
DATA ≠ EVIDENCE ≠ ADMISSION ≠ AUTHORIZATION ≠ ACTION
UNKNOWN ≠ FALSE
```

## 3. Public baseline status

**Commit:** `2e8ced1e1c4beda7199b5e80ff84b5721186bce5`

| Finding | Classification |
|---------|----------------|
| `swi_beagle/build_engine.py` | **ABSENT** from public tree |
| Phase 5 collection | **FAIL** — `ModuleNotFoundError: No module named 'swi_beagle.build_engine'` |
| Core tests (`tests/test_beagle_core.py`) | **7 passed** (independently reproducible on clean checkout) |
| Phase 5 behavioral tests | **NOT_RUN** (collection blocked) |

| Requirement | Public baseline | Notes |
|-------------|-----------------|-------|
| BE-001–BE-006 | **UNVERIFIED** | Behavioral tests did not execute |
| BE-007 | **FAIL_WITH_EVIDENCE** | Required module/interface absent |
| BE-008–BE-009 | **UNVERIFIED** | Sufficient public-baseline runtime evidence not established |

A collection error is **not** a behavioral FAIL of BE-001–BE-006.

## 4. Reconstructed candidate status

| Field | Value |
|-------|--------|
| Classification | `NEW_RECONSTRUCTION` / `RECONSTRUCTED_IMPLEMENTATION` |
| Implementation | `swi_beagle/build_engine.py` (candidate only) |
| SHA-256 | `7489da958e6ca206fc40691cf05a31e30c53d6d8658cd31097791e4f83001806` |
| Hash verification | Recalculated against local candidate file — **MATCH** |

| Suite | Reported / verified result |
|-------|----------------------------|
| Phase 5 | **6 passed** |
| Core | **7 passed** |
| Adversarial | **10/10 passed** |
| Authority-boundary | **6/6 passed** |

| Requirement | Candidate | Notes |
|-------------|-----------|-------|
| BE-001–BE-007 | **PASS_WITH_EVIDENCE** | Within stated test scope |
| BE-008–BE-009 | **PASS_WITH_EVIDENCE** | Runtime force-false ceilings + invariants + no counterexample in tested scope; **not** formal proof of all paths |

## 5. Evidence packages

Local evidence directories (may be inaccessible to repository readers):

- Requirements-closure: workspace package with dual-domain registers (checksum verification: **18 files, 0 mismatches** when inspected).
- Candidate-verification archive: reported SHA-256 `fc07a56ee90eb94d67499480ac3943ed548de0409e51538f32766d6dfbfafd5b` — **recalculated MATCH** against accessible zip when present.
- Prior candidate verification record SHA-256: `9d54c0747c014470ab9c724bf9090aeba6cb6c56110c3c5a07882f2ca0c99331` — **recalculated MATCH** when present.

## 6. Outstanding content-tree hash discrepancy

A previously recorded **candidate content-tree** hash did not match a later recalculation under possibly different inclusion/exclusion rules. The prior value was **preserved**, not overwritten.

**Status:** OUTSTANDING — a matching implementation-file hash does **not** establish that the entire candidate tree is identical across runs.

## 7. Provenance limitations

- V2 approved object `ed600c05…` remains **BLOCKED_PROVENANCE** (not independently obtainable from the public remote at time of assessment).
- Candidate code is **not** claimed as byte-identical to any missing historical archive.

## 8. Authorization ceilings

```text
PROVEN = NO
SEALED = NO
AUTHORIZED = NO
PRODUCTION_AUTHORIZED = NO

PUBLIC_BASELINE_MODIFIED = NO
MERGE = NO
DEPLOY = NO
```

Passing candidate tests do **not** establish formal proof, production readiness, or authorization.

## 9. Reproduction (public baseline)

```bash
git clone https://github.com/Kelronmos/SWI-V4-Beagle.git
cd SWI-V4-Beagle
git rev-parse HEAD   # expect 2e8ced1e… (or pin that commit)
PYTHONPATH=. python3 -m pytest --collect-only -q tests/test_phase5_gates.py
# expect ModuleNotFoundError: swi_beagle.build_engine
PYTHONPATH=. python3 -m pytest -q tests/test_beagle_core.py
# expect 7 passed
```

Candidate reproduction requires the separate reconstruction tree and is **not** identical to the published commit.

## 10. Summary

| Domain | Outcome |
|--------|---------|
| Public baseline | Unrepaired; BE-007 FAIL; Phase 5 not executable |
| V4.7 candidate | Bounded PASS_WITH_EVIDENCE under isolated tests |
| Requirements closure | **EVIDENCE_RECORDED** — not SWI V4.7 = PROVEN |

*End of record.*
