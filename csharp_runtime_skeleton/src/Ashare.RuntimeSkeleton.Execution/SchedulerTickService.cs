using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Pathing;
using Ashare.RuntimeSkeleton.PythonBridge;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class SchedulerTickService
{
    private readonly RuntimeStateAggregator _aggregator;
    private readonly TickPhaseSelector _selector;
    private readonly PhaseOrchestrator _orchestrator;
    private readonly RuntimeResultWriter _resultWriter;
    private readonly RuntimeRunManifestWriter _manifestWriter;

    public SchedulerTickService(
        RuntimeStateAggregator aggregator,
        TickPhaseSelector selector,
        PhaseOrchestrator orchestrator,
        RuntimeResultWriter resultWriter,
        RuntimeRunManifestWriter manifestWriter)
    {
        _aggregator = aggregator;
        _selector = selector;
        _orchestrator = orchestrator;
        _resultWriter = resultWriter;
        _manifestWriter = manifestWriter;
    }

    public async Task<SchedulerTickResult> RunAsync(
        PathRegistry registry,
        PythonRuntimeSelection runtimes,
        PythonCommandFactory commandFactory,
        string mode,
        IReadOnlyList<string> passthroughArgs)
    {
        var state = _aggregator.Build(registry);
        var selection = string.Equals(mode, "auto", StringComparison.OrdinalIgnoreCase)
            ? _selector.SelectAuto(state)
            : _selector.SelectManual(mode);

        if (selection.Phase == RuntimePhase.None)
        {
            var payload = new
            {
                tick_id = $"tick_{DateTime.Now:yyyyMMdd_HHmmss}",
                timestamp_start = DateTimeOffset.Now.ToString("O"),
                timestamp_end = DateTimeOffset.Now.ToString("O"),
                requested_mode = mode,
                selected_phase = "none",
                selection_reason = selection.Reason,
                selection_reasons = selection.Reasons,
                can_run = false,
                severity = GateSeverity.Blocking.ToString(),
                reasons = selection.Reasons,
                recommended_next_action = "No phase selected. Check runtime state and mode.",
                python_command_preview = string.Empty,
                launched = false,
                python_exit_code = (int?)null,
                final_status = "no_phase_selected"
            };
            _resultWriter.WriteSchedulerTick(registry, payload);
            _manifestWriter.Write(registry, "scheduler-tick", payload);
            return new SchedulerTickResult { ExitCode = 2, FinalStatus = "no_phase_selected", SelectedPhase = RuntimePhase.None, Launched = false, Blocked = true };
        }

        var result = await _orchestrator.RunAsync(registry, runtimes, commandFactory, selection.Phase, passthroughArgs);
        var tickPayload = new
        {
            tick_id = $"tick_{DateTime.Now:yyyyMMdd_HHmmss}",
            timestamp_start = result.TimestampStart.ToString("O"),
            timestamp_end = result.TimestampEnd.ToString("O"),
            requested_mode = mode,
            selected_phase = ToPhaseName(result.Phase),
            selection_reason = selection.Reason,
            selection_reasons = selection.Reasons,
            can_run = result.CanRun,
            severity = result.Severity.ToString(),
            reasons = result.Reasons,
            recommended_next_action = result.RecommendedNextAction,
            python_command_preview = result.PythonCommandPreview,
            launched = result.Launched,
            python_exit_code = result.PythonExitCode,
            final_status = result.FinalStatus
        };

        _resultWriter.WriteSchedulerTick(registry, tickPayload);
        _manifestWriter.Write(registry, "scheduler-tick", tickPayload);

        if (result.FinalStatus == "succeeded")
        {
            return new SchedulerTickResult { ExitCode = 0, FinalStatus = result.FinalStatus, SelectedPhase = result.Phase, Launched = result.Launched, Blocked = false };
        }

        if (result.FinalStatus == "blocked")
        {
            return new SchedulerTickResult { ExitCode = 2, FinalStatus = result.FinalStatus, SelectedPhase = result.Phase, Launched = false, Blocked = true };
        }

        return new SchedulerTickResult
        {
            ExitCode = result.PythonExitCode ?? 1,
            FinalStatus = result.FinalStatus,
            SelectedPhase = result.Phase,
            Launched = result.Launched,
            Blocked = false
        };
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
}
