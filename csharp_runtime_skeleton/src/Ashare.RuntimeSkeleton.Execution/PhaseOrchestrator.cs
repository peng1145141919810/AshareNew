using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Pathing;
using Ashare.RuntimeSkeleton.PythonBridge;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class PhaseOrchestrator
{
    private readonly RuntimeStateAggregator _aggregator;
    private readonly RuntimeGateEvaluator _gateEvaluator;
    private readonly GapReportService _gapReportService;
    private readonly RuntimeResultWriter _resultWriter;
    private readonly RuntimeRunManifestWriter _manifestWriter;
    private readonly ExecutionBackendService _executionBackendService;
    private readonly OmsLifecycleService _omsLifecycleService;
    private readonly ShadowExecutionGuardService _shadowGuardService;

    public PhaseOrchestrator(
        RuntimeStateAggregator aggregator,
        RuntimeGateEvaluator gateEvaluator,
        GapReportService gapReportService,
        RuntimeResultWriter resultWriter,
        RuntimeRunManifestWriter manifestWriter,
        ExecutionBackendService? executionBackendService = null,
        OmsLifecycleService? omsLifecycleService = null,
        ShadowExecutionGuardService? shadowGuardService = null)
    {
        _aggregator = aggregator;
        _gateEvaluator = gateEvaluator;
        _gapReportService = gapReportService;
        _resultWriter = resultWriter;
        _manifestWriter = manifestWriter;
        _executionBackendService = executionBackendService ?? new ExecutionBackendService();
        _omsLifecycleService = omsLifecycleService ?? new OmsLifecycleService(new DesiredStateService(new ReleaseContractService()), new Ashare.RuntimeSkeleton.Oms.OmsStateFacade(), gapReportService, resultWriter);
        _shadowGuardService = shadowGuardService ?? new ShadowExecutionGuardService();
    }

    public async Task<PhaseRunResult> RunAsync(
        PathRegistry registry,
        PythonRuntimeSelection runtimes,
        PythonCommandFactory commandFactory,
        RuntimePhase phase,
        IReadOnlyList<string> passthroughArgs)
    {
        var start = DateTimeOffset.Now;
        var runId = $"{DateTime.Now:yyyyMMdd_HHmmss}_{ToPhaseName(phase)}";
        var state = _aggregator.Build(registry);
        var gate = _gateEvaluator.Evaluate(state);
        var lifecyclePre = _omsLifecycleService.Capture(registry, "pre_phase");

        if (!PhaseRegistry.TryGet(phase, out var definition))
        {
            var unsupported = BuildBlocked(runId, phase, string.Empty, start, ["phase_not_registered"], "Register phase in PhaseRegistry first.", null, null, lifecyclePre);
            _resultWriter.WritePhaseJournal(registry, unsupported);
            _manifestWriter.Write(registry, "phase-run", new { runId, phase = ToPhaseName(phase), final_status = "blocked", reasons = unsupported.Reasons });
            return unsupported;
        }

        var policy = EvaluatePhasePolicy(phase, gate, registry);
        GapReport? gap = null;
        if (IsExecutionSensitivePhase(phase))
        {
            gap = _gapReportService.Build(registry);
            if (!gap.CanCompare)
            {
                policy = MergePolicy(policy, GateSeverity.Blocking, "execution_gap_compare_unavailable", "Fix desired/actual artifacts before execution phase.");
            }
            else if (gap.Severity == GateSeverity.Blocking)
            {
                policy = MergePolicy(policy, GateSeverity.Blocking, "execution_gap_blocking", "Gap exceeded blocking threshold. Review reconciliation report.");
            }
            else if (gap.Severity == GateSeverity.Warning)
            {
                policy = MergePolicy(policy, GateSeverity.Warning, "execution_gap_warning", "Execution allowed with mismatch warnings.");
            }
        }

        var args = new List<string> { "--mode", definition.CanonicalMode };
        args.AddRange(definition.FixedArgs);
        args.AddRange(passthroughArgs);

        var shadowGuard = _shadowGuardService.Evaluate(phase, args);
        if (phase == RuntimePhase.AfternoonShadow && !shadowGuard.LaunchAllowed)
        {
            var reasons = policy.Reasons.Concat(shadowGuard.Reasons).Distinct(StringComparer.OrdinalIgnoreCase).ToArray();
            var blockedShadow = BuildBlocked(runId, phase, definition.CanonicalMode, start, reasons, "Shadow guard fail-closed: enforce no-submit and isolated namespace.", null, gap, lifecyclePre, GateSeverity.Blocking, shadowGuard.SubmitDisabled, shadowGuard.BrokerIsolated);
            _resultWriter.WritePhaseJournal(registry, blockedShadow);
            _manifestWriter.Write(registry, "phase-run", new { runId, phase = ToPhaseName(phase), final_status = "blocked", reasons = blockedShadow.Reasons, shadow = true });
            return blockedShadow;
        }

        if (phase == RuntimePhase.Summary)
        {
            var summaryResult = new PhaseRunResult
            {
                RunId = runId,
                Phase = phase,
                MappedMode = definition.CanonicalMode,
                CanRun = true,
                Severity = policy.Severity,
                Reasons = policy.Reasons,
                RecommendedNextAction = "Summary phase completed by control-plane internal audit output.",
                PythonCommandPreview = "summary_internal",
                BackendSelected = "csharp_internal",
                BackendExecutorType = "internal_owner",
                LaunchedByControlPlane = true,
                SubmitDisabled = false,
                BrokerIsolated = false,
                Launched = false,
                PythonExitCode = 0,
                FinalStatus = "succeeded",
                Gap = null,
                TimestampStart = start,
                TimestampEnd = DateTimeOffset.Now
            };
            _omsLifecycleService.Capture(registry, "post_phase_summary");
            _resultWriter.WritePhaseJournal(registry, summaryResult);
            _manifestWriter.Write(registry, "phase-run", new { runId, phase = ToPhaseName(phase), final_status = "succeeded", launched = false, backend = "csharp_internal" });
            return summaryResult;
        }

        var request = commandFactory.BuildScriptInvocation(
            registry,
            runtimes.ResearchPython,
            registry.LaunchCanonicalPath,
            "PhaseOrchestratorRun",
            args);

        if (!policy.CanExecute || policy.Severity == GateSeverity.Blocking)
        {
            var blocked = BuildBlocked(runId, phase, definition.CanonicalMode, start, policy.Reasons, policy.RecommendedNextAction, request, gap, lifecyclePre, policy.Severity, shadowGuard.SubmitDisabled, shadowGuard.BrokerIsolated);
            _resultWriter.WritePhaseJournal(registry, blocked);
            _manifestWriter.Write(registry, "phase-run", new { runId, phase = ToPhaseName(phase), final_status = "blocked", reasons = blocked.Reasons });
            return blocked;
        }

        var backendResult = await _executionBackendService.ExecuteAsync(
            registry,
            runtimes,
            commandFactory,
            phase,
            definition.CanonicalMode,
            args,
            shadowGuard.SubmitDisabled,
            shadowGuard.BrokerIsolated);

        _omsLifecycleService.Capture(registry, "post_phase");

        var output = new PhaseRunResult
        {
            RunId = runId,
            Phase = phase,
            MappedMode = definition.CanonicalMode,
            CanRun = true,
            Severity = policy.Severity,
            Reasons = policy.Reasons.Concat(backendResult.Reasons).Distinct(StringComparer.OrdinalIgnoreCase).ToArray(),
            RecommendedNextAction = policy.RecommendedNextAction,
            PythonCommandPreview = BuildCommandPreview(request),
            BackendSelected = backendResult.BackendSelected,
            BackendExecutorType = backendResult.BackendExecutorType,
            LaunchedByControlPlane = backendResult.LaunchedByControlPlane,
            SubmitDisabled = backendResult.SubmitDisabled,
            BrokerIsolated = backendResult.BrokerIsolated,
            Launched = backendResult.Launched,
            PythonExitCode = backendResult.ExitCode,
            FinalStatus = backendResult.NormalizedFinalStatus,
            Gap = gap,
            TimestampStart = start,
            TimestampEnd = DateTimeOffset.Now
        };

        _resultWriter.WritePhaseJournal(registry, output);
        _manifestWriter.Write(registry, "phase-run", new
        {
            runId,
            phase = ToPhaseName(phase),
            final_status = output.FinalStatus,
            python_exit_code = output.PythonExitCode,
            backend_selected = output.BackendSelected,
            backend_executor_type = output.BackendExecutorType,
            launched_by_control_plane = output.LaunchedByControlPlane,
            submit_disabled = output.SubmitDisabled,
            broker_isolated = output.BrokerIsolated
        });
        return output;
    }

    private static PhaseRunResult BuildBlocked(
        string runId,
        RuntimePhase phase,
        string mode,
        DateTimeOffset start,
        IReadOnlyList<string> reasons,
        string action,
        PythonInvocationRequest? request,
        GapReport? gap,
        OmsLifecycleResult lifecycle,
        GateSeverity? severity = null,
        bool submitDisabled = false,
        bool brokerIsolated = false)
    {
        return new PhaseRunResult
        {
            RunId = runId,
            Phase = phase,
            MappedMode = mode,
            CanRun = false,
            Severity = severity ?? GateSeverity.Blocking,
            Reasons = reasons.Concat(lifecycle.Reasons).Distinct(StringComparer.OrdinalIgnoreCase).ToArray(),
            RecommendedNextAction = action,
            PythonCommandPreview = request is null ? string.Empty : BuildCommandPreview(request),
            BackendSelected = "blocked_before_backend",
            BackendExecutorType = "none",
            LaunchedByControlPlane = true,
            SubmitDisabled = submitDisabled,
            BrokerIsolated = brokerIsolated,
            Launched = false,
            PythonExitCode = null,
            FinalStatus = "blocked",
            Gap = gap,
            TimestampStart = start,
            TimestampEnd = DateTimeOffset.Now
        };
    }

    private static bool IsExecutionSensitivePhase(RuntimePhase phase)
    {
        return phase is RuntimePhase.Execution or RuntimePhase.PreopenGate or RuntimePhase.Simulation or RuntimePhase.AfternoonExecution or RuntimePhase.AfternoonShadow;
    }

    private static string ToPhaseName(RuntimePhase phase)
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

    private static string BuildCommandPreview(PythonInvocationRequest request)
    {
        return string.Join(" ", new[] { request.Command.PreferredPythonPath }.Concat(request.Command.Arguments));
    }

    private static (bool CanExecute, GateSeverity Severity, IReadOnlyList<string> Reasons, string RecommendedNextAction) EvaluatePhasePolicy(
        RuntimePhase phase,
        GateEvaluation baseGate,
        PathRegistry registry)
    {
        if (phase is RuntimePhase.Execution or RuntimePhase.PreopenGate or RuntimePhase.Simulation or RuntimePhase.AfternoonExecution or RuntimePhase.AfternoonShadow)
        {
            return (baseGate.CanExecute, baseGate.Severity, baseGate.Reasons, baseGate.RecommendedNextAction);
        }

        if (phase == RuntimePhase.Release)
        {
            if (baseGate.Severity == GateSeverity.Blocking)
            {
                return (false, baseGate.Severity, baseGate.Reasons, baseGate.RecommendedNextAction);
            }

            return (true, baseGate.Severity, baseGate.Reasons, "Release phase allowed.");
        }

        var reasons = new List<string>();
        if (!File.Exists(registry.LaunchCanonicalPath))
        {
            reasons.Add("launch_canonical_missing");
        }
        if (!File.Exists(registry.ManifestPath))
        {
            reasons.Add("system_manifest_missing");
        }
        if (!File.Exists(registry.RunProfilesPath))
        {
            reasons.Add("run_profiles_missing");
        }

        var ok = reasons.Count == 0;
        return (ok, ok ? GateSeverity.Normal : GateSeverity.Blocking, reasons, ok ? "Phase allowed." : "Fix workspace entry files first.");
    }

    private static (bool CanExecute, GateSeverity Severity, IReadOnlyList<string> Reasons, string RecommendedNextAction) MergePolicy(
        (bool CanExecute, GateSeverity Severity, IReadOnlyList<string> Reasons, string RecommendedNextAction) current,
        GateSeverity severity,
        string reason,
        string action)
    {
        var reasons = current.Reasons.ToList();
        if (!reasons.Contains(reason, StringComparer.OrdinalIgnoreCase))
        {
            reasons.Add(reason);
        }

        var mergedSeverity = (GateSeverity)Math.Max((int)current.Severity, (int)severity);
        var canRun = current.CanExecute && mergedSeverity != GateSeverity.Blocking;

        var nextAction = current.RecommendedNextAction;
        if (current.CanExecute)
        {
            nextAction = action;
        }

        return (canRun, mergedSeverity, reasons, nextAction);
    }
}
