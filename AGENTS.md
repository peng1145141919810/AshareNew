# AGENTS.md

Before making changes in this repository, read `F:\quant_data\Ashare\CODEX_DEV_LOG.md`.

## Required First Steps
1. Read `CODEX_DEV_LOG.md` before touching code.
2. Treat `CODEX_DEV_LOG.md` as the current source of truth when older `README` files disagree.
3. Read these sections first: `Latest Stable Snapshot`, `Session Start Checklist`, `Known Dangerous Operations`, and `Known Issues`.
4. Check whether the user has explicitly allowed a long-running end-to-end run in the current session.
5. If you make code, config, runtime, data-path, or operational-rule changes, update `CODEX_DEV_LOG.md` before ending the turn.

## Hard Operational Rules
- Do not run the full integrated pipeline or any full-cycle validation by default.
- The user has explicitly said full validation can run for hours and freeze Codex.
- Default to lightweight checks only:
  - file inspection
  - targeted `Select-String`
  - targeted small commands
  - `python -m py_compile` on touched files
- This workspace may auto-push to GitHub after each local commit through a local post-commit hook.
- If a session needs a local-only commit in PowerShell, use `$env:DISABLE_AUTO_PUSH='1'; git commit -m "..."; Remove-Item Env:DISABLE_AUTO_PUSH`.
- `CODEX_DEV_LOG.md` may also be mirrored to Google Drive by `scripts/sync_codex_dev_log_to_gdrive.py` when the local watcher is running.
- Watcher control scripts:
  - start: `powershell -ExecutionPolicy Bypass -File F:\quant_data\Ashare\scripts\start_codex_dev_log_sync.ps1`
  - stop: `powershell -ExecutionPolicy Bypass -File F:\quant_data\Ashare\scripts\stop_codex_dev_log_sync.ps1`
- Logon autostart installer:
  - install: `powershell -ExecutionPolicy Bypass -File F:\quant_data\Ashare\scripts\install_codex_dev_log_sync_autostart.ps1`
  - remove: `powershell -ExecutionPolicy Bypass -File F:\quant_data\Ashare\scripts\remove_codex_dev_log_sync_autostart.ps1`
- Scheduled task name: `Ashare Codex Dev Log Mirror`
- Do not switch the Gmtrade bridge to the main Python environment. It must keep using the dedicated `gmtrade39` Python.
- Do not echo API tokens or duplicate secrets into normal user-facing output unless explicitly asked.

## Dev Log Maintenance
- `F:\quant_data\Ashare\CODEX_DEV_LOG.md` is a living handoff file, not a one-time snapshot.
- Future Codex sessions must append or revise the log when they materially change:
  - entrypoints
  - configs
  - runtime profiles
  - data sources
  - execution behavior
  - operational warnings
  - validation policy
- Future Codex sessions should also refresh the relevant stable sections when needed:
  - `Latest Stable Snapshot`
  - `Run Profile Quick Reference`
  - `Artifact Registry`
  - `Config Surface`
  - `Known Issues`
  - `Deferred Work`
  - `Decision Log`
- If current truth changes, update the relevant stable sections before appending the new historical change-log entry.
- Use the `Change Log Entry Template` in `CODEX_DEV_LOG.md` unless there is a strong reason not to.
- Each new log entry should include:
  - local date and time
  - type
  - scope
  - file path or module location
  - what changed
  - impact
  - validation
  - compatibility
  - rollback guidance when practical
- Do not leave undocumented behavioral changes in code.

## Current Canonical Entry
- Formal operator entry: `F:\quant_data\Ashare\launch_canonical.py`
- Wrapped business root entry: `F:\quant_data\Ashare\main_research_runner.py`
- If you are reasoning about the live code chain itself, inspect `main_research_runner.py`.
- If you are reasoning about the formal operator path, start from `launch_canonical.py`.

## Runtime Notes
- Default mode is `integrated_supervisor`.
- Default profile is `quick_test`.
- `quick_test` exists for minimal full-chain debugging.
- The live V5.1 research runtime is the embedded `quant_research_hub_v6_repacked_clean\quant_research_hub_v6_repacked_clean\v5_gpu_runtime`, not the archived root-level `quant_research_hub_v5*` copies.
- Tushare quotas and the execution-bridge dual-Python setup are documented in `CODEX_DEV_LOG.md`.
