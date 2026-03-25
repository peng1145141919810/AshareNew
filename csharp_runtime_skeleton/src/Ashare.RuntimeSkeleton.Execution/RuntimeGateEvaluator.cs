using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class RuntimeGateEvaluator
{
    public GateEvaluation Evaluate(UnifiedRuntimeState state)
    {
        var reasons = state.BlockingReasons.ToList();

        if (!state.OmsSummaryExists)
        {
            reasons.Add("oms_summary_unavailable");
        }

        if (!state.ActualStateExists)
        {
            reasons.Add("actual_state_unavailable");
        }

        var severity = ResolveSeverity(state, reasons);
        var canExecute = state.AllowExecution && severity != GateSeverity.Blocking;

        return new GateEvaluation
        {
            CanExecute = canExecute,
            Severity = severity,
            Reasons = reasons,
            RecommendedNextAction = BuildAction(canExecute, reasons)
        };
    }

    private static GateSeverity ResolveSeverity(UnifiedRuntimeState state, IReadOnlyList<string> reasons)
    {
        if (!state.ReleasePointerExists || !state.ReleaseManifestExists)
        {
            return GateSeverity.Blocking;
        }

        if (reasons.Any(x => x.StartsWith("safety_halt:", StringComparison.OrdinalIgnoreCase)))
        {
            return GateSeverity.Blocking;
        }

        if (!state.OmsSummaryExists || !state.ActualStateExists)
        {
            return GateSeverity.Blocking;
        }

        if (!state.AllowExecution || reasons.Any(x => x.StartsWith("clock_gate_blocked:", StringComparison.OrdinalIgnoreCase)))
        {
            return GateSeverity.Warning;
        }

        return GateSeverity.Normal;
    }

    private static string BuildAction(bool canExecute, IReadOnlyList<string> reasons)
    {
        if (canExecute)
        {
            return "Execution is green. Proceed with execution_only.";
        }

        if (reasons.Any(x => x.StartsWith("safety_halt:", StringComparison.OrdinalIgnoreCase)))
        {
            return "Safety is HALT. Clear safety incident or manual halt first.";
        }

        if (reasons.Contains("latest_release_missing") || reasons.Contains("release_manifest_missing"))
        {
            return "Publish a valid release first, then rerun doctor.";
        }

        if (reasons.Contains("oms_summary_missing") || reasons.Contains("latest_actual_portfolio_state_missing"))
        {
            return "Run OMS cycle to rebuild summary and actual state artifacts.";
        }

        if (reasons.Any(x => x.StartsWith("clock_gate_blocked:", StringComparison.OrdinalIgnoreCase)))
        {
            return "Clock gate is closed. Check window, trade_date, and precision_trade switch.";
        }

        return "Resolve blocking reasons, then rerun doctor.";
    }
}
