# SWI V4 Beagle

**Deployment · Rebuild · Diagnostics · Device-binding · Test control plane**

```
V1 → V2 → V3 → V4 Beagle
```

V4 does **not** replace SWI V1, V2, or V3.
V4 does **not** authorize, seal, or prove SWI.

> Beagle shows what exists, what is missing, what failed, and actual readiness.
> It does **not** turn a successful build into authorization.

## Quick start

```bash
cd SWI-V4-Beagle
export PYTHONPATH=.
python3 -m swi_beagle audit --roots ..
python3 -m swi_beagle build --source /path/to/SWI-V2-Modules-11-22
python3 -m swi_beagle status
python3 -m swi_beagle dashboard   # http://127.0.0.1:8777
```

Launchers: `launchers/beagle.sh` · `beagle.bat` · `beagle.ps1`

## Pipeline

```
DISCOVER → IDENTIFY → STRUCTURE → DEPENDENCIES → DEVICE → BINDING
→ ISOLATED BUILD (gated) → TEST (only if build PASS) → DIAGNOSIS
→ EVIDENCE → SECURITY SCAN → READINESS
```

Default mode is **AUDIT only**. Rebuild requires explicit `build`.

## Boundaries

```
BUILD PASS ≠ AUTHORIZATION
PIPELINE READY ≠ AUTHORIZATION
DEVICE BOUND ≠ AUTHORIZATION
TESTED ≠ PROVEN ≠ SEALED ≠ AUTHORIZED
CI GREEN ≠ SWI AUTHORIZED
```

## Phase 5 (V2 isolated build gate)

Implemented:

- Source allowlist + identity capture
- Isolated workspace under `runs/<RUN_ID>/`
- Dependency discovery (no silent install)
- Build gate (`import` smoke; compileall best-effort)
- Test gate only after BUILD PASS
- Break tests (unknown source, forced fail, auth ceiling, secret scan)
- Evidence JSON + SHA-256

Measured against local V2 `ed600c05…` (adversarial suite): BUILD PASS, 61 tests PASS.
**PROVEN / SEALED / AUTHORIZED / PRODUCTION_AUTHORIZED = NO**

## Status of this package

| Item | Status |
|------|--------|
| Source audit | Implemented |
| Structure audit | Implemented |
| Device detection | Implemented |
| Binding diagnostics | Implemented (not auto-bound) |
| Isolated build gate | Implemented |
| Test gate | Implemented |
| Readiness dimensions | Implemented |
| Evidence export | Implemented |
| Dashboard | Minimal |
| Full-tree snapshot of large trees | Partial (lean snapshot preferred) |
| Replay execution | NOT_RUN |
| Android / iOS clients | Not claimed |
| PROVEN / SEALED / AUTHORIZED | **NO** |

## Approved sources (inspect only)

- https://github.com/Kelronmos/SWI-V1-Module-1-10
- https://github.com/Kelronmos/SWI-V2-Modules-11-22
- https://github.com/Kelronmos/SWI-V3-Modules-11-22
