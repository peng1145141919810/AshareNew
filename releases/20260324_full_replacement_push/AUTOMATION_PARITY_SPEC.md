# AUTOMATION_PARITY_SPEC

## Scope
- Workspace: `F:\quant_data\AshareC#`
- Old contract reference (read-only): `F:\quant_data\Ashare\quant_research_hub_v6_repacked_clean\quant_research_hub_v6_repacked_clean\hub_v6\clock_supervisor.py`
- Focus: non-research automation parity

## Phase/Host/Loop Parity Matrix
- `scheduler-host`: implemented in C# (single-run + loop)
- `scheduler-tick`: implemented in C# (auto/manual)
- `phase-run`: implemented in C# full phase graph
- `guarded-run`: implemented in C# with gate + deeper gap
- `gap-report`: implemented in C# deeper 3-layer compare
- `parity-report`: implemented in C# structured parity output
- `summary`: implemented in C# internal branch and artifacts
- `shadow`: implemented with fail-closed protection (`submit_disabled` + `broker_isolated`)

## Old Phase Graph -> New C# Status
- `research`: covered
- `release`: covered
- `preopen_gate`: covered
- `simulation`: covered
- `midday_review`: covered
- `afternoon_execution`: covered
- `afternoon_shadow`: covered (protected fail-closed path)
- `summary`: covered

## Deeper Gap Parity
- Depth: `symbol + weight + shares`
- C# owner path:
  - desired normalization: `DesiredStateService`
  - actual normalization: `OmsStateFacade`
  - layered mismatch + threshold policy: `GapReportService`

## Execution/OMS Authority Parity
- control_plane_owner: `csharp_runtime_skeleton`
- authority_owner (execution): `ExecutionBackendService` + `PhaseOrchestrator`
- authority_owner (OMS lifecycle): `OmsLifecycleService`
- adapter dependency state: `compressed_single_owner_path`
- backend executor type: `python_canonical_adapter` (compat target only)

## Residual Gaps (Minimum)
- Python adapter process is still required as backend executor target.
- Current OMS order/fill ledgers are not available in the runtime artifacts, so lifecycle completeness remains data-limited.

## Final Parity Split
- feature parity: **YES**
- authority parity: **YES**
- live cutover safety parity: **NO** (data/runtime constraints only)
