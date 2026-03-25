using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Oms;
using Ashare.RuntimeSkeleton.Pathing;
using Ashare.RuntimeSkeleton.Safety;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class RuntimeStateAggregator
{
    public UnifiedRuntimeState Build(PathRegistry registry)
    {
        var releaseService = new ReleaseContractService();
        var safetyService = new SafetyStateService();
        var omsFacade = new OmsStateFacade();

        var release = releaseService.Read(registry);

        var clockPath = Path.Combine(registry.ExternalTradeClockRoot, "clock_state.json");
        var safetyPath = Path.Combine(registry.ExternalTradeClockRoot, "system_safety_state.json");
        var omsSummaryPath = Path.Combine(registry.ExternalOmsRoot, "snapshots", "oms_summary.json");
        var actualStatePath = Path.Combine(registry.ExternalOmsRoot, "snapshots", "latest_actual_portfolio_state.json");

        var clock = ReadClockState(clockPath);
        var safetySnapshot = safetyService.Read(safetyPath);
        var oms = omsFacade.Read(omsSummaryPath, actualStatePath);

        var reasons = new List<string>();
        reasons.AddRange(release.ValidationIssues);

        if (!File.Exists(clockPath))
        {
            reasons.Add("clock_state_missing");
        }

        if (!safetySnapshot.Exists)
        {
            reasons.Add("system_safety_state_missing");
        }

        var safetyPolicy = safetyService.BuildPolicyView(safetySnapshot, "execution");
        reasons.AddRange(safetyPolicy.Reasons);

        if (!oms.SummaryExists)
        {
            reasons.Add("oms_summary_missing");
        }

        if (!oms.ActualStateExists)
        {
            reasons.Add("latest_actual_portfolio_state_missing");
        }

        if (!clock.Gate.ShouldExecute)
        {
            var reason = string.IsNullOrWhiteSpace(clock.Gate.Reason) ? "gate_not_ready" : clock.Gate.Reason;
            reasons.Add($"clock_gate_blocked:{reason}");
        }

        var releaseId = FirstNonEmpty(
            release.Manifest.ReleaseId,
            release.Pointer.ReleaseId,
            clock.Gate.Release.ReleaseId);

        var tradeDate = FirstNonEmpty(
            release.Manifest.TradeDate,
            release.Pointer.TradeDate,
            clock.Gate.Release.TradeDate,
            clock.NextDueTradeDate);

        if (string.IsNullOrWhiteSpace(releaseId))
        {
            reasons.Add("release_id_unknown");
        }

        if (string.IsNullOrWhiteSpace(tradeDate))
        {
            reasons.Add("trade_date_unknown");
        }

        var allowExecution = release.IsComplete
            && File.Exists(clockPath)
            && safetySnapshot.Exists
            && clock.Gate.ShouldExecute
            && !safetyPolicy.FailClosed
            && !safetyPolicy.IsHalt;

        return new UnifiedRuntimeState
        {
            ReleasePointerExists = release.PointerExists,
            ReleaseManifestExists = release.ManifestExists,
            ReleaseId = releaseId,
            TradeDate = tradeDate,
            ClockHeartbeatAt = clock.LastHeartbeatAt,
            ClockPhase = clock.MarketStage,
            GateReason = clock.Gate.Reason,
            SafetyMode = safetyPolicy.SystemMode,
            AllowExecution = allowExecution,
            OmsSummaryExists = oms.SummaryExists,
            ActualStateExists = oms.ActualStateExists,
            BlockingReasons = reasons.Distinct(StringComparer.OrdinalIgnoreCase).ToArray(),
            ReleasePointerPath = release.PointerPath,
            ReleaseManifestPath = release.ManifestPath,
            ClockStatePath = clockPath,
            SafetyStatePath = safetyPath,
            OmsSummaryPath = omsSummaryPath,
            ActualStatePath = actualStatePath
        };
    }

    private static ClockState ReadClockState(string path)
    {
        if (!File.Exists(path))
        {
            return new ClockState();
        }

        try
        {
            var text = File.ReadAllText(path);
            return System.Text.Json.JsonSerializer.Deserialize<ClockState>(text, new System.Text.Json.JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true,
                ReadCommentHandling = System.Text.Json.JsonCommentHandling.Skip,
                AllowTrailingCommas = true
            }) ?? new ClockState();
        }
        catch
        {
            return new ClockState();
        }
    }

    private static string FirstNonEmpty(params string[] values)
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
}
