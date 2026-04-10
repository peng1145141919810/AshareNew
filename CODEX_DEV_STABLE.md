# Codex Stable Snapshot

## Document Contract
- This file is the stable operational truth for `F:\quant_data\AshareC#`.
- Historical session records live in `CODEX_DEV_UPDATES.md`.
- Fast retrieval pointers live in `CODEX_DEV_LOG_INDEX.md`.
- When current truth changes, update this file first, then append an indexed entry to `CODEX_DEV_UPDATES.md`, then refresh the index file.

## Latest Stable Snapshot
- Snapshot time: `2026-04-10 19:35:00`
- Workspace root: `F:\quant_data\AshareC#`
- Formal operator entry: `launch_canonical.py`
- Wrapped business root: `main_research_runner.py`
- Trade clock entry: `trade_clock_service.py`
- Active runtime root: `src\ashare`
- Control-plane helper package: `ashare_control`
- Formal run trace root: `outputs\canonical_runs`
- Formal run manifest: `outputs\canonical_runs\<run_id>\run_manifest.json`
- Workspace default launcher mode/profile: `integrated_supervisor` / `quick_test`
- Trade-clock service default profile: `daily_production`
- Canonical data root in manifest: `data`
- Live public portal source bundle: `site_portal`
- Site publish stage: `outputs\site_publish_stage`
- C# runtime status: governance/orchestration skeleton only, not the live business runtime replacement

## Session Start Checklist
1. Read `CODEX_DEV_LOG.md`, then this file, then `CODEX_DEV_LOG_INDEX.md`.
2. Confirm whether the user has explicitly allowed any long-running end-to-end run in the current session.
3. Assume `F:\quant_data\Ashare` is read-only unless the user explicitly says otherwise.
4. Start reasoning from `launch_canonical.py` for governance flow and `main_research_runner.py` for runtime flow.
5. Treat `src\ashare` as the active Python runtime root, not the deleted repacked path family.
6. Read `CODEX_SECURE_OPS.md` before touching SSH-dependent deployment scripts, Git publishing scripts, or secret-adjacent runtime settings.
7. If you change behavior or operational truth, update this file, `CODEX_DEV_UPDATES.md`, and `CODEX_DEV_LOG_INDEX.md` before ending the turn.

## Workspace Identity
- This repository is the Rider / C# migration workspace copy.
- It now contains the active Python runtime tree under `src\ashare`.
- It still depends on machine-local runtime secrets and settings, especially `src\ashare\engine\local_settings.py`.
- The old live repo `F:\quant_data\Ashare` remains an operationally protected upstream and should be treated as read-only from this workspace.
- Large runtime data and generated artifacts are increasingly mirrored locally, but external backfills and legacy environment dependencies may still point back to the old machine layout.

## Canonical Runtime Chain
1. `launch_canonical.py`
2. Lightweight preflight via `tools\preflight_check.py` unless `--skip-preflight`
3. Canonical run registration via `tools\register_run.py`
4. Research Python resolved from `src\ashare\engine\local_settings.py`
5. `main_research_runner.py`
6. Runtime config generation into `src\ashare\configs\hub_config.v6.runtime.<profile>.json` and alias paths
7. Control-plane snapshot write into `site_portal\control_plane_snapshot.json`
8. Mode dispatch into `src\ashare\engine\...`

## Cross-Language Boundary
- Active business runtime is still Python and the C# skeleton still consumes many audit/state artifacts from disk.
- Active C# -> Python active invocation path now prefers a local loopback RPC host instead of direct stdout-only process coupling:
  - Python RPC host script: `python_rpc_bridge.py`
  - Default endpoint: `http://127.0.0.1:8765`
  - Health path: `/health`
  - Invoke path: `/invoke`
  - Runtime state path: `/runtime-state`
- `csharp_runtime_skeleton\src\Ashare.RuntimeSkeleton.PythonBridge\PythonProcessBridge.cs` now tries RPC first and falls back to direct process launch if the host cannot be reached.
- `csharp_runtime_skeleton\src\Ashare.RuntimeSkeleton.OperatorCli\Program.cs` now supports both legacy positional workspace-root usage and explicit `--workspace-root` / `-w` usage, so Python passthrough flags like `--preflight-only` no longer collide with CLI path parsing.
- This means active launch paths such as canonical run, trade clock run, summary run, and execution backend invocation are no longer forced to treat stdout as the only transport channel.
- JSON/CSV artifacts are still retained as audit and runtime state outputs; this change only upgrades the active invocation transport.
- Verified smoke path: `dotnet run ... canonical-run --workspace-root F:\quant_data\AshareC# --preflight-only --profile quick_test --mode execution_only` now reports `rpc_used: True`; current non-zero exit comes from Python preflight failure, not bridge/CLI parsing failure.

## Runtime State Query Layer
- `csharp_runtime_skeleton\src\Ashare.RuntimeSkeleton.Execution\RuntimeStateQueryService.cs` is now the single C# query surface for execution/runtime status aggregation.
- It centralizes reads for:
  - release contract
  - clock state
  - safety state
  - OMS summary and actual-state snapshots
  - `outputs\site_publish_stage\operator_runtime_context.json`
  - `outputs\site_publish_stage\control_plane_snapshot.json`
- `RuntimeStateAggregator` now resolves `release_id`, `trade_date`, `clock_phase`, `heartbeat_at`, `safety_mode`, and `gate_reason` through this query layer instead of directly scattering file reads in the aggregator.
- Current authority order is:
  - operator runtime context
  - control-plane snapshot
  - release / clock / safety / OMS artifacts
- The query layer now prefers one RPC bundle from `/runtime-state` for all of these:
  - `latest_release.json`
  - release manifest referenced by `latest_release.json`
  - target positions existence/path referenced by the release manifest
  - `clock_state.json`
  - `system_safety_state.json`
  - `oms_summary.json`
  - `latest_actual_portfolio_state.json`
  - `intent_ledger_latest.csv`
  - `order_ledger_latest.csv`
  - `fill_ledger_latest.csv`
  - `operator_runtime_context.json`
  - `control_plane_snapshot.json`
- If any of those cannot be obtained from the bridge, the corresponding C# services still fall back to local file reads.
- `status` / `doctor` can expose the active transport through `state_query_transport`; current mixed mode is `rpc_runtime_state+file_fallback`.
- `DesiredStateService`, `GapReportService`, and `OmsLifecycleService` are now also wired to the same query layer, so desired-vs-actual comparison paths no longer reintroduce separate release/OMS file scans as their primary truth source.
- OMS lifecycle capture now also prefers RPC-delivered ledger metadata for intent/order/fill availability and row counts before falling back to local CSV reads.
- This still does not remove file-backed state yet; it introduces a stable abstraction boundary so later migration to SQLite or broader RPC status queries can happen without changing the aggregator call sites again.

## Canonical Modes And Profiles

### Profiles
- `quick_test`: minimal real integrated debug profile, research cycles `1`
- `daily_production`: stable scheduled research/release profile, research cycles `3`
- `overnight`: heavy nightly research profile, research cycles `8`

### Modes
- Main modes: `integrated_supervisor`, `research_only`, `release_only`, `execution_only`, `midday_review_only`, `resume_downstream`
- Support modes: `oms_validate`, `full_cycle`, `ingest_only`, `extract_only`, `gap_only`, `industry_router_only`, `plan_only`, `bridge_only`, `intraday_tactics_only`

## Trade-Clock Truth
- Service entry is `trade_clock_service.py`.
- It resolves runtime root the same way as the canonical launcher and writes a generated runtime config when `--config` is omitted.
- It runs lightweight preflight for `research_only`, `release_only`, `execution_only`, and `midday_review_only` before entering the clock loop.
- Latest trade-clock preflight status is written to `data\trade_clock\runtime\preflight_status.json`.
- Current default CLI profile in `trade_clock_service.py` is `daily_production`, which is different from the global launcher default `quick_test`.
- `scripts\start_trade_clock.ps1` reads `src\ashare\engine\local_settings.py` (and the example file) for Python resolution; it no longer points at deleted repacked `hub_v6` paths.
- `trade_clock.runtime_hot_reload` now defaults off (`TRADE_CLOCK_RUNTIME_HOT_RELOAD_ENABLED=False` in `local_settings.example.py`) so always-on supervisors are not torn down by hub-tree churn; turn it on only when you intentionally want config-driven reloads.
- Hot-reload fingerprinting ignores `__pycache__` and the embedded candidate paths for `local_settings` now resolve under `src\ashare` (the previous doubled `src\ashare\src\ashare` segment was incorrect).

## Runtime Configuration Surface
- Governance manifest: `SYSTEM_MANIFEST.yaml`
- Allowed profiles/modes: `RUN_PROFILES.yaml`
- Runtime config examples and generated configs: `src\ashare\configs`
- Strategy activation weights, overlay boosts, and priority blend are now config-backed under `strategy_activation` in the runtime config, not hard-coded only inside `strategy_activation.py`
- External source seed currently under top-level `configs`: `configs\external_sources\qianzhan_seed_urls.json`
- Industry-router configs: `src\ashare\configs\industry_router\*`
- Market-state config: `src\ashare\configs\market_state\default.json`
- Technical-confirmation config: `src\ashare\configs\technical_confirmation\default.json`
- T-overlay policy: `src\ashare\configs\t_overlay\t_audit_policy.json`
- Gmtrade runtime config examples and local config: `src\ashare\configs\gmtrade_runtime_config.*.json`
- Global-objective and EMS defaults now live in the generated runtime config under `global_objective` and `execution_management`; `config_builder.py` seeds those sections from `local_settings.py` / `local_settings.example.py`.
- Current execution account semantics on this machine are:
  - `simulation`: purely simulated matching / mock execution path
  - `precision`: precision-matching paper account path on the Gmtrade side; this is still a simulated account operationally, not live capital
  - future real-money execution is intended to move to QMT / QM rather than reusing the current Gmtrade simulation bridge

## Artifact Registry

### Formal Governance Artifacts
- Canonical run manifests: `outputs\canonical_runs\<run_id>\run_manifest.json`
- Latest control-plane snapshot source: `site_portal\control_plane_snapshot.json`
- Publish-stage site bundle: `outputs\site_publish_stage`

### Trade-Clock And Intraday
- Trade-clock runtime preflight: `data\trade_clock\runtime\preflight_status.json`
- Clock account snapshot: `data\trade_clock\clock_account_snapshot.json`
- Intraday proxy latest root: `data\trade_clock\intraday_proxy\latest`
- Intraday tactics latest orders: `data\trade_clock\intraday_tactics\latest\intraday_tactical_orders.json`

### Release, OMS, And Execution
- Latest release family: `data\trade_release_v1`
- OMS ledgers root: `data\live_execution_bridge\oms_v1\ledgers`
- OMS snapshots root: `data\live_execution_bridge\oms_v1\snapshots`
- `src\ashare\engine\oms\runtime.py` now emits explicit `ok` / `status` fields in `execution_report_*.json`, and `src\ashare\engine\execution_bridge_runner.py` infers the same success contract for older report-shaped JSON payloads that omitted those fields.
- `src\ashare\engine\portfolio_release.py` now keeps `trade_date=today` as long as the current trading day still has at least one remaining execution window; it no longer flips to the next trading day immediately after the first morning window starts.
- `src\ashare\engine\intraday_proxy_store.py` now treats Eastmoney minute K-line history as the default `rt_min` provider (`market_pipeline.rt_min_provider = eastmoney`) with Tushare as fallback; quote/list/tick proxy pulls remain on the existing Tushare crawler path.
- `src\ashare\engine\portfolio_recommendation.py` now emits `global_objective_snapshot.json` and `harvest_risk_assessment.json` beside `portfolio_recommendation.json` so downstream schedulers can consume normalized objective / adversarial signals without re-deriving them from the whole recommendation payload.
- `src\ashare\engine\execution_manager.py` now emits an EMS-layer decision artifact under `data\trade_clock\ems\<namespace>\<timestamp>\execution_management_decision.json` and carries `global_objective`, `harvest_risk`, and EMS posture into the execution dispatch chain.

### SQL Stores
- Runtime research SQLite: `data\sql_store\research_data_v1.sqlite3`
- Research fact layer SQLite: `data\sql_store\research_fact_layers_v1.sqlite3`
- Affordable data SQLite: `data\sql_store\affordable_data_v1.sqlite3`

## Current Architecture Truth
- Python business runtime lives under `src\ashare\engine`.
- C# skeleton under `csharp_runtime_skeleton` is for pathing, authority models, CLI observability, and Python bridge orchestration, not direct strategy replacement.
- Control-plane snapshot generation is centralized in `ashare_control\control_plane.py`.
- `strategy_activation.py` now reads named weight groups from config and writes the effective weight set into the activation summary, so activation/ranking constants are auditable instead of buried only in code.
- The active engine surface includes dedicated modules for:
  - `candidate_pipeline.py`
  - `portfolio_construction_pipeline.py`
  - `strategy_activation.py`
  - `clock_phase_registry.py`
  - `remote_clock_delegate.py`
  - `constraint_brain.py`
  - `llm_trace.py`
  - `llm_operating_brain.py`
  - `intraday_tactics\`
  - `intraday_state_machine\`
  - `market_state\`
  - `oms\`
  - `portfolio\`
- V5.1 candidate codegen under `src\ashare\research_brain\hub\codegen.py` no longer asks the LLM to emit free-form Python modules directly.
- Current candidate-lab flow is now:
  - each provider attempt first emits a lightweight structured `intent`, then emits the final structured JSON spec for `feature_pack`, `train_override`, or `generated_model`
  - local validators enforce schema, naming, numeric bounds, and allowed feature-formula helpers
  - a deterministic local compiler renders those validated specs into Python modules in the candidate lab
  - compiled modules still go through compile/import validation before the candidate can run
  - spec repair remains bounded and is now provider-tier aware: local Ollama first, DeepSeek next, OpenAI last when configured and reachable
- The V5.1 `llm_brain` config surface now supports `provider_tiers`, so codegen can escalate by cost/quality tier instead of hardwiring one provider:
  - typical order is `local_ollama` -> `deepseek` -> `openai`
  - legality is judged locally by schema validation plus compiled-module validation, not by model self-report
  - unresolved invalid specs still fall back to deterministic baseline specs after tier exhaustion
- Local Ollama shared clients now short-circuit after recent healthcheck failure or timeout instead of repeatedly blocking:
  - `llm_router.LocalOllamaChatClient` performs a cached `/api/tags` health probe before role calls
  - recent timeout/unreachable states enter a short cooldown and return `service_cooldown` / `service_unavailable`
  - the event-extract-specific local worker applies the same cooldown pattern before retrying `/api/chat`
- V5.1 generated model specs now canonicalize common tree-model aliases before legality checks:
  - `xgboost` / `xgb` family hints normalize into supported local families
  - `n_estimators`, `num_trees`, and `eta` normalize into local schema keys
  - tree-style specs carrying `min_child_weight` can reroute into `extra_trees` and map that weight into `min_samples_leaf`
- V5.1 training-override specs now also normalize the most common low-cost-tier schema drifts before legality checks:
  - `sample_weight_mode` aliases like `balanced` / `uniform` normalize into supported local values
  - ratio-style `feature_cap` values can normalize into an integer cap using local context
  - pair-style `clip_label_quantile` values like `[0.05, 0.95]` normalize into the local single-sided quantile form
- Candidate labs now store both spec and compiled-module artifacts:
  - `feature_pack.spec.json` + `feature_pack.py`
  - `train_override.spec.json` + `train_override.py`
  - `generated_model.spec.json` + `generated_model.py`
  - validation, selected provider intent, and repair history in `workspace_validation.json`
- `src\ashare\research_brain\hub\training_engine.py` treats unresolved invalid generated artifacts as a candidate-level skip (`budget_action=skip_invalid_codegen`) before training starts, so one bad generated candidate does not crash the whole V5.1 batch.
- Portfolio recommendation and V2A portfolio-control stages now defensively tolerate missing optional candidate columns such as `is_existing_position`, `event_fact_backed`, `router_allow_entry`, `tech_allow_entry`, `current_weight_ref`, and `portfolio_weight` instead of assuming `DataFrame.get(...).fillna(...)` always returns a Series.
- A bounded manual end-to-end smoke has now been verified across:
  - `research_only` producing fresh V5.1 output
  - manual portfolio recommendation regeneration
  - `release_only` publishing a fresh release
  - `execution_only --execution-mode simulation` producing OMS ledgers, control feedback, research-meta feedback, and execution report artifacts
  - `plan_only` reloading `oms_v1\feedback\research_meta_feedback_latest.json` into `research\context_pack\research_context_pack.json`
- The system is no longer truthfully described by the old `hub_v6` or repacked-root naming as a runtime root, even though some compatibility references still exist in helper code.

## Operational Rules
- Do not run the full integrated pipeline by default.
- Use lightweight validation first: file inspection, targeted commands, `python -m py_compile`, and small probes.
- Do not modify `F:\quant_data\Ashare` from this workspace.
- Do not switch the broker bridge to the main Python environment; keep `GMTRADE_PYTHON_EXECUTABLE` on the dedicated Gmtrade / 掘金 adapter interpreter (on this machine the template points at Python 3.9; prefer a dedicated `gmtrade39` venv `Scripts\\python.exe` when you maintain one).
- Do not echo secrets into user-facing output.
- Unless the user explicitly asks for mock matching, default manual execution probes to the runtime default `precision` account mode instead of overriding to `simulation`.
- Treat `precision` here as the default paper-trading / precision-matching account, not as live trading.
- Treat `simulation` and `precision` as different paper-execution semantics; do not conflate either of them with the future QMT / QM real-money path.
- The interpreter behind `GMTRADE_PYTHON_EXECUTABLE` must have the `gmtrade` package installed; otherwise the health probe and OMS bridge fail before login with `ModuleNotFoundError: No module named 'gmtrade'`.
- Secret-adjacent operating notes now live in `CODEX_SECURE_OPS.md`; use that file for SSH/credential workflow memory without storing secret values.
- Watch for auto-push behavior on commit because a local post-commit hook may publish automatically.

## Known Dangerous Operations
- Running `launch_canonical.py` without `--preflight-only` starts a real runtime chain.
- `quick_test` is still a real integrated path, not a trivial smoke test.
- `trade_clock_service.py` can enter an always-on loop; use `--once` for bounded inspection.
- `execution_only` without gating or shadow protections can reach the broker bridge.
- `release_only` can rewrite latest release pointers and downstream execution truth.
- Site publish scripts can replace contents under `outputs\site_publish_stage` and publish targets.

## Known Issues
- `README.md` and several legacy sub-readmes had mojibake and stale path assumptions before this rewrite; older copies should not be trusted over this file.
- `tools\preflight_check.py` still contains legacy import targets under `hub_v6.*`; treat it as a lightweight guardrail, not a full proof that naming migration is complete.
- `local_settings.example.py` pins `PYTHON_EXECUTABLE` to the workspace `\.venv\Scripts\python.exe` (Python **3.14** with `requirements_v6_runtime` installed) and `GMTRADE_PYTHON_EXECUTABLE` to Python **3.9** for the broker adapter; the bare `Python314` install under `AppData\Local\Programs` is not the full research stack. `launch_canonical.py` resolves the research child via `engine.local_settings`. Private overlays should preserve that split so canonical research does not run on the Gmtrade-only interpreter.
- On this machine, `C:\Users\Administrator\AppData\Local\Programs\Python\Python39\python.exe` now has `gmtrade 3.0.6` installed and passes the health probe again. If broker health regresses on another machine, verify that exact interpreter first before debugging token/account settings.
- `sql_store.sqlite_connection` enables WAL, `busy_timeout`, and a longer busy wait on connect; `market_pipeline.sync_enriched_daily_from_tushare` holds one SQLite connection for the whole enriched sync to cut down `database is locked` races when the trade clock or RPC bridge touches `research_data_v1.sqlite3` at the same time.
- If `PYTHON_EXECUTABLE` is left as a placeholder in a private overlay, the fallback is still `PATH` `python.exe`, which may lack `pypdf` and other research deps; install `src\ashare\requirements_v6_runtime.txt` on that interpreter or set an explicit path.
- Historical `execution_report_*.json` files created before `2026-04-10 15:35` may omit explicit `ok` / `status`; use the bridge parser or inspect the rest of the report structure before treating those older artifacts as hard execution failures.
- Releases published after all configured execution windows for the day still roll forward to the next trading day; the fix only changes the earlier misclassification of midday manual releases when an afternoon execution window still remained.
- Eastmoney intraday-minute integration currently covers the `rt_min` / minute-bar path only; it does not yet replace the Tushare-backed realtime quote/list/tick proxy endpoints.
- The new global-objective / EMS integration is an execution-and-audit scaffold first: it centralizes objective signals and execution posture, but it does not yet dynamically rewrite research cycle counts or route budgets inside the upstream research runner.
- EMS is now a distinct execution-policy layer in Python (`execution_ems.py`), but it is still advisory-to-bridge rather than a fully separate long-lived intraday controller service or a QMT / QM execution adapter.
- The bounded end-to-end smoke recorded earlier hit the `simulation` account only because the command explicitly passed `--execution-mode simulation`; the workspace default `quick_test` runtime config and execution-policy default are already `precision`, and `execution_bridge_runner` correctly maps that to the `account_profiles.precision` account id / alias.
- `scripts\run_validation_tiers.py` currently resolves `_hub_root()` as `src/ashare/src/ashare`, which does not match the actual runtime root and should not be treated as canonical validation until corrected.
- Some helper scripts and docs still use historical terminology from deleted repacked roots or old website deployment flow.
- The workspace is a dirty tree with many unrelated modifications; do not assume uncommitted files belong to the current task.
- The new structured-spec compiler reduces syntax-fragment failures, but unresolved failures are still possible when the LLM repeatedly emits invalid specs or asks for unsupported formula helpers / model params; those candidates now skip with explicit validation diagnostics instead of taking down the full batch.
- Current smoke verification on this machine shows the tier escalation path is live, but provider quality still differs materially:
  - local Ollama can sometimes satisfy simple feature specs
  - DeepSeek can participate but still frequently violates schema on training/model specs
  - OpenAI can produce correct structured specs when available, but if `OPENAI_API_KEY` is absent from the active shell/session it cannot serve as the repair tier
- After the latest train-override canonicalization pass, a model-route smoke workspace showed all three candidate artifacts (`feature_pack`, `train_override`, `generated_model`) succeeding on the local Ollama tier without needing OpenAI fallback.
- Local Ollama remains the least reliable tier operationally:
  - the new cooldown/healthcheck path prevents repeated long stalls, but it does not make the local daemon fast
  - if the Ollama daemon is up but overloaded, the system now fails fast and escalates instead of waiting out repeated long timeouts

## Documentation Maintenance Rule
- Stable truth belongs here.
- Historical entries belong in `CODEX_DEV_UPDATES.md`.
- Search/index shortcuts belong in `CODEX_DEV_LOG_INDEX.md`.
- Every material change must refresh all three files in one turn.
- Each change entry must have:
  - entry id
  - local timestamp
  - type
  - scope
  - touched paths
  - summary
  - impact
  - validation
  - compatibility
  - rollback guidance when practical
