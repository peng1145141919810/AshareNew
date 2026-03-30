using Ashare.RuntimeSkeleton.Clock;
using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Execution;
using Ashare.RuntimeSkeleton.Governance;
using Ashare.RuntimeSkeleton.Oms;
using Ashare.RuntimeSkeleton.Pathing;
using Ashare.RuntimeSkeleton.PythonBridge;
using Ashare.RuntimeSkeleton.Safety;

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
        Console.WriteLine($"three_strategy_kernel_root: {registry.ThreeStrategyKernelRoot}");
        Console.WriteLine($"intraday_state_root: {registry.IntradayStateRoot}");
        Console.WriteLine($"intraday_phase_state_path: {registry.IntradayPhaseStatePath}");
        Console.WriteLine($"intraday_symbol_state_path: {registry.IntradaySymbolStatePath}");
        Console.WriteLine($"intraday_intent_state_path: {registry.IntradayIntentStatePath}");
        Console.WriteLine($"intraday_event_log_path: {registry.IntradayEventLogPath}");
        Console.WriteLine($"intraday_control_summary_path: {registry.IntradayControlSummaryPath}");
        Console.WriteLine($"affordable_sql_store_path: {registry.AffordableSqlStorePath}");
        Console.WriteLine($"affordable_snapshot_root: {registry.AffordableSnapshotRoot}");
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
    Console.WriteLine("  authority");
    Console.WriteLine("  schedule");
    Console.WriteLine("  execution-plan [workspaceRoot]");
}
