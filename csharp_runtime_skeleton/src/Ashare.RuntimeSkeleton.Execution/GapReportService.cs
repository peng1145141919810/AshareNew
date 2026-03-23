using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Oms;
using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class GapReportService
{
    private readonly DesiredStateService _desiredStateService;
    private readonly OmsStateFacade _omsStateFacade;
    private readonly GapThresholdPolicyProvider _policyProvider;

    public GapReportService(
        DesiredStateService desiredStateService,
        OmsStateFacade omsStateFacade,
        GapThresholdPolicyProvider? policyProvider = null)
    {
        _desiredStateService = desiredStateService;
        _omsStateFacade = omsStateFacade;
        _policyProvider = policyProvider ?? new GapThresholdPolicyProvider();
    }

    public GapReport Build(PathRegistry registry)
    {
        var desired = _desiredStateService.Read(registry);
        var oms = _omsStateFacade.Read(
            Path.Combine(registry.ExternalOmsRoot, "snapshots", "oms_summary.json"),
            Path.Combine(registry.ExternalOmsRoot, "snapshots", "latest_actual_portfolio_state.json"));
        var policy = _policyProvider.Load(registry);

        var reasons = new List<string>();
        reasons.AddRange(desired.Reasons);
        reasons.AddRange(oms.Reasons);

        var desiredBySymbol = desired.Positions
            .Where(x => !string.IsNullOrWhiteSpace(x.Symbol))
            .GroupBy(x => x.Symbol, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(g => g.Key, g => g.First(), StringComparer.OrdinalIgnoreCase);

        var actualBySymbol = oms.ActualPositions
            .Where(x => !string.IsNullOrWhiteSpace(x.Symbol))
            .GroupBy(x => x.Symbol, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(g => g.Key, g => g.First(), StringComparer.OrdinalIgnoreCase);

        var desiredSymbols = desiredBySymbol.Keys.ToHashSet(StringComparer.OrdinalIgnoreCase);
        var actualSymbols = actualBySymbol.Keys.ToHashSet(StringComparer.OrdinalIgnoreCase);

        var missingInActual = desiredSymbols.Except(actualSymbols, StringComparer.OrdinalIgnoreCase).OrderBy(x => x).ToArray();
        var extraInActual = actualSymbols.Except(desiredSymbols, StringComparer.OrdinalIgnoreCase).OrderBy(x => x).ToArray();
        var overlap = desiredSymbols.Intersect(actualSymbols, StringComparer.OrdinalIgnoreCase).ToArray();

        var canCompare = desired.HasDesiredState && oms.ActualStateExists;
        if (!desired.HasDesiredState)
        {
            reasons.Add("gap_compare_desired_unavailable");
        }

        if (!oms.ActualStateExists)
        {
            reasons.Add("gap_compare_actual_unavailable");
        }

        var weightCompareAvailable = desired.WeightCompareAvailable && oms.WeightCompareAvailable;
        var sharesCompareAvailable = desired.SharesCompareAvailable && oms.SharesCompareAvailable;

        var weightMismatchSymbols = new List<string>();
        var sharesMismatchSymbols = new List<string>();
        var blockingReasons = new List<string>();
        var warningReasons = new List<string>();

        foreach (var symbol in overlap)
        {
            var d = desiredBySymbol[symbol];
            var a = actualBySymbol[symbol];

            if (weightCompareAvailable && d.TargetWeight.HasValue && a.ActualWeight.HasValue)
            {
                var diff = Math.Abs(d.TargetWeight.Value - a.ActualWeight.Value);
                if (diff >= policy.WeightMismatchWarningThreshold)
                {
                    weightMismatchSymbols.Add(symbol);
                    if (diff >= policy.WeightMismatchBlockingThreshold)
                    {
                        blockingReasons.Add($"weight_mismatch_blocking:{symbol}:{diff:F6}");
                    }
                    else
                    {
                        warningReasons.Add($"weight_mismatch_warning:{symbol}:{diff:F6}");
                    }
                }
            }

            if (sharesCompareAvailable && d.TargetShares.HasValue && a.ActualShares.HasValue)
            {
                var diff = Math.Abs(d.TargetShares.Value - a.ActualShares.Value);
                if (diff >= policy.SharesMismatchWarningThreshold)
                {
                    sharesMismatchSymbols.Add(symbol);
                    if (diff >= policy.SharesMismatchBlockingThreshold)
                    {
                        blockingReasons.Add($"shares_mismatch_blocking:{symbol}:{diff:F2}");
                    }
                    else
                    {
                        warningReasons.Add($"shares_mismatch_warning:{symbol}:{diff:F2}");
                    }
                }
            }
        }

        if (!canCompare)
        {
            blockingReasons.Add("gap_compare_unavailable");
        }

        if (missingInActual.Length > 0)
        {
            warningReasons.Add("symbol_missing_in_actual");
        }

        if (extraInActual.Length > 0)
        {
            warningReasons.Add("symbol_extra_in_actual");
        }

        if (!weightCompareAvailable)
        {
            warningReasons.Add("weight_compare_unavailable");
        }

        if (!sharesCompareAvailable)
        {
            warningReasons.Add("shares_compare_unavailable");
        }

        var severity = GateSeverity.Normal;
        if (blockingReasons.Count > 0)
        {
            severity = GateSeverity.Blocking;
        }
        else if (warningReasons.Count > 0)
        {
            severity = GateSeverity.Warning;
        }

        var summary = canCompare
            ? $"symbol_missing={missingInActual.Length}, symbol_extra={extraInActual.Length}, weight_mismatch={weightMismatchSymbols.Count}, shares_mismatch={sharesMismatchSymbols.Count}, overlap={overlap.Length}"
            : "compare_unavailable";

        var combinedReasons = reasons
            .Concat(blockingReasons)
            .Concat(warningReasons)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();

        return new GapReport
        {
            HasDesiredState = desired.HasDesiredState,
            HasActualState = oms.ActualStateExists,
            CanCompare = canCompare,
            DesiredSymbolCount = desired.SymbolCount,
            ActualSymbolCount = actualSymbols.Count,
            OverlapSymbolCount = overlap.Length,
            SymbolMissingInActual = missingInActual,
            SymbolExtraInActual = extraInActual,
            WeightMismatchSymbols = weightMismatchSymbols.Distinct(StringComparer.OrdinalIgnoreCase).OrderBy(x => x).ToArray(),
            SharesMismatchSymbols = sharesMismatchSymbols.Distinct(StringComparer.OrdinalIgnoreCase).OrderBy(x => x).ToArray(),
            WeightMismatchCount = weightMismatchSymbols.Distinct(StringComparer.OrdinalIgnoreCase).Count(),
            SharesMismatchCount = sharesMismatchSymbols.Distinct(StringComparer.OrdinalIgnoreCase).Count(),
            WeightCompareAvailable = weightCompareAvailable,
            SharesCompareAvailable = sharesCompareAvailable,
            CompareCapabilities = new Dictionary<string, bool>
            {
                ["symbol_presence"] = canCompare,
                ["weight_compare"] = weightCompareAvailable,
                ["shares_compare"] = sharesCompareAvailable
            },
            ThresholdPolicy = policy,
            BlockingReasons = blockingReasons.Distinct(StringComparer.OrdinalIgnoreCase).ToArray(),
            WarningReasons = warningReasons.Distinct(StringComparer.OrdinalIgnoreCase).ToArray(),
            MismatchSummary = summary,
            Severity = severity,
            Reasons = combinedReasons,
            SummaryText = summary
        };
    }
}
