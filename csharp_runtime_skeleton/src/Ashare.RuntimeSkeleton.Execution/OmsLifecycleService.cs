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
        var actualSnapshotPath = Path.Combine(registry.ExternalOmsRoot, "snapshots", "latest_actual_portfolio_state.json");
        var oms = _omsStateFacade.Read(
            Path.Combine(registry.ExternalOmsRoot, "snapshots", "oms_summary.json"),
            actualSnapshotPath);
        var gap = _gapReportService.Build(registry);

        var intentLedgerPath = Path.Combine(registry.ExternalOmsRoot, "intent_ledger_latest.csv");
        var orderLedgerPath = Path.Combine(registry.ExternalOmsRoot, "order_ledger_latest.csv");
        var fillLedgerPath = Path.Combine(registry.ExternalOmsRoot, "fill_ledger_latest.csv");

        var hasOrderArtifacts = File.Exists(orderLedgerPath) || File.Exists(intentLedgerPath);
        var hasFillArtifacts = File.Exists(fillLedgerPath);
        var hasAccountSnapshot = oms.ActualStateExists;

        var orderCount = ReadCsvRowCount(orderLedgerPath);
        var fillCount = ReadCsvRowCount(fillLedgerPath);

        var unavailable = new List<string>();
        if (!File.Exists(intentLedgerPath))
        {
            unavailable.Add("intent_lifecycle_unavailable");
        }
        if (!hasOrderArtifacts)
        {
            unavailable.Add("order_lifecycle_unavailable");
        }
        if (!hasFillArtifacts)
        {
            unavailable.Add("fill_lifecycle_unavailable");
        }
        if (!hasAccountSnapshot)
        {
            unavailable.Add("account_snapshot_unavailable");
        }

        var reasons = new List<string>();
        reasons.AddRange(unavailable);
        reasons.AddRange(gap.Reasons);

        var lifecycleSeverity = unavailable.Count > 0 ? GateSeverity.Warning : GateSeverity.Normal;
        if (!hasAccountSnapshot || !desired.HasDesiredState)
        {
            lifecycleSeverity = GateSeverity.Blocking;
        }

        var result = new OmsLifecycleResult
        {
            AuthorityOwner = "OmsLifecycleService",
            LifecycleStage = lifecycleStage,
            HasDesiredState = desired.HasDesiredState,
            HasActualState = oms.ActualStateExists,
            HasOrderArtifacts = hasOrderArtifacts,
            HasFillArtifacts = hasFillArtifacts,
            HasAccountSnapshot = hasAccountSnapshot,
            DesiredSnapshotPath = desired.ArtifactPath,
            ActualSnapshotPath = actualSnapshotPath,
            CompareCapability = gap.CanCompare,
            OrderCount = orderCount,
            FillCount = fillCount,
            MismatchSummary = gap.MismatchSummary,
            LifecycleSeverity = lifecycleSeverity,
            ReconciliationSeverity = gap.Severity,
            UnavailableReasons = unavailable,
            Reasons = reasons.Distinct(StringComparer.OrdinalIgnoreCase).ToArray()
        };

        _resultWriter.WriteOmsLifecycle(registry, new
        {
            timestamp = DateTimeOffset.Now.ToString("O"),
            authority_owner = result.AuthorityOwner,
            lifecycle_stage = result.LifecycleStage,
            has_desired_state = result.HasDesiredState,
            has_actual_state = result.HasActualState,
            has_order_artifacts = result.HasOrderArtifacts,
            has_fill_artifacts = result.HasFillArtifacts,
            has_account_snapshot = result.HasAccountSnapshot,
            desired_snapshot_path = result.DesiredSnapshotPath,
            actual_snapshot_path = result.ActualSnapshotPath,
            compare_capability = result.CompareCapability,
            order_count = result.OrderCount,
            fill_count = result.FillCount,
            mismatch_summary = result.MismatchSummary,
            lifecycle_severity = result.LifecycleSeverity.ToString(),
            reconciliation_severity = result.ReconciliationSeverity.ToString(),
            unavailable_reasons = result.UnavailableReasons,
            reasons = result.Reasons
        });

        return result;
    }

    public string WriteExecutionLifecycle(PathRegistry registry, RuntimePhase phase, ExecutionBackendResult backend, OmsLifecycleResult pre, OmsLifecycleResult post)
    {
        return _resultWriter.WriteExecutionLifecycle(registry, new
        {
            timestamp = DateTimeOffset.Now.ToString("O"),
            phase = phase.ToString().ToLowerInvariant(),
            control_plane_owner = backend.ControlPlaneOwner,
            authority_owner = backend.AuthorityOwner,
            backend_executor_type = backend.BackendExecutorType,
            adapter_used = backend.AdapterUsed,
            launched_by_control_plane = backend.LaunchedByControlPlane,
            submit_disabled = backend.SubmitDisabled,
            broker_isolated = backend.BrokerIsolated,
            final_status = backend.NormalizedFinalStatus,
            exit_code = backend.ExitCode,
            failure_classification = backend.FailureClassification,
            pre_oms_lifecycle = new
            {
                has_desired_state = pre.HasDesiredState,
                has_actual_state = pre.HasActualState,
                has_order_artifacts = pre.HasOrderArtifacts,
                has_fill_artifacts = pre.HasFillArtifacts,
                has_account_snapshot = pre.HasAccountSnapshot,
                compare_capability = pre.CompareCapability,
                order_count = pre.OrderCount,
                fill_count = pre.FillCount,
                lifecycle_severity = pre.LifecycleSeverity.ToString(),
                unavailable_reasons = pre.UnavailableReasons
            },
            post_oms_lifecycle = new
            {
                has_desired_state = post.HasDesiredState,
                has_actual_state = post.HasActualState,
                has_order_artifacts = post.HasOrderArtifacts,
                has_fill_artifacts = post.HasFillArtifacts,
                has_account_snapshot = post.HasAccountSnapshot,
                compare_capability = post.CompareCapability,
                order_count = post.OrderCount,
                fill_count = post.FillCount,
                lifecycle_severity = post.LifecycleSeverity.ToString(),
                unavailable_reasons = post.UnavailableReasons
            }
        });
    }

    private static int ReadCsvRowCount(string path)
    {
        if (!File.Exists(path))
        {
            return 0;
        }

        try
        {
            var lines = File.ReadAllLines(path).Where(x => !string.IsNullOrWhiteSpace(x)).ToArray();
            if (lines.Length <= 1)
            {
                return 0;
            }

            return lines.Length - 1;
        }
        catch
        {
            return 0;
        }
    }
}
