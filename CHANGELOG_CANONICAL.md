# Canonical Governance Changelog

This file tracks governance-layer additions that define the formal operator
path, runtime identity, and run-trace rules.

Detailed engineering handoff and runtime history remain in:
- `F:\quant_data\Ashare\CODEX_DEV_LOG.md`

## Entries

### 2026-03-21 19:29
- Phase: `1`
- Change:
  - Added the first law/manifest/profile/changelog governance files.
- Files:
  - `F:\quant_data\Ashare\PROJECT_LAW.md`
  - `F:\quant_data\Ashare\SYSTEM_MANIFEST.yaml`
  - `F:\quant_data\Ashare\RUN_PROFILES.yaml`
  - `F:\quant_data\Ashare\CHANGELOG_CANONICAL.md`
- Intent:
  - Freeze one live runtime identity and define archive/experiment semantics
    without changing business logic.

### 2026-03-21 19:36
- Phase: `2`
- Change:
  - Added the formal operator wrapper `launch_canonical.py`.
  - Added `tools/preflight_check.py` for lightweight path/profile/import/py_compile checks.
- Files:
  - `F:\quant_data\Ashare\launch_canonical.py`
  - `F:\quant_data\Ashare\tools\preflight_check.py`
  - `F:\quant_data\Ashare\AGENTS.md`
  - `F:\quant_data\Ashare\CHANGELOG_CANONICAL.md`
- Intent:
  - Make one operator-facing launch path real without changing the underlying business call chain.
  - Keep the wrapper thin by dispatching to the canonical research Python instead of assuming the shell Python is the live runtime.

### 2026-03-21 19:43
- Phase: `3`
- Change:
  - Added `tools/register_run.py`.
  - Made `launch_canonical.py` create one governance run directory and `run_manifest.json` for each formal run.
- Files:
  - `F:\quant_data\Ashare\tools\register_run.py`
  - `F:\quant_data\Ashare\launch_canonical.py`
  - `F:\quant_data\Ashare\AGENTS.md`
  - `F:\quant_data\Ashare\CHANGELOG_CANONICAL.md`
- Intent:
  - Ensure formal runs have one lightweight trace artifact without changing the business output chain.
