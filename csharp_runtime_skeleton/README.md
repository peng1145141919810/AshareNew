# Ashare Runtime Skeleton

This solution is the first C# governance and orchestration skeleton for the `AshareC#` migration workspace.

## Non-Negotiable Rules

- The old live Python repo at `F:\quant_data\Ashare` is read-only from this skeleton's perspective.
- This solution must faithfully reproduce the existing logic, authority boundaries, and operational contracts.
- Research authority, release authority, safety authority, OMS authority, and broker-dispatch authority must not be collapsed together.
- Python remains the execution target for the existing research runtime until a deliberate migration step replaces a boundary.

## What This Skeleton Covers

- authority and contract models
- workspace and external-dependency path registry
- manifest/profile loading
- trade-clock and execution planning skeletons
- safety decision skeleton
- OMS ledger and authority catalog
- Python bridge command building
- operator CLI for inspecting the mapped runtime boundary
- awareness of the canonical SQLite research store path used by the new SQL-first migration work

## What This Skeleton Does Not Do Yet

- replace V5 research
- replace V6 event extraction or LLM planning
- rewrite portfolio logic
- submit broker orders directly

## Build

```powershell
dotnet build .\Ashare.RuntimeSkeleton.sln
```

Current project files target `.NET 8`, so a standard .NET 8 SDK is enough for local build and `dotnet run`.

Current runtime truth is still hybrid:
- governance/execution inspection in C#
- business runtime in Python
- research-side structured fact/factor SQLite store at `data\sql_store\research_fact_layers_v1.sqlite3`
- affordable low-cost feed SQLite store at `data\sql_store\affordable_data_v1.sqlite3`
- primary stock-alpha research line now runs through `integrated_thesis`, not the removed `three_strategy` split
- audit artifacts and public portal staging currently publish under `outputs\site_publish_stage`
- the active trade-clock profile can be inspected from C# with `runtime-profile`
- the active audit artifact surface, including `t_overlay_analysis`, can be inspected from C# with `audit-status`
- the staged site portal state and local `latest_t_audit.json` can be inspected from C# with `site-status`

## Example Commands

```powershell
dotnet run --project .\src\Ashare.RuntimeSkeleton.OperatorCli\Ashare.RuntimeSkeleton.OperatorCli.csproj -- authority
dotnet run --project .\src\Ashare.RuntimeSkeleton.OperatorCli\Ashare.RuntimeSkeleton.OperatorCli.csproj -- paths F:\quant_data\AshareC#
dotnet run --project .\src\Ashare.RuntimeSkeleton.OperatorCli\Ashare.RuntimeSkeleton.OperatorCli.csproj -- runtime-profile F:\quant_data\AshareC#
dotnet run --project .\src\Ashare.RuntimeSkeleton.OperatorCli\Ashare.RuntimeSkeleton.OperatorCli.csproj -- audit-status F:\quant_data\AshareC#
dotnet run --project .\src\Ashare.RuntimeSkeleton.OperatorCli\Ashare.RuntimeSkeleton.OperatorCli.csproj -- site-status F:\quant_data\AshareC#
```
