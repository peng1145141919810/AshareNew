using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Pathing;
using Ashare.RuntimeSkeleton.PythonBridge;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class SchedulerHostService
{
    private readonly RuntimeStateAggregator _aggregator;
    private readonly SchedulerTickService _tickService;
    private readonly RuntimeResultWriter _resultWriter;
    private readonly RuntimeRunManifestWriter _manifestWriter;

    public SchedulerHostService(
        RuntimeStateAggregator aggregator,
        SchedulerTickService tickService,
        RuntimeResultWriter resultWriter,
        RuntimeRunManifestWriter manifestWriter)
    {
        _aggregator = aggregator;
        _tickService = tickService;
        _resultWriter = resultWriter;
        _manifestWriter = manifestWriter;
    }

    public async Task<int> RunAsync(
        PathRegistry registry,
        PythonRuntimeSelection runtimes,
        PythonCommandFactory commandFactory,
        string mode,
        IReadOnlyList<string> passthroughArgs)
    {
        var start = DateTimeOffset.Now;
        var precheckReasons = new List<string>();

        if (!File.Exists(registry.LaunchCanonicalPath))
        {
            precheckReasons.Add("launch_canonical_missing");
        }

        if (!File.Exists(registry.ManifestPath))
        {
            precheckReasons.Add("system_manifest_missing");
        }

        if (precheckReasons.Count > 0)
        {
            var blockedPayload = new
            {
                host_id = $"host_{DateTime.Now:yyyyMMdd_HHmmss}",
                timestamp_start = start.ToString("O"),
                timestamp_end = DateTimeOffset.Now.ToString("O"),
                requested_mode = mode,
                selected_phase = "none",
                can_run = false,
                severity = "Blocking",
                reasons = precheckReasons,
                recommended_next_action = "Fix scheduler host precheck issues.",
                python_command_preview = string.Empty,
                launched = false,
                python_exit_code = (int?)null,
                final_status = "blocked"
            };

            _resultWriter.WriteSchedulerHost(registry, blockedPayload);
            _manifestWriter.Write(registry, "scheduler-host", blockedPayload);
            return 2;
        }

        var tick = await _tickService.RunAsync(registry, runtimes, commandFactory, mode, passthroughArgs);

        var payload = new
        {
            host_id = $"host_{DateTime.Now:yyyyMMdd_HHmmss}",
            timestamp_start = start.ToString("O"),
            timestamp_end = DateTimeOffset.Now.ToString("O"),
            requested_mode = mode,
            selected_phase = ToPhaseName(tick.SelectedPhase),
            can_run = tick.ExitCode == 0,
            severity = tick.ExitCode == 0 ? "Normal" : "Warning",
            reasons = tick.ExitCode == 0 ? Array.Empty<string>() : new[] { "tick_failed_or_blocked" },
            recommended_next_action = tick.ExitCode == 0 ? "Scheduler host tick succeeded." : "Inspect scheduler_tick_result.json and phase journals.",
            python_command_preview = "delegated_to_scheduler_tick",
            launched = tick.Launched,
            python_exit_code = tick.ExitCode,
            final_status = tick.FinalStatus
        };

        _resultWriter.WriteSchedulerHost(registry, payload);
        _manifestWriter.Write(registry, "scheduler-host", payload);
        return tick.ExitCode;
    }

    public async Task<int> RunLoopAsync(
        PathRegistry registry,
        PythonRuntimeSelection runtimes,
        PythonCommandFactory commandFactory,
        string mode,
        int maxTicks,
        int intervalSeconds,
        IReadOnlyList<string> passthroughArgs)
    {
        var start = DateTimeOffset.Now;
        var hostId = $"host_loop_{DateTime.Now:yyyyMMdd_HHmmss}";
        var max = Math.Max(maxTicks, 1);
        var interval = Math.Max(intervalSeconds, 1);

        var tickRows = new List<object>();
        var phasesSeen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var phasesBlocked = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var phasesLaunched = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var finalCode = 0;

        for (var i = 1; i <= max; i++)
        {
            var tick = await _tickService.RunAsync(registry, runtimes, commandFactory, mode, passthroughArgs);
            var phaseName = ToPhaseName(tick.SelectedPhase);

            phasesSeen.Add(phaseName);
            if (tick.Blocked)
            {
                phasesBlocked.Add(phaseName);
            }

            if (tick.Launched)
            {
                phasesLaunched.Add(phaseName);
            }

            tickRows.Add(new
            {
                tick_index = i,
                selected_phase = phaseName,
                launched = tick.Launched,
                blocked = tick.Blocked,
                exit_code = tick.ExitCode,
                final_status = tick.FinalStatus,
                timestamp = DateTimeOffset.Now.ToString("O")
            });

            finalCode = tick.ExitCode;
            if (finalCode != 0)
            {
                break;
            }

            if (i < max)
            {
                await Task.Delay(TimeSpan.FromSeconds(interval));
            }
        }

        var payload = new
        {
            host_id = hostId,
            timestamp_start = start.ToString("O"),
            timestamp_end = DateTimeOffset.Now.ToString("O"),
            requested_mode = mode,
            loop = true,
            max_ticks = max,
            interval_seconds = interval,
            ticks = tickRows,
            final_status = finalCode == 0 ? "succeeded" : "failed_or_blocked",
            python_exit_code = finalCode
        };

        _resultWriter.WriteSchedulerHost(registry, payload);
        _manifestWriter.Write(registry, "scheduler-host-loop", payload);

        var shadowPayload = new
        {
            started_at = start.ToString("O"),
            ended_at = DateTimeOffset.Now.ToString("O"),
            ticks_run = tickRows.Count,
            phases_seen = phasesSeen.OrderBy(x => x).ToArray(),
            phases_blocked = phasesBlocked.OrderBy(x => x).ToArray(),
            phases_launched = phasesLaunched.OrderBy(x => x).ToArray(),
            journals_written = tickRows.Count,
            gap_reports_written = tickRows.Count,
            parity_observations = new[]
            {
                "loop_runs_under_csharp_control_plane",
                "phase_selection_and_launch_are_audited",
                "execution_sensitive_phases_use_deeper_gap"
            },
            cutover_safe_now = false,
            notes = "Controlled shadow loop only. Live cutover remains disabled."
        };
        _resultWriter.WriteShadowRunReport(registry, shadowPayload);
        _manifestWriter.Write(registry, "shadow-run-report", shadowPayload);

        return finalCode;
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
