using System.Text.Json;
using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class RuntimeResultWriter
{
    public string WriteGuarded(PathRegistry registry, object payload)
    {
        var io = RuntimeIoPaths.Build(registry);
        Directory.CreateDirectory(io.RuntimeRoot);
        File.WriteAllText(io.GuardedRunResultPath, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        return io.GuardedRunResultPath;
    }

    public string WriteClockHost(PathRegistry registry, object payload)
    {
        var io = RuntimeIoPaths.Build(registry);
        Directory.CreateDirectory(io.RuntimeRoot);
        File.WriteAllText(io.ClockHostResultPath, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        return io.ClockHostResultPath;
    }

    public string WriteGapReport(PathRegistry registry, object payload)
    {
        var io = RuntimeIoPaths.Build(registry);
        Directory.CreateDirectory(io.RuntimeRoot);
        File.WriteAllText(io.ReconciliationResultPath, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        return io.ReconciliationResultPath;
    }

    public string WriteSchedulerTick(PathRegistry registry, object payload)
    {
        var io = RuntimeIoPaths.Build(registry);
        Directory.CreateDirectory(io.RuntimeRoot);
        var path = Path.Combine(io.RuntimeRoot, "scheduler_tick_result.json");
        File.WriteAllText(path, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        return path;
    }

    public string WriteSchedulerHost(PathRegistry registry, object payload)
    {
        var io = RuntimeIoPaths.Build(registry);
        Directory.CreateDirectory(io.RuntimeRoot);
        var path = Path.Combine(io.RuntimeRoot, "scheduler_host_result.json");
        File.WriteAllText(path, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        return path;
    }

    public string WriteOmsLifecycle(PathRegistry registry, object payload)
    {
        var io = RuntimeIoPaths.Build(registry);
        Directory.CreateDirectory(io.RuntimeRoot);
        var path = Path.Combine(io.RuntimeRoot, "oms_lifecycle_result.json");
        File.WriteAllText(path, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        return path;
    }

    public string WriteExecutionLifecycle(PathRegistry registry, object payload)
    {
        var io = RuntimeIoPaths.Build(registry);
        Directory.CreateDirectory(io.RuntimeRoot);
        var path = Path.Combine(io.RuntimeRoot, "execution_lifecycle_result.json");
        File.WriteAllText(path, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        return path;
    }

    public string WriteShadowRunReport(PathRegistry registry, object payload)
    {
        var io = RuntimeIoPaths.Build(registry);
        Directory.CreateDirectory(io.RuntimeRoot);
        var path = Path.Combine(io.RuntimeRoot, "shadow_run_report.json");
        File.WriteAllText(path, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        return path;
    }

    public string WritePhaseJournal(PathRegistry registry, PhaseRunResult result)
    {
        var io = RuntimeIoPaths.Build(registry);
        Directory.CreateDirectory(io.PhaseRunsRoot);
        var phaseName = ToPhaseName(result.Phase);
        var path = Path.Combine(io.PhaseRunsRoot, $"{DateTime.Now:yyyyMMdd_HHmmss}_{phaseName}.json");
        var payload = new
        {
            run_id = result.RunId,
            timestamp_start = result.TimestampStart.ToString("O"),
            timestamp_end = result.TimestampEnd.ToString("O"),
            phase = phaseName,
            mapped_mode = result.MappedMode,
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
            symbol_missing_in_actual = result.Gap?.SymbolMissingInActual ?? [],
            symbol_extra_in_actual = result.Gap?.SymbolExtraInActual ?? [],
            weight_mismatch_symbols = result.Gap?.WeightMismatchSymbols ?? [],
            shares_mismatch_symbols = result.Gap?.SharesMismatchSymbols ?? [],
            weight_mismatch_count = result.Gap?.WeightMismatchCount,
            shares_mismatch_count = result.Gap?.SharesMismatchCount,
            compare_capabilities = result.Gap?.CompareCapabilities,
            weight_compare_available = result.Gap?.WeightCompareAvailable,
            shares_compare_available = result.Gap?.SharesCompareAvailable,
            threshold_policy = result.Gap?.ThresholdPolicy,
            blocking_reasons = result.Gap?.BlockingReasons ?? [],
            warning_reasons = result.Gap?.WarningReasons ?? []
        };
        File.WriteAllText(path, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        return path;
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
