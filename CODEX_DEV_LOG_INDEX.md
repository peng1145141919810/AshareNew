# Codex Dev Log Index

## Read Order
1. `CODEX_DEV_LOG.md`
2. `CODEX_DEV_STABLE.md`
3. `CODEX_DEV_UPDATES.md`

## Stable Retrieval Map
- `Latest Stable Snapshot`: current entrypoints, defaults, runtime roots, and output roots
- `Session Start Checklist`: mandatory first actions before touching code
- `CODEX_SECURE_OPS.md`: SSH, credential, and secret-adjacent operational memory without raw secrets
- `Canonical Runtime Chain`: launcher-to-runtime control flow
- `Canonical Modes And Profiles`: supported profile and mode truth
- `Trade-Clock Truth`: service defaults and preflight behavior
- `Runtime Configuration Surface`: where real config files actually live
- `Artifact Registry`: formal manifests, SQL stores, portal, OMS, and intraday outputs
- `Known Dangerous Operations`: commands that trigger real runtime behavior
- `Known Issues`: known mismatches and stale helper surfaces

## Key Paths
- Secure ops notes: `CODEX_SECURE_OPS.md`
- Launcher: `launch_canonical.py`
- Business root: `main_research_runner.py`
- Trade clock: `trade_clock_service.py`
- Runtime root: `src\ashare`
- Control plane: `ashare_control\control_plane.py`
- Manifest: `SYSTEM_MANIFEST.yaml`
- Profiles: `RUN_PROFILES.yaml`
- Formal run root: `outputs\canonical_runs`
- Site source: `site_portal`
- Site stage: `outputs\site_publish_stage`
- Runtime configs: `src\ashare\configs`

## Current Architecture Anchors
- Candidate orchestration: `src\ashare\engine\candidate_pipeline.py`
- Portfolio construction: `src\ashare\engine\portfolio_construction_pipeline.py`
- Global objective: `src\ashare\engine\global_objective.py`
- Harvest-risk scoring: `src\ashare\engine\harvest_risk.py`
- Strategy activation: `src\ashare\engine\strategy_activation.py`
- Constraint arbitration: `src\ashare\engine\constraint_brain.py`
- EMS policy layer: `src\ashare\engine\execution_ems.py`
- Intraday tactics: `src\ashare\engine\intraday_tactics\`
- Intraday state machine: `src\ashare\engine\intraday_state_machine\`
- Clock supervisor: `src\ashare\engine\clock_supervisor.py`
- OMS: `src\ashare\engine\oms\`
- Market state: `src\ashare\engine\market_state\`
- LLM tracing: `src\ashare\engine\llm_trace.py`

## Update Index
- `CDL-20260410-027`: added centralized global-objective scoring, harvest-risk assessment, and a first-class EMS policy layer with new portfolio/execution audit artifacts
- `CDL-20260410-026`: added Eastmoney as the default intraday minute-bar (`rt_min`) provider with Tushare fallback, wired into the existing intraday proxy pipeline
- `CDL-20260410-025`: fixed same-day `release_only` trade-date selection so midday manual releases stay on today if an afternoon execution window still remains
- `CDL-20260410-024`: fixed OMS execution-report success signaling so bridge/runner no longer default report-shaped JSON payloads to failure when `ok/status` were omitted
- `CDL-20260410-023`: documented that `simulation` is mock matching, `precision` is the default precision-matching paper account, and future real trading should move to QMT / QM
- `CDL-20260410-022`: hardened portfolio recommendation / V2A column handling and verified a bounded research -> release -> simulation execution -> feedback -> plan loop
- `CDL-20260410-021`: V5.1 codegen now uses a single-chain `intent -> spec -> compile` contract inside each provider attempt instead of jumping directly from context to spec
- `CDL-20260410-020`: V5.1 train-override specs now canonicalize common low-cost-tier alias/value drift, sharply reducing unnecessary OpenAI escalation
- `CDL-20260410-019`: local Ollama now uses cached health/cooldown short-circuiting, and V5.1 model specs canonicalize common tree-model aliases before legality checks
- `CDL-20260410-018`: V5.1 codegen now escalates by provider tier (`local_ollama` -> `deepseek` -> `openai`) while legality is still judged locally
- `CDL-20260410-017`: V5.1 candidate codegen now uses structured JSON specs plus deterministic local Python compilation instead of free-form Python emission
- `CDL-20260410-016`: V5.1 generated candidate modules now use bounded traceback-driven self-repair and skip unresolved invalid code as `skip_invalid_codegen`
- `CDL-20260410-015`: fixed 掘金 / Gmtrade bridge import failure by installing `gmtrade` into the configured Python39 interpreter and hardening broker import diagnostics
- `CDL-20260410-014`: fix integrated-thesis `integrated_thesis_daily.csv` trade_date str/int mix breaking `sort_values`
- `CDL-20260410-013`: `PYTHON_EXECUTABLE` -> workspace `.venv` (full 3.14 stack), not bare `Python314` install
- `CDL-20260410-012`: Python 3.14 vs 3.9 interpreter split in local settings example, SQLite WAL/busy timeout, single-connection enriched daily sync
- `CDL-20260410-011`: trade-clock autostart script paths, hot-reload default-off, and hot-reload fingerprint hardening for long-lived supervisors
- `CDL-20260410-010`: added `CODEX_SECURE_OPS.md` to preserve SSH and credential workflow memory without storing secrets
- `CDL-20260410-009`: moved OMS lifecycle ledger metadata into `/runtime-state` and finished unifying the major execution-state consumers
- `CDL-20260410-008`: moved desired-state, gap-report, and OMS lifecycle consumers onto the same runtime query layer
- `CDL-20260410-007`: expanded `/runtime-state` to cover release, clock, safety, and OMS so status aggregation can query nearly the full authority set over RPC
- `CDL-20260410-006`: added `/runtime-state` RPC and made control-plane status queries prefer RPC with visible transport reporting
- `CDL-20260410-005`: introduced `RuntimeStateQueryService` so C# runtime aggregation reads through one authority layer instead of scattering file reads
- `CDL-20260410-004`: fixed Operator CLI workspace-root parsing and verified canonical RPC smoke path with `rpc_used: True`
- `CDL-20260410-003`: introduced local loopback RPC for C# -> Python active invocation with direct-process fallback
- `CDL-20260410-002`: moved strategy-activation magic numbers into runtime config and summary weight snapshots
- `CDL-20260410-001`: split dev log into stable/history/index, rewrote primary readmes and operator guide, updated doc sync tooling

## Retrieval Hints
- Search `CDL-20260410-027` in `CODEX_DEV_UPDATES.md` for the new `Outcome/Evidence/Diversity/Execution/Adversarial` objective contract, EMS posture artifact, and harvest-risk integration points.
- Search `global_objective_snapshot.json` in `portfolio_recommendation.py` for where recommendation runs now persist the centralized objective view.
- Search `execution_management_decision.json` in `execution_manager.py` for the new EMS artifact path under `data\trade_clock\ems\...`.
- Search `CDL-20260410-026` in `CODEX_DEV_UPDATES.md` for the Eastmoney minute-bar integration and the new `INTRADAY_RT_MIN_PROVIDER` settings.
- Search `eastmoney.rt_min` in `intraday_proxy_store.py` for where the new provider is attached to the existing `rt_min` snapshot path.
- Search `CDL-20260410-025` in `CODEX_DEV_UPDATES.md` for the release trade-date fix that keeps midday manual releases on the current trading day when a later execution window still exists.
- Search `same_day_with_remaining_execution_window` in `portfolio_release.py` for the current release-date gating rule.
- Search `CDL-20260410-024` in `CODEX_DEV_UPDATES.md` for the execution-report contract fix that adds explicit `ok/status` at the OMS source and compatibility inference in the bridge parser.
- Search `execution_report_*.json` and `ok / status` in `CODEX_DEV_STABLE.md` for the current execution-report truth contract.
- Search `CDL-20260410-023` in `CODEX_DEV_UPDATES.md` for the operational distinction between `simulation` and `precision` and the confirmation that quick-test defaults already point at the precision paper account.
- Search `selected_account_mode=precision` in the latest update entry for the direct runtime-config-generation proof that `execution_bridge_runner` maps the default policy to `account_profiles.precision`.
- Search `future live trading is intended to use QMT / QM` in `CODEX_DEV_STABLE.md` for the current broker-platform boundary.
- Search `CDL-20260410-022` in `CODEX_DEV_UPDATES.md` for the end-to-end canonical smoke that proved `research_meta_feedback_latest.json` is reloaded by `plan_only` after simulation execution.
- Search `_series(frame, "is_existing_position"` in `portfolio\runtime.py`, `portfolio\lifecycle_engine.py`, and `portfolio\admission_engine.py` for the missing-column hardening that fixed the portfolio recommendation crash chain.
- Search `execution_report_20260410_145514.json` for the verified simulation execution artifact set and the `reduce_only` scheduler verdict.
- Search `execution_only can still return process exit code 2` in `CODEX_DEV_STABLE.md` for the current mismatch between simulation artifact emission and runner exit code semantics.
- Search `CDL-20260410-021` in `CODEX_DEV_UPDATES.md` for the new single-chain `intent -> spec` contract that preserves higher-level model ideas without adding sidecar pipelines.
- Search `selected_intent` in `codegen.py` or `workspace_validation.json` for where the intermediate research intent is now retained.
- Search `CDL-20260410-020` in `CODEX_DEV_UPDATES.md` for the train-override canonicalization that maps `balanced` / `uniform`, ratio `feature_cap`, and pair-style quantiles into legal local values.
- Search `TRAIN_OVERRIDE_VALUE_ALIASES` in `codegen.py` for the new low-cost-tier normalization path.
- Search `CDL-20260410-019` in `CODEX_DEV_UPDATES.md` for the local Ollama cooldown guardrails and the V5.1 tree-model alias canonicalization.
- Search `service_cooldown` in `llm_router.py` for the new fast-fail path after recent local Ollama timeout/unreachable states.
- Search `min_child_weight` in `codegen.py` for the new generated-model family correction and alias mapping logic.
- Search `CDL-20260410-018` in `CODEX_DEV_UPDATES.md` for the new cost-aware provider-tier escalation and local legality gate for V5.1 codegen.
- Search `provider_tiers` in the V5.1 config files for the explicit local/deepseek/openai ordering and attempt controls.
- Search `CDL-20260410-017` in `CODEX_DEV_UPDATES.md` for the structured-spec compiler architecture that replaced free-form Python candidate generation.
- Search `feature_pack.spec.json` in `CODEX_DEV_STABLE.md` for the current candidate-lab artifact layout and validation flow.
- Search `CDL-20260410-016` in `CODEX_DEV_UPDATES.md` for the V5.1 candidate codegen fix that adds traceback-driven repair attempts and skips unresolved invalid generated modules before training.
- Search `skip_invalid_codegen` in `CODEX_DEV_STABLE.md` for the new training-time gate that isolates bad generated candidates instead of crashing the full V5.1 batch.
- Search `CDL-20260410-015` in `CODEX_DEV_UPDATES.md` for the 掘金 / Gmtrade outage caused by missing `gmtrade` in `GMTRADE_PYTHON_EXECUTABLE` and the broker import hardening.
- Search `CDL-20260410-014` in `CODEX_DEV_UPDATES.md` for integrated-thesis daily CSV trade_date normalization.
- Search `CDL-20260410-013` in `CODEX_DEV_UPDATES.md` for PYTHON_EXECUTABLE pointing at `.venv` vs bare Python314.
- Search `CDL-20260410-012` in `CODEX_DEV_UPDATES.md` for PYTHON_EXECUTABLE 3.14 vs GMTRADE 3.9 and enriched-daily SQLite locking fixes.
- Search `CDL-20260410-011` in `CODEX_DEV_UPDATES.md` for trade-clock autostart path fixes and hot-reload stability defaults.
- Search `CODEX_SECURE_OPS.md` in `CODEX_DEV_STABLE.md` for the new secret-adjacent ops pointer.
- Search `CDL-20260410-010` in `CODEX_DEV_UPDATES.md` for the secure-ops document split.
- Search `intent_ledger_latest.csv` in `CODEX_DEV_STABLE.md` for the final `/runtime-state` bundle contents.
- Search `CDL-20260410-009` in `CODEX_DEV_UPDATES.md` for the OMS lifecycle ledger unification.
- Search `DesiredStateService` in `CODEX_DEV_STABLE.md` for the note that desired/gap/lifecycle consumers now share the authority layer.
- Search `CDL-20260410-008` in `CODEX_DEV_UPDATES.md` for the final consumer-side unification onto `RuntimeStateQueryService`.
- Search `rpc_runtime_state+file_fallback` in `CODEX_DEV_STABLE.md` for the current full runtime-state transport mode.
- Search `CDL-20260410-007` in `CODEX_DEV_UPDATES.md` for the release/clock/safety/OMS expansion of `/runtime-state`.
- Search `state_query_transport` in `CODEX_DEV_STABLE.md` for the current RPC-vs-file status query mode.
- Search `CDL-20260410-006` in `CODEX_DEV_UPDATES.md` for the `/runtime-state` endpoint and control-plane status RPC change.
- Search `Runtime State Query Layer` in `CODEX_DEV_STABLE.md` for the new authority ordering and query-service boundary.
- Search `CDL-20260410-005` in `CODEX_DEV_UPDATES.md` for the `RuntimeStateAggregator` refactor and validation command.
- Search `--workspace-root` in `CODEX_DEV_STABLE.md` for the corrected Operator CLI passthrough contract.
- Search `CDL-20260410-004` in `CODEX_DEV_UPDATES.md` for the CLI parsing fix and the `rpc_used: True` smoke verification.
- Search `Cross-Language Boundary` in `CODEX_DEV_STABLE.md` for the current RPC-vs-artifact split.
- Search `CDL-20260410-003` in `CODEX_DEV_UPDATES.md` for the C# -> Python RPC transport change.
- Search `strategy activation weights` in `CODEX_DEV_STABLE.md` for the new config-backed activation governance.
- Search `CDL-20260410-002` in `CODEX_DEV_UPDATES.md` for the weight-governance code change.
- Search `trade_clock_service default profile` in `CODEX_DEV_STABLE.md` for the `daily_production` vs `quick_test` distinction.
- Search `hub_v6` in `CODEX_DEV_STABLE.md` for legacy naming debt still present in helper code.
- Search `CDL-20260410-001` in `CODEX_DEV_UPDATES.md` for the documentation restructuring entry.
- Search `Artifact Registry` in `CODEX_DEV_STABLE.md` for formal outputs and SQL store locations.
