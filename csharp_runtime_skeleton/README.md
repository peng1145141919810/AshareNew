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

## Example Commands

```powershell
dotnet run --project .\src\Ashare.RuntimeSkeleton.OperatorCli\Ashare.RuntimeSkeleton.OperatorCli.csproj -- authority
dotnet run --project .\src\Ashare.RuntimeSkeleton.OperatorCli\Ashare.RuntimeSkeleton.OperatorCli.csproj -- paths F:\quant_data\AshareC#
dotnet run --project .\src\Ashare.RuntimeSkeleton.OperatorCli\Ashare.RuntimeSkeleton.OperatorCli.csproj -- bridge F:\quant_data\AshareC# quick_test research_only
```
