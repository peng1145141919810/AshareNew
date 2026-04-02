using Ashare.RuntimeSkeleton.Clock;
using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Execution;
using Ashare.RuntimeSkeleton.Governance;
using Ashare.RuntimeSkeleton.Oms;
using Ashare.RuntimeSkeleton.Pathing;
using Ashare.RuntimeSkeleton.PythonBridge;
using Ashare.RuntimeSkeleton.Safety;
using System.Text.Json;
using System.Text.RegularExpressions;

var command = args.Length > 0 ? args[0].Trim().ToLowerInvariant() : "help";
var workspaceRoot = args.Length > 1 ? args[1] : @"F:\quant_data\AshareC#";

var registry = PathRegistry.Create(workspaceRoot);
var loader = new ManifestDocumentLoader();
var manifest = loader.LoadSystemManifest(registry.ManifestPath);
var runtimes = new PythonRuntimeLocator().Locate(manifest);
var commandFactory = new PythonCommandFactory();

var releaseService = new ReleaseContractService();
var desiredService = new DesiredStateService(releaseService);
var omsFacade = new OmsStateFacade();
var gapService = new GapReportService(desiredService, omsFacade);
var aggregator = new RuntimeStateAggregator();
var gateEvaluator = new RuntimeGateEvaluator();
var resultWriter = new RuntimeResultWriter();
var manifestWriter = new RuntimeRunManifestWriter();
var omsLifecycleService = new OmsLifecycleService(desiredService, omsFacade, gapService, resultWriter);
var orchestrator = new PhaseOrchestrator(
    aggregator,
    gateEvaluator,
    gapService,
    resultWriter,
    manifestWriter,
    new ExecutionBackendService(),
    omsLifecycleService,
    new ShadowExecutionGuardService());
var tickSelector = new TickPhaseSelector();
var tickService = new SchedulerTickService(aggregator, tickSelector, orchestrator, resultWriter, manifestWriter);
var hostService = new SchedulerHostService(aggregator, tickService, resultWriter, manifestWriter);
var parityService = new ParityCheckService();

switch (command)
{
    case "status":
    {
        var state = aggregator.Build(registry);
        var gate = gateEvaluator.Evaluate(state);
        Console.WriteLine("Runtime Status");
        Console.WriteLine($"data_root: {registry.ExternalDataRoot}");
        Console.WriteLine($"data_fallback: {registry.UsesLegacyDataFallback}");
        Console.WriteLine($"release_id: {V(state.ReleaseId)}");
        Console.WriteLine($"trade_date: {V(state.TradeDate)}");
        Console.WriteLine($"safety_mode: {V(state.SafetyMode)}");
        Console.WriteLine($"allow_execution: {state.AllowExecution}");
        Console.WriteLine($"severity: {gate.Severity}");
        foreach (var reason in gate.Reasons.Distinct(StringComparer.OrdinalIgnoreCase))
        {
            Console.WriteLine($"reason: {reason}");
        }

        Console.WriteLine($"next: {gate.RecommendedNextAction}");
        break;
    }
    case "doctor":
    {
        var state = aggregator.Build(registry);
        var gate = gateEvaluator.Evaluate(state);
        Console.WriteLine("Runtime Doctor");
        Console.WriteLine($"can_execute: {gate.CanExecute}");
        Console.WriteLine($"severity: {gate.Severity}");
        Console.WriteLine($"release_pointer: {(state.ReleasePointerExists ? "ok" : "missing")}");
        Console.WriteLine($"release_manifest: {(state.ReleaseManifestExists ? "ok" : "missing")}");
        Console.WriteLine($"clock_state: {(File.Exists(state.ClockStatePath) ? "ok" : "missing")}");
        Console.WriteLine($"safety_state: {(File.Exists(state.SafetyStatePath) ? "ok" : "missing")}");
        Console.WriteLine($"oms_summary: {(state.OmsSummaryExists ? "ok" : "missing")}");
        Console.WriteLine($"actual_state: {(state.ActualStateExists ? "ok" : "missing")}");
        foreach (var reason in gate.Reasons.Distinct(StringComparer.OrdinalIgnoreCase))
        {
            Console.WriteLine($"reason: {reason}");
        }

        Console.WriteLine($"next: {gate.RecommendedNextAction}");
        if (!gate.CanExecute || gate.Severity == GateSeverity.Blocking)
        {
            Environment.ExitCode = 2;
        }

        break;
    }
    case "guarded-run":
    {
        await RunGuarded(args, registry, runtimes, commandFactory, orchestrator, resultWriter, manifestWriter);
        break;
    }
    case "phase-run":
    {
        await RunPhase(args, registry, runtimes, commandFactory, orchestrator);
        break;
    }
    case "scheduler-tick":
    {
        var mode = args.Length > 2 ? args[2] : "auto";
        var extra = SliceArgs(args, 3);
        var tick = await tickService.RunAsync(registry, runtimes, commandFactory, mode, extra);
        Console.WriteLine("Scheduler Tick");
        Console.WriteLine($"mode: {mode}");
        Console.WriteLine($"selected_phase: {ToPhaseName(tick.SelectedPhase)}");
        Console.WriteLine($"final: {tick.FinalStatus}");
        if (tick.ExitCode != 0)
        {
            Environment.ExitCode = tick.ExitCode;
        }
        break;
    }
    case "scheduler-host":
    case "automation-host":
    {
        var mode = GetOption(args, "--mode") ?? (args.Length > 2 ? args[2] : "auto");
        var loop = HasFlag(args, "--loop");
        var maxTicks = ParseIntOption(args, "--max-ticks", 1);
        var intervalSeconds = ParseIntOption(args, "--interval-seconds", 10);
        var extra = RemoveControlOptions(SliceArgs(args, args.Length > 2 && !args[2].StartsWith("--") ? 3 : 2));

        var code = loop
            ? await hostService.RunLoopAsync(registry, runtimes, commandFactory, mode, maxTicks, intervalSeconds, extra)
            : await hostService.RunAsync(registry, runtimes, commandFactory, mode, extra);

        Console.WriteLine("Scheduler Host");
        Console.WriteLine($"mode: {mode}");
        Console.WriteLine($"loop: {loop}");
        Console.WriteLine($"exit: {code}");
        if (code != 0)
        {
            Environment.ExitCode = code;
        }
        break;
    }
    case "clock-host":
    {
        var mode = args.Length > 2 ? args[2] : "auto";
        var code = await hostService.RunAsync(registry, runtimes, commandFactory, mode, SliceArgs(args, 3));
        Console.WriteLine("Clock Host");
        Console.WriteLine($"delegated_scheduler_mode: {mode}");
        Console.WriteLine($"exit: {code}");
        if (code != 0)
        {
            Environment.ExitCode = code;
        }
        break;
    }
    case "gap-report":
    case "reconcile":
    {
        var gap = gapService.Build(registry);
        var payload = new
        {
            timestamp = DateTimeOffset.Now.ToString("O"),
            has_desired_state = gap.HasDesiredState,
            has_actual_state = gap.HasActualState,
            can_compare = gap.CanCompare,
            desired_symbol_count = gap.DesiredSymbolCount,
            actual_symbol_count = gap.ActualSymbolCount,
            overlap_symbol_count = gap.OverlapSymbolCount,
            symbol_missing_in_actual = gap.SymbolMissingInActual,
            symbol_extra_in_actual = gap.SymbolExtraInActual,
            weight_mismatch_symbols = gap.WeightMismatchSymbols,
            shares_mismatch_symbols = gap.SharesMismatchSymbols,
            weight_mismatch_count = gap.WeightMismatchCount,
            shares_mismatch_count = gap.SharesMismatchCount,
            compare_capabilities = gap.CompareCapabilities,
            weight_compare_available = gap.WeightCompareAvailable,
            shares_compare_available = gap.SharesCompareAvailable,
            threshold_policy = gap.ThresholdPolicy,
            blocking_reasons = gap.BlockingReasons,
            warning_reasons = gap.WarningReasons,
            mismatch_summary = gap.MismatchSummary,
            severity = gap.Severity.ToString(),
            reasons = gap.Reasons,
            summary_text = gap.SummaryText
        };
        resultWriter.WriteGapReport(registry, payload);
        manifestWriter.Write(registry, "gap-report", payload);

        Console.WriteLine("Gap Report");
        Console.WriteLine($"can_compare: {gap.CanCompare}");
        Console.WriteLine($"severity: {gap.Severity}");
        Console.WriteLine($"summary: {gap.SummaryText}");
        foreach (var reason in gap.Reasons.Distinct(StringComparer.OrdinalIgnoreCase))
        {
            Console.WriteLine($"reason: {reason}");
        }

        if (!gap.CanCompare && gap.Severity == GateSeverity.Blocking)
        {
            Environment.ExitCode = 2;
        }

        break;
    }
    case "parity-report":
    {
        var payload = parityService.BuildParityReport(registry);
        var io = RuntimeIoPaths.Build(registry);
        Directory.CreateDirectory(io.RuntimeRoot);
        var path = Path.Combine(io.RuntimeRoot, "parity_report.json");
        File.WriteAllText(path, System.Text.Json.JsonSerializer.Serialize(payload, new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
        manifestWriter.Write(registry, "parity-report", payload);
        Console.WriteLine("Parity Report");
        Console.WriteLine($"path: {path}");
        break;
    }
    case "canonical-run":
    {
        var request = commandFactory.BuildScriptInvocation(
            registry,
            runtimes.ResearchPython,
            registry.LaunchCanonicalPath,
            "CanonicalRun",
            SliceArgs(args, 2));
        var result = await new PythonProcessBridge().InvokeAsync(request);
        Console.WriteLine($"python_exit: {result.ExitCode}");
        if (result.ExitCode != 0)
        {
            Environment.ExitCode = result.ExitCode;
        }
        break;
    }
    case "clock-run":
    {
        var request = commandFactory.BuildScriptInvocation(
            registry,
            runtimes.ResearchPython,
            registry.TradeClockServicePath,
            "ClockRun",
            SliceArgs(args, 2));
        var result = await new PythonProcessBridge().InvokeAsync(request);
        Console.WriteLine($"python_exit: {result.ExitCode}");
        if (result.ExitCode != 0)
        {
            Environment.ExitCode = result.ExitCode;
        }
        break;
    }
    case "paths":
    {
        Console.WriteLine("Path Registry");
        Console.WriteLine($"workspace_root: {registry.Policy.WorkspaceRoot}");
        Console.WriteLine($"external_data_root: {registry.ExternalDataRoot}");
        Console.WriteLine($"legacy_data_root: {registry.LegacyDataRoot}");
        Console.WriteLine($"uses_legacy_fallback: {registry.UsesLegacyDataFallback}");
        Console.WriteLine($"launch_canonical_path: {registry.LaunchCanonicalPath}");
        Console.WriteLine($"trade_clock_service_path: {registry.TradeClockServicePath}");
        Console.WriteLine($"affordable_data_bundle_script_path: {registry.AffordableDataBundleScriptPath}");
        Console.WriteLine($"live_price_snapshot_path: {registry.LivePriceSnapshotPath}");
        Console.WriteLine($"integrated_thesis_root: {registry.IntegratedThesisRoot}");
        Console.WriteLine($"intraday_state_root: {registry.IntradayStateRoot}");
        Console.WriteLine($"intraday_phase_state_path: {registry.IntradayPhaseStatePath}");
        Console.WriteLine($"intraday_symbol_state_path: {registry.IntradaySymbolStatePath}");
        Console.WriteLine($"intraday_intent_state_path: {registry.IntradayIntentStatePath}");
        Console.WriteLine($"intraday_event_log_path: {registry.IntradayEventLogPath}");
        Console.WriteLine($"intraday_control_summary_path: {registry.IntradayControlSummaryPath}");
        Console.WriteLine($"clock_state_path: {registry.ClockStatePath}");
        Console.WriteLine($"safety_state_path: {registry.SafetyStatePath}");
        Console.WriteLine($"research_sql_store_path: {registry.ResearchSqlStorePath}");
        Console.WriteLine($"affordable_sql_store_path: {registry.AffordableSqlStorePath}");
        Console.WriteLine($"affordable_snapshot_root: {registry.AffordableSnapshotRoot}");
        Console.WriteLine($"position_ledger_latest_path: {registry.PositionLedgerLatestPath}");
        Console.WriteLine($"mechanism_realism_rollup_path: {registry.MechanismRealismRollupPath}");
        Console.WriteLine($"latest_t_audit_json_path: {registry.LatestTAuditJsonPath}");
        Console.WriteLine($"latest_t_audit_window_csv_path: {registry.LatestTAuditWindowCsvPath}");
        Console.WriteLine($"site_publish_root: {registry.SitePublishRoot}");
        Console.WriteLine($"audit_reports_root: {registry.AuditReportsRoot}");
        Console.WriteLine($"operator_runtime_context_path: {registry.OperatorRuntimeContextPath}");
        break;
    }
    case "runtime-profile":
    case "profile":
    {
        PrintRuntimeProfile(registry, loader);
        break;
    }
    case "audit-status":
    {
        PrintAuditStatus(registry);
        break;
    }
    case "site-status":
    {
        PrintSiteStatus(registry);
        break;
    }
    case "authority":
    {
        Console.WriteLine("Authority Boundaries");
        foreach (var role in AuthorityBoundaries.Default)
        {
            Console.WriteLine($"- {role.RoleName}");
        }
        break;
    }
    case "schedule":
    {
        Console.WriteLine("Trade Clock Schedule");
        foreach (var phase in TradeClockSchedule.DefaultPhases)
        {
            Console.WriteLine($"- {phase.Name} @ {phase.ScheduledTime}");
        }
        break;
    }
    case "execution-plan":
    {
        var plan = new ExecutionCoordinator(
            new SafetyGateEvaluator(),
            new TradeClockPlanner(),
            new PythonCommandFactory()).BuildPlan(
            registry,
            runtimes,
            new ReleaseReference
            {
                ReleaseId = "skeleton_release",
                TradeDate = DateOnly.FromDateTime(DateTime.Today).ToString("yyyy-MM-dd"),
                Profile = "daily_production",
                SourceMode = "release_only",
                ManifestPath = Path.Combine(registry.ExternalTradeReleaseRoot, "latest_release.json"),
                TargetPositionsPath = Path.Combine(registry.ExternalTradeReleaseRoot, "target_positions.csv")
            },
            profile: "daily_production",
            gateAllowsExecution: true,
            precisionTradeEnabled: false,
            staleAccountTruth: false,
            hasUnfinishedOrders: false,
            allowUnfinishedOrdersReconcile: false);
        Console.WriteLine("Execution Plan");
        Console.WriteLine($"allow_execution: {plan.Safety.AllowExecution}");
        Console.WriteLine($"system_mode: {plan.Safety.SystemMode}");
        break;
    }
    default:
        PrintHelp();
        break;
}

return;

static async Task RunPhase(
    string[] args,
    PathRegistry registry,
    PythonRuntimeSelection runtimes,
    PythonCommandFactory commandFactory,
    PhaseOrchestrator orchestrator)
{
    var phaseText = args.Length > 2 ? args[2] : string.Empty;
    var phase = ParsePhase(phaseText);
    if (phase == RuntimePhase.None)
    {
        Console.WriteLine("Phase Run");
        Console.WriteLine("phase: invalid");
        Environment.ExitCode = 2;
        return;
    }

    var result = await orchestrator.RunAsync(registry, runtimes, commandFactory, phase, SliceArgs(args, 3));
    PrintPhaseResult(result);
}

static async Task RunGuarded(
    string[] args,
    PathRegistry registry,
    PythonRuntimeSelection runtimes,
    PythonCommandFactory commandFactory,
    PhaseOrchestrator orchestrator,
    RuntimeResultWriter resultWriter,
    RuntimeRunManifestWriter manifestWriter)
{
    var mode = args.Length > 2 ? args[2] : string.Empty;
    RuntimePhase phase = mode switch
    {
        "research_only" => RuntimePhase.Research,
        "release_only" => RuntimePhase.Release,
        "execution_only" => RuntimePhase.Execution,
        _ => RuntimePhase.None
    };

    if (phase == RuntimePhase.None)
    {
        var payload = new
        {
            timestamp = DateTimeOffset.Now.ToString("O"),
            requested_mode = mode,
            can_run = false,
            severity = GateSeverity.Blocking.ToString(),
            reasons = new[] { "unsupported_mode" },
            recommended_next_action = "Use research_only, release_only, or execution_only.",
            python_command_preview = string.Empty,
            launched = false,
            final_status = "blocked"
        };
        resultWriter.WriteGuarded(registry, payload);
        manifestWriter.Write(registry, "guarded-run", payload);
        Console.WriteLine("Guarded Run");
        Console.WriteLine("mode: invalid");
        Console.WriteLine("launch: blocked");
        Environment.ExitCode = 2;
        return;
    }

    var result = await orchestrator.RunAsync(registry, runtimes, commandFactory, phase, SliceArgs(args, 3));
    var guardedPayload = new
    {
        timestamp = DateTimeOffset.Now.ToString("O"),
        requested_mode = mode,
        can_run = result.CanRun,
        severity = result.Severity.ToString(),
        reasons = result.Reasons,
        recommended_next_action = result.RecommendedNextAction,
        python_command_preview = result.PythonCommandPreview,
        backend_selected = result.BackendSelected,
        backend_executor_type = result.BackendExecutorType,
        control_plane_owner = result.ControlPlaneOwner,
        authority_owner = result.AuthorityOwner,
        adapter_used = result.AdapterUsed,
        failure_classification = result.FailureClassification,
        launched_by_control_plane = result.LaunchedByControlPlane,
        submit_disabled = result.SubmitDisabled,
        broker_isolated = result.BrokerIsolated,
        launched = result.Launched,
        python_exit_code = result.PythonExitCode,
        final_status = result.FinalStatus,
        gap_report_available = result.Gap is not null,
        gap_can_compare = result.Gap?.CanCompare,
        gap_severity = result.Gap?.Severity.ToString(),
        gap_summary = result.Gap?.SummaryText,
        gap_reasons = result.Gap?.Reasons ?? [],
        symbol_missing_in_actual = result.Gap?.SymbolMissingInActual ?? [],
        symbol_extra_in_actual = result.Gap?.SymbolExtraInActual ?? [],
        weight_mismatch_symbols = result.Gap?.WeightMismatchSymbols ?? [],
        shares_mismatch_symbols = result.Gap?.SharesMismatchSymbols ?? [],
        weight_mismatch_count = result.Gap?.WeightMismatchCount,
        shares_mismatch_count = result.Gap?.SharesMismatchCount,
        compare_capabilities = result.Gap?.CompareCapabilities,
        threshold_policy = result.Gap?.ThresholdPolicy,
        blocking_reasons = result.Gap?.BlockingReasons ?? [],
        warning_reasons = result.Gap?.WarningReasons ?? []
    };
    resultWriter.WriteGuarded(registry, guardedPayload);
    manifestWriter.Write(registry, "guarded-run", guardedPayload);

    Console.WriteLine("Guarded Run");
    Console.WriteLine($"mode: {mode}");
    Console.WriteLine($"can_run: {result.CanRun}");
    Console.WriteLine($"severity: {result.Severity}");
    Console.WriteLine($"launched: {result.Launched}");
    Console.WriteLine($"final: {result.FinalStatus}");
    foreach (var reason in result.Reasons.Distinct(StringComparer.OrdinalIgnoreCase))
    {
        Console.WriteLine($"reason: {reason}");
    }
    Console.WriteLine($"next: {result.RecommendedNextAction}");

    if (result.FinalStatus == "blocked")
    {
        Environment.ExitCode = 2;
    }
    else if (result.FinalStatus == "failed")
    {
        Environment.ExitCode = result.PythonExitCode ?? 1;
    }
}

static void PrintPhaseResult(PhaseRunResult result)
{
    Console.WriteLine("Phase Run");
    Console.WriteLine($"phase: {ToPhaseName(result.Phase)}");
    Console.WriteLine($"mode: {result.MappedMode}");
    Console.WriteLine($"backend: {result.BackendSelected}");
    Console.WriteLine($"executor: {result.BackendExecutorType}");
    Console.WriteLine($"control_plane_owner: {result.ControlPlaneOwner}");
    Console.WriteLine($"authority_owner: {result.AuthorityOwner}");
    Console.WriteLine($"adapter_used: {result.AdapterUsed}");
    Console.WriteLine($"failure_classification: {result.FailureClassification}");
    Console.WriteLine($"launched_by_control_plane: {result.LaunchedByControlPlane}");
    Console.WriteLine($"submit_disabled: {result.SubmitDisabled}");
    Console.WriteLine($"broker_isolated: {result.BrokerIsolated}");
    Console.WriteLine($"gate: {result.Severity}");
    Console.WriteLine($"launch: {(result.Launched ? "started" : "blocked")}");
    Console.WriteLine($"final: {result.FinalStatus}");
    if (result.PythonExitCode.HasValue)
    {
        Console.WriteLine($"python_exit: {result.PythonExitCode}");
    }
    foreach (var reason in result.Reasons.Distinct(StringComparer.OrdinalIgnoreCase))
    {
        Console.WriteLine($"reason: {reason}");
    }
    Console.WriteLine($"next: {result.RecommendedNextAction}");

    if (result.FinalStatus == "blocked")
    {
        Environment.ExitCode = 2;
    }
    else if (result.FinalStatus == "failed")
    {
        Environment.ExitCode = result.PythonExitCode ?? 1;
    }
}

static RuntimePhase ParsePhase(string phase)
{
    return phase.ToLowerInvariant() switch
    {
        "research" => RuntimePhase.Research,
        "release" => RuntimePhase.Release,
        "preopen_gate" => RuntimePhase.PreopenGate,
        "simulation" => RuntimePhase.Simulation,
        "midday_review" => RuntimePhase.MiddayReview,
        "afternoon_execution" => RuntimePhase.AfternoonExecution,
        "afternoon_shadow" => RuntimePhase.AfternoonShadow,
        "summary" => RuntimePhase.Summary,
        "execution" => RuntimePhase.Execution,
        _ => RuntimePhase.None
    };
}

static string ToPhaseName(RuntimePhase phase)
{
    return phase switch
    {
        RuntimePhase.PreopenGate => "preopen_gate",
        RuntimePhase.MiddayReview => "midday_review",
        RuntimePhase.AfternoonExecution => "afternoon_execution",
        RuntimePhase.AfternoonShadow => "afternoon_shadow",
        _ => phase.ToString().ToLowerInvariant()
    };
}

static string V(string v) => string.IsNullOrWhiteSpace(v) ? "unknown" : v;

static IReadOnlyList<string> SliceArgs(string[] fullArgs, int start)
{
    if (fullArgs.Length <= start)
    {
        return [];
    }

    return fullArgs.Skip(start).ToArray();
}

static bool HasFlag(string[] args, string flag)
{
    return args.Any(x => string.Equals(x, flag, StringComparison.OrdinalIgnoreCase));
}

static string? GetOption(string[] args, string key)
{
    for (var i = 0; i < args.Length - 1; i++)
    {
        if (string.Equals(args[i], key, StringComparison.OrdinalIgnoreCase))
        {
            return args[i + 1];
        }
    }

    return null;
}

static int ParseIntOption(string[] args, string key, int fallback)
{
    var value = GetOption(args, key);
    return int.TryParse(value, out var parsed) ? parsed : fallback;
}

static IReadOnlyList<string> RemoveControlOptions(IReadOnlyList<string> args)
{
    var output = new List<string>();
    for (var i = 0; i < args.Count; i++)
    {
        var token = args[i];
        if (string.Equals(token, "--loop", StringComparison.OrdinalIgnoreCase))
        {
            continue;
        }
        if (string.Equals(token, "--mode", StringComparison.OrdinalIgnoreCase)
            || string.Equals(token, "--max-ticks", StringComparison.OrdinalIgnoreCase)
            || string.Equals(token, "--interval-seconds", StringComparison.OrdinalIgnoreCase))
        {
            i++;
            continue;
        }

        output.Add(token);
    }

    return output;
}

static void PrintHelp()
{
    Console.WriteLine("Usage:");
    Console.WriteLine("  status [workspaceRoot]");
    Console.WriteLine("  doctor [workspaceRoot]");
    Console.WriteLine("  guarded-run [workspaceRoot] [research_only|release_only|execution_only] [args...]");
    Console.WriteLine("  phase-run [workspaceRoot] [research|release|preopen_gate|simulation|midday_review|afternoon_execution|afternoon_shadow|summary|execution] [args...]");
    Console.WriteLine("  scheduler-tick [workspaceRoot] [auto|research|release|preopen_gate|simulation|midday_review|afternoon_execution|afternoon_shadow|summary|execution] [args...]");
    Console.WriteLine("  scheduler-host [workspaceRoot] [mode] [--loop] [--max-ticks N] [--interval-seconds N] [args...]");
    Console.WriteLine("  automation-host [workspaceRoot] [mode] [--loop] [--max-ticks N] [--interval-seconds N] [args...]");
    Console.WriteLine("  clock-host [workspaceRoot] [mode] [args...]");
    Console.WriteLine("  gap-report [workspaceRoot]");
    Console.WriteLine("  parity-report [workspaceRoot]");
    Console.WriteLine("  reconcile [workspaceRoot]");
    Console.WriteLine("  canonical-run [workspaceRoot] [args...]");
    Console.WriteLine("  clock-run [workspaceRoot] [args...]");
    Console.WriteLine("  paths [workspaceRoot]");
    Console.WriteLine("  runtime-profile [workspaceRoot]");
    Console.WriteLine("  audit-status [workspaceRoot]");
    Console.WriteLine("  site-status [workspaceRoot]");
    Console.WriteLine("  authority");
    Console.WriteLine("  schedule");
    Console.WriteLine("  execution-plan [workspaceRoot]");
}

static void PrintRuntimeProfile(PathRegistry registry, ManifestDocumentLoader loader)
{
    var profiles = loader.LoadRunProfiles(registry.RunProfilesPath);
    var clockJson = ReadJsonObject(registry.ClockStatePath);
    if (clockJson.ValueKind == JsonValueKind.Undefined)
    {
        clockJson = ReadJsonObject(Path.Combine(registry.ExternalTradeClockRoot, "clock_state.json"));
    }

    var schedulerProfile = GetJsonString(clockJson, "scheduler_profile");
    var runtime = GetJsonObject(clockJson, "runtime");
    var serviceProfile = GetJsonString(runtime, "service_profile");
    var configPath = GetJsonString(runtime, "config_path");

    var effectiveProfile = FirstNonEmpty(serviceProfile, schedulerProfile, profiles.DefaultProfile);
    var runtimeConfig = ReadJsonObject(configPath);
    var execution = GetJsonObject(runtimeConfig, "execution");
    var supervisor = GetJsonObject(runtimeConfig, "supervisor");
    var executionCycles = GetJsonInt(execution, "max_cycles");
    var v5Cycles = GetJsonInt(supervisor, "v5_gpu_max_cycles_per_tick");

    Console.WriteLine("Runtime Profile");
    Console.WriteLine($"clock_state_path: {registry.ClockStatePath}");
    Console.WriteLine($"scheduler_profile: {V(schedulerProfile)}");
    Console.WriteLine($"service_profile: {V(serviceProfile)}");
    Console.WriteLine($"effective_profile: {V(effectiveProfile)}");
    Console.WriteLine($"runtime_config_path: {V(configPath)}");
    Console.WriteLine($"v5_gpu_max_cycles_per_tick: {v5Cycles?.ToString() ?? "unknown"}");
    Console.WriteLine($"execution_max_cycles: {executionCycles?.ToString() ?? "unknown"}");
    Console.WriteLine("note: execution_max_cycles is not the V5/XGBoost research-depth control.");

    if (!string.IsNullOrWhiteSpace(effectiveProfile)
        && profiles.AllowedProfiles.TryGetValue(effectiveProfile, out var definition))
    {
        Console.WriteLine($"run_profile_v5_cycles: {definition.V5Cycles}");
        Console.WriteLine($"run_profile_operator_use: {definition.OperatorUse}");
    }
}

static void PrintAuditStatus(PathRegistry registry)
{
    Console.WriteLine("Audit Status");
    Console.WriteLine($"site_publish_root: {registry.SitePublishRoot}");
    Console.WriteLine($"audit_reports_root: {registry.AuditReportsRoot}");
    Console.WriteLine($"operator_runtime_context: {(File.Exists(registry.OperatorRuntimeContextPath) ? "ok" : "missing")}");
    Console.WriteLine($"position_ledger_latest: {(File.Exists(registry.PositionLedgerLatestPath) ? "ok" : "missing")}");
    Console.WriteLine($"mechanism_realism_rollup: {(File.Exists(registry.MechanismRealismRollupPath) ? "ok" : "missing")}");
    Console.WriteLine($"latest_t_audit_json: {(File.Exists(registry.LatestTAuditJsonPath) ? "ok" : "missing")}");
    Console.WriteLine($"latest_t_audit_window_csv: {(File.Exists(registry.LatestTAuditWindowCsvPath) ? "ok" : "missing")}");

    if (!Directory.Exists(registry.AuditReportsRoot))
    {
        Console.WriteLine("latest_report: missing");
        return;
    }

    var latestJson = Directory
        .EnumerateFiles(registry.AuditReportsRoot, "strategy_audit.json", SearchOption.AllDirectories)
        .Select(path => new FileInfo(path))
        .OrderByDescending(info => info.LastWriteTimeUtc)
        .FirstOrDefault();

    if (latestJson is null)
    {
        Console.WriteLine("latest_report: missing");
        return;
    }

    Console.WriteLine($"latest_report_json: {latestJson.FullName}");
    var htmlPath = Path.Combine(latestJson.DirectoryName ?? string.Empty, "strategy_audit.html");
    Console.WriteLine($"latest_report_html: {(File.Exists(htmlPath) ? htmlPath : "missing")}");

    var auditJson = ReadJsonObject(latestJson.FullName);
    PrintAuditSectionAvailability(auditJson, "pnl_source_analysis");
    PrintAuditSectionAvailability(auditJson, "mechanism_realism_analysis");
    PrintAuditSectionAvailability(auditJson, "execution_flow_analysis");
    PrintAuditSectionAvailability(auditJson, "realized_pnl_analysis");
    PrintAuditSectionAvailability(auditJson, "t_overlay_analysis");
}

static void PrintSiteStatus(PathRegistry registry)
{
    Console.WriteLine("Site Status");
    Console.WriteLine($"site_publish_root: {registry.SitePublishRoot}");
    Console.WriteLine($"site_publish_root_exists: {Directory.Exists(registry.SitePublishRoot)}");

    var siteStatePath = Path.Combine(registry.SitePublishRoot, "site_state.json");
    var siteState = ReadJsonObject(siteStatePath);
    var runtimeContext = ReadJsonObject(registry.OperatorRuntimeContextPath);

    Console.WriteLine($"site_state_path: {siteStatePath}");
    Console.WriteLine($"site_state_exists: {File.Exists(siteStatePath)}");
    Console.WriteLine($"operator_runtime_context_exists: {File.Exists(registry.OperatorRuntimeContextPath)}");
    Console.WriteLine($"latest_t_audit_json_exists: {File.Exists(registry.LatestTAuditJsonPath)}");
    Console.WriteLine($"index_html: {(File.Exists(Path.Combine(registry.SitePublishRoot, "index.html")) ? "ok" : "missing")}");
    Console.WriteLine($"audit_center_html: {(File.Exists(Path.Combine(registry.SitePublishRoot, "audit-center.html")) ? "ok" : "missing")}");
    Console.WriteLine($"operator_console_html: {(File.Exists(Path.Combine(registry.SitePublishRoot, "operator-console.html")) ? "ok" : "missing")}");

    Console.WriteLine($"site_generated_at: {V(GetJsonString(siteState, "generated_at"))}");
    Console.WriteLine($"site_latest_release_id: {V(GetJsonString(siteState, "latest_release_id"))}");
    Console.WriteLine($"site_report_count: {GetJsonInt(siteState, "report_count")?.ToString() ?? "unknown"}");
    Console.WriteLine($"site_target_count: {GetJsonInt(siteState, "target_count")?.ToString() ?? "unknown"}");
    Console.WriteLine($"site_position_count: {GetJsonInt(siteState, "position_count")?.ToString() ?? "unknown"}");

    Console.WriteLine($"runtime_trade_date: {V(GetJsonString(runtimeContext, "trade_date"))}");
    Console.WriteLine($"runtime_clock_phase: {V(GetJsonString(runtimeContext, "clock_phase"))}");
    Console.WriteLine($"runtime_release_id: {V(GetJsonString(runtimeContext, "release_id"))}");
    Console.WriteLine($"runtime_heartbeat_at: {V(GetJsonString(runtimeContext, "heartbeat_at"))}");

    var safety = GetJsonObject(runtimeContext, "safety");
    Console.WriteLine($"runtime_system_mode: {V(GetJsonString(safety, "system_mode"))}");
    Console.WriteLine($"runtime_market_safety_regime: {V(GetJsonString(safety, "market_safety_regime"))}");
    Console.WriteLine($"runtime_gate_open: {GetJsonBool(safety, "gate_open")?.ToString() ?? "unknown"}");
    Console.WriteLine($"runtime_gate_reason: {V(GetJsonString(safety, "gate_reason"))}");

    var tAudit = ReadJsonObject(registry.LatestTAuditJsonPath);
    Console.WriteLine($"t_audit_available: {GetJsonBool(tAudit, "available")?.ToString() ?? "unknown"}");
    Console.WriteLine($"t_audit_top_reject_reason: {V(GetJsonString(tAudit, "top_reject_reason"))}");
    Console.WriteLine($"t_audit_top_suited_mechanism: {V(GetJsonString(tAudit, "top_suited_mechanism"))}");

    if (Directory.Exists(registry.AuditReportsRoot))
    {
        var reportDirs = Directory.GetDirectories(registry.AuditReportsRoot);
        Console.WriteLine($"staged_audit_report_dirs: {reportDirs.Length}");
        var latestReportDir = reportDirs
            .Select(path => new DirectoryInfo(path))
            .OrderByDescending(info => info.LastWriteTimeUtc)
            .FirstOrDefault();
        Console.WriteLine($"latest_audit_report_dir: {latestReportDir?.FullName ?? "missing"}");
    }
    else
    {
        Console.WriteLine("staged_audit_report_dirs: 0");
        Console.WriteLine("latest_audit_report_dir: missing");
    }
}

static void PrintAuditSectionAvailability(JsonElement root, string sectionName)
{
    var section = GetJsonObject(root, sectionName);
    var available = GetJsonBool(section, "available");
    var mode = GetJsonString(section, "mode");
    Console.WriteLine($"{sectionName}: {(available.HasValue ? (available.Value ? "available" : "unavailable") : "unknown")}");
    if (!string.IsNullOrWhiteSpace(mode))
    {
        Console.WriteLine($"{sectionName}_mode: {mode}");
    }
}

static JsonElement ReadJsonObject(string? path)
{
    if (string.IsNullOrWhiteSpace(path) || !File.Exists(path))
    {
        return default;
    }

    try
    {
        var text = File.ReadAllText(path);
        text = SanitizeJson(text);
        using var document = JsonDocument.Parse(text);
        return document.RootElement.Clone();
    }
    catch
    {
        return default;
    }
}

static string SanitizeJson(string text)
{
    if (string.IsNullOrWhiteSpace(text))
    {
        return text;
    }

    return Regex.Replace(text, @"(?<=[:\[,]\s*)(NaN|Infinity|-Infinity)(?=\s*[,}\]])", "null");
}

static JsonElement GetJsonObject(JsonElement element, string propertyName)
{
    return element.ValueKind == JsonValueKind.Object && element.TryGetProperty(propertyName, out var value)
        ? value
        : default;
}

static string GetJsonString(JsonElement element, string propertyName)
{
    if (element.ValueKind != JsonValueKind.Object || !element.TryGetProperty(propertyName, out var value))
    {
        return string.Empty;
    }

    return value.ValueKind == JsonValueKind.String ? value.GetString() ?? string.Empty : string.Empty;
}

static int? GetJsonInt(JsonElement element, string propertyName)
{
    if (element.ValueKind != JsonValueKind.Object || !element.TryGetProperty(propertyName, out var value))
    {
        return null;
    }

    return value.ValueKind == JsonValueKind.Number && value.TryGetInt32(out var parsed) ? parsed : null;
}

static bool? GetJsonBool(JsonElement element, string propertyName)
{
    if (element.ValueKind != JsonValueKind.Object || !element.TryGetProperty(propertyName, out var value))
    {
        return null;
    }

    return value.ValueKind switch
    {
        JsonValueKind.True => true,
        JsonValueKind.False => false,
        _ => null
    };
}

static string FirstNonEmpty(params string[] values)
{
    foreach (var value in values)
    {
        if (!string.IsNullOrWhiteSpace(value))
        {
            return value.Trim();
        }
    }

    return string.Empty;
}
