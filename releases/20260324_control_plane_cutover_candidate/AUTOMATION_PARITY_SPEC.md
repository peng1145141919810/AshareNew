# AUTOMATION_PARITY_SPEC

## Contract Source
- Old non-research phase contract verified from `F:\quant_data\Ashare\quant_research_hub_v6_repacked_clean\quant_research_hub_v6_repacked_clean\hub_v6\clock_supervisor.py`.

## Phase Parity (Old -> New C#)
- `research` -> covered in `PhaseRegistry` + `PhaseOrchestrator`
- `release` -> covered
- `preopen_gate` -> covered
- `simulation` -> covered
- `midday_review` -> covered
- `afternoon_execution` -> covered
- `afternoon_shadow` -> covered, default safe mode (no-submit + isolated namespace guard)
- `summary` -> covered (internal C# summary branch)

## Deeper Gap Parity
- Depth now: `symbol + weight + shares`
- Implemented in C#:
  - desired normalization (`DesiredStateService`)
  - actual normalization (`OmsStateFacade`)
  - layered compare + threshold policy (`GapReportService` + `GapThresholdPolicyProvider`)
- Output fields include:
  - `symbol_missing_in_actual`
  - `symbol_extra_in_actual`
  - `weight_mismatch_symbols`
  - `shares_mismatch_symbols`
  - `weight_mismatch_count`
  - `shares_mismatch_count`
  - `compare_capabilities`
  - `threshold_policy`
  - `blocking_reasons`
  - `warning_reasons`

## Authority Split (Current)
- Control plane owner: `csharp_runtime_skeleton`
- Execution lifecycle authority: `ExecutionBackendService` (C#)
- OMS lifecycle authority: `OmsLifecycleService` (C#)
- Backend executor adapter: Python canonical runtime (compatibility adapter, non-authority)

## Residual Gaps
- Backend adapter still depends on Python runtime process.
- OMS order/fill lifecycle artifacts are partially unavailable in current environment.

## Parity Verdict
- Phase parity: **high / covered**
- Control-plane authority parity: **substantially improved**
- Full runtime replacement parity: **not yet complete**
