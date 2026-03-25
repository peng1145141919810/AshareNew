# Project Law

## Purpose
This file defines the low-risk governance layer for the live A-share system.
It does not replace business logic. It defines which paths and wrappers are
formal, live, archived, experimental, or deprecated.

For this repository specifically, `F:\quant_data\AshareC#` is currently a Rider / C# migration workspace mirror.
Unless an explicit cutover is documented in `CODEX_DEV_LOG.md`, the live operator repo still remains `F:\quant_data\Ashare`.

## Binding Rules
1. Do not replace the live business root entry by refactoring imports.
2. Do not move live runtime packages just to improve layout.
3. Do not treat archived or experimental paths as live runtime by default.
4. All governance additions must strengthen one operator path, one live runtime,
   and one run-trace chain.
5. Do not assume the Rider mirror has already replaced the live `Ashare` repo.
6. Do not modify files under `F:\quant_data\Ashare` from this workspace unless the user explicitly revokes the read-only rule.

## Canonical Runtime Law
- Workspace operator mirror:
  - `F:\quant_data\AshareC#\launch_canonical.py`
- Workspace trade-clock mirror:
  - `F:\quant_data\AshareC#\trade_clock_service.py`
- Workspace wrapped business root mirror:
  - `F:\quant_data\AshareC#\main_research_runner.py`
- Workspace code root:
  - `F:\quant_data\AshareC#\quant_research_hub_v6_repacked_clean\quant_research_hub_v6_repacked_clean`
- Current live operator repo:
  - `F:\quant_data\Ashare`
- Default mode:
  - `integrated_supervisor`
- Default profile:
  - `quick_test`
- Allowed run profiles:
  - Defined in this workspace at `F:\quant_data\AshareC#\RUN_PROFILES.yaml`
- Precision-style split:
  - `research_only` produces research artifacts and portfolio releases.
  - `execution_only` consumes a published release and applies trading-clock gates.
  - `trade_clock_service.py` is the lightweight always-on trigger process for execution.

## Formal Output Law
- Governance run-trace root:
  - `F:\quant_data\AshareC#\outputs\canonical_runs`
- Current large data/output dependency root used by the live business chain:
  - `F:\quant_data\Ashare\data`
- Formal run trace artifact:
  - `run_manifest.json`
- Rule:
  - Every formal run started from `launch_canonical.py` must have one run
    directory under `outputs\canonical_runs\<run_id>\`.

## Directory Status Definitions
- `live`
  - The current runtime code and current business outputs used by the official
    chain.
- `archive`
  - Historical code or assets kept for rollback or reference only. Not a live
    edit target.
- `experiment`
  - Samples, scratch outputs, generated candidate workspaces, or ad hoc
    research artifacts. Not a source of canonical runtime truth.
- `deprecated`
  - Paths or entrypoints kept only for transition. They must point operators to
    the current replacement.

## Current Classification
- `live`
  - `main_research_runner.py`
  - `quant_research_hub_v6_repacked_clean\quant_research_hub_v6_repacked_clean`
  - `outputs\canonical_runs`
- `external_live_dependency`
  - `F:\quant_data\Ashare\data`
- `archive`
  - `F:\quant_data\早期实验数据\Ashare_legacy_code_20260321`
- `experiment`
  - `outputs\` except `outputs\canonical_runs`
  - `quant_research_hub_v6_repacked_clean\quant_research_hub_v6_repacked_clean\examples`
- `deprecated`
  - Historical direct operator habits that bypass the governance wrapper once
    `launch_canonical.py` is in use

## Non-Goals
- No business-logic rewrite
- No import-tree rewrite
- No path cleanup that changes the live call chain
- No large directory migration
