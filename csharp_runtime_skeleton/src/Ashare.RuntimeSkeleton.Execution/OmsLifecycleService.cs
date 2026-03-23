using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Oms;
using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class OmsLifecycleService
{
    private readonly DesiredStateService _desiredStateService;
    private readonly OmsStateFacade _omsStateFacade;
    private readonly GapReportService _gapReportService;
    private readonly RuntimeResultWriter _resultWriter;

    public OmsLifecycleService(
        DesiredStateService desiredStateService,
        OmsStateFacade omsStateFacade,
        GapReportService gapReportService,
        RuntimeResultWriter resultWriter)
    {
        _desiredStateService = desiredStateService;
        _omsStateFacade = omsStateFacade;
        _gapReportService = gapReportService;
        _resultWriter = resultWriter;
    }

    public OmsLifecycleResult Capture(PathRegistry registry, string lifecycleStage)
    {
        var desired = _desiredStateService.Read(registry);
        var oms = _omsStateFacade.Read(
            Path.Combine(registry.ExternalOmsRoot, "snapshots", "oms_summary.json"),
            Path.Combine(registry.ExternalOmsRoot, "snapshots", "latest_actual_portfolio_state.json"));
        var gap = _gapReportService.Build(registry);

        var intentLedgerPath = Path.Combine(registry.ExternalOmsRoot, "intent_ledger_latest.csv");
        var orderLedgerPath = Path.Combine(registry.ExternalOmsRoot, "order_ledger_latest.csv");
        var fillLedgerPath = Path.Combine(registry.ExternalOmsRoot, "fill_ledger_latest.csv");

        var reasons = new List<string>();
        if (!File.Exists(intentLedgerPath))
        {
            reasons.Add("intent_lifecycle_unavailable");
        }
        if (!File.Exists(orderLedgerPath))
        {
            reasons.Add("order_lifecycle_unavailable");
        }
        if (!File.Exists(fillLedgerPath))
        {
            reasons.Add("fill_lifecycle_unavailable");
        }
        reasons.AddRange(gap.Reasons);

        var result = new OmsLifecycleResult
        {
            LifecycleStage = lifecycleStage,
            DesiredSnapshotPath = desired.ArtifactPath,
            ActualSnapshotPath = Path.Combine(registry.ExternalOmsRoot, "snapshots", "latest_actual_portfolio_state.json"),
            CompareCapability = gap.CanCompare,
            MismatchSummary = gap.MismatchSummary,
            ReconciliationSeverity = gap.Severity,
            Reasons = reasons.Distinct(StringComparer.OrdinalIgnoreCase).ToArray(),
            OrderDataAvailable = File.Exists(orderLedgerPath),
            FillDataAvailable = File.Exists(fillLedgerPath),
            AccountDataAvailable = oms.ActualStateExists
        };

        _resultWriter.WriteOmsLifecycle(registry, new
        {
            timestamp = DateTimeOffset.Now.ToString("O"),
            lifecycle_stage = result.LifecycleStage,
            desired_snapshot_path = result.DesiredSnapshotPath,
            actual_snapshot_path = result.ActualSnapshotPath,
            compare_capability = result.CompareCapability,
            mismatch_summary = result.MismatchSummary,
            reconciliation_severity = result.ReconciliationSeverity.ToString(),
            order_data_available = result.OrderDataAvailable,
            fill_data_available = result.FillDataAvailable,
            account_data_available = result.AccountDataAvailable,
            reasons = result.Reasons
        });

        return result;
    }
}
