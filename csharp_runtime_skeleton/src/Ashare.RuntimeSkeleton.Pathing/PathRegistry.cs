using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.Pathing;

public sealed record PathRegistry
{
    public WorkspacePathPolicy Policy { get; init; } = new();
    public string WorkspaceCodeRoot { get; init; } = string.Empty;
    public string FormalTraceRoot { get; init; } = string.Empty;
    public string ManifestPath { get; init; } = string.Empty;
    public string RunProfilesPath { get; init; } = string.Empty;
    public string LaunchCanonicalPath { get; init; } = string.Empty;
    public string MainResearchRunnerPath { get; init; } = string.Empty;
    public string TradeClockServicePath { get; init; } = string.Empty;
    public string AffordableDataBundleScriptPath { get; init; } = string.Empty;
    public string LivePriceSnapshotPath { get; init; } = string.Empty;
    public string IntegratedThesisRoot { get; init; } = string.Empty;
    public string IntradayStateRoot { get; init; } = string.Empty;
    public string IntradayPhaseStatePath { get; init; } = string.Empty;
    public string IntradaySymbolStatePath { get; init; } = string.Empty;
    public string IntradayIntentStatePath { get; init; } = string.Empty;
    public string IntradayEventLogPath { get; init; } = string.Empty;
    public string IntradayControlSummaryPath { get; init; } = string.Empty;
    public string ExternalTradeReleaseRoot { get; init; } = string.Empty;
    public string ExternalTradeClockRoot { get; init; } = string.Empty;
    public string ExternalOmsRoot { get; init; } = string.Empty;
    public string ExternalDataRoot { get; init; } = string.Empty;
    public string ClockStatePath { get; init; } = string.Empty;
    public string SafetyStatePath { get; init; } = string.Empty;
    public string ResearchSqlStorePath { get; init; } = string.Empty;
    public string AffordableSqlStorePath { get; init; } = string.Empty;
    public string AffordableSnapshotRoot { get; init; } = string.Empty;
    public string PositionLedgerLatestPath { get; init; } = string.Empty;
    public string MechanismRealismRollupPath { get; init; } = string.Empty;
    public string LatestTAuditJsonPath { get; init; } = string.Empty;
    public string LatestTAuditWindowCsvPath { get; init; } = string.Empty;
    public string SitePublishRoot { get; init; } = string.Empty;
    public string AuditReportsRoot { get; init; } = string.Empty;
    public string OperatorRuntimeContextPath { get; init; } = string.Empty;
    public string LegacyDataRoot { get; init; } = string.Empty;
    public bool UsesLegacyDataFallback { get; init; }

    public static PathRegistry Create(string workspaceRoot)
    {
        var normalizedRoot = Path.GetFullPath(workspaceRoot);
        const string legacyRoot = @"F:\quant_data\Ashare";
        var localDataRoot = Path.Combine(normalizedRoot, "data");
        var legacyDataRoot = Path.Combine(legacyRoot, "data");

        var useLocalData = Directory.Exists(localDataRoot) && HasMinimumRuntimeContract(localDataRoot);
        var externalDataRoot = useLocalData ? localDataRoot : legacyDataRoot;

        return new PathRegistry
        {
            Policy = new WorkspacePathPolicy
            {
                WorkspaceRoot = normalizedRoot,
                LegacyRepoRoot = legacyRoot,
                ExternalDataRoot = externalDataRoot,
                ProtectLegacyRepo = true
            },
            WorkspaceCodeRoot = Path.Combine(
                normalizedRoot,
                "quant_research_hub_v6_repacked_clean",
                "quant_research_hub_v6_repacked_clean"),
            FormalTraceRoot = Path.Combine(normalizedRoot, "outputs", "canonical_runs"),
            ManifestPath = Path.Combine(normalizedRoot, "SYSTEM_MANIFEST.yaml"),
            RunProfilesPath = Path.Combine(normalizedRoot, "RUN_PROFILES.yaml"),
            LaunchCanonicalPath = Path.Combine(normalizedRoot, "launch_canonical.py"),
            MainResearchRunnerPath = Path.Combine(normalizedRoot, "main_research_runner.py"),
            TradeClockServicePath = Path.Combine(normalizedRoot, "trade_clock_service.py"),
            AffordableDataBundleScriptPath = Path.Combine(normalizedRoot, "scripts", "update_affordable_data_bundle.py"),
            LivePriceSnapshotPath = Path.Combine(externalDataRoot, "live_execution_bridge", "daily_price_snapshot.csv"),
            IntegratedThesisRoot = Path.Combine(externalDataRoot, "event_lake_v6", "research", "integrated_thesis"),
            IntradayStateRoot = Path.Combine(localDataRoot, "trade_clock", "intraday_state"),
            IntradayPhaseStatePath = Path.Combine(localDataRoot, "trade_clock", "intraday_state", "latest", "intraday_phase_state.json"),
            IntradaySymbolStatePath = Path.Combine(localDataRoot, "trade_clock", "intraday_state", "latest", "symbol_execution_state.csv"),
            IntradayIntentStatePath = Path.Combine(localDataRoot, "trade_clock", "intraday_state", "latest", "intent_state_daily.csv"),
            IntradayEventLogPath = Path.Combine(localDataRoot, "trade_clock", "intraday_state", "latest", "intraday_event_log.jsonl"),
            IntradayControlSummaryPath = Path.Combine(localDataRoot, "trade_clock", "intraday_state", "latest", "intraday_control_summary.json"),
            ExternalTradeReleaseRoot = Path.Combine(externalDataRoot, "trade_release_v1"),
            ExternalTradeClockRoot = Path.Combine(externalDataRoot, "trade_clock"),
            ExternalOmsRoot = Path.Combine(externalDataRoot, "live_execution_bridge", "oms_v1"),
            ExternalDataRoot = externalDataRoot,
            ClockStatePath = Path.Combine(externalDataRoot, "trade_clock", "clock_state.json"),
            SafetyStatePath = Path.Combine(externalDataRoot, "trade_clock", "system_safety_state.json"),
            ResearchSqlStorePath = Path.Combine(localDataRoot, "sql_store", "research_fact_layers_v1.sqlite3"),
            AffordableSqlStorePath = Path.Combine(localDataRoot, "sql_store", "affordable_data_v1.sqlite3"),
            AffordableSnapshotRoot = Path.Combine(localDataRoot, "affordable_feeds", "latest"),
            PositionLedgerLatestPath = Path.Combine(externalDataRoot, "live_execution_bridge", "oms_v1", "ledgers", "position_ledger_latest.csv"),
            MechanismRealismRollupPath = Path.Combine(externalDataRoot, "live_execution_bridge", "oms_v1", "feedback", "mechanism_realism_rollup.csv"),
            LatestTAuditJsonPath = Path.Combine(localDataRoot, "audit_v1", "latest", "latest_t_audit.json"),
            LatestTAuditWindowCsvPath = Path.Combine(localDataRoot, "audit_v1", "latest", "t_overlay_window_daily.csv"),
            SitePublishRoot = Path.Combine(normalizedRoot, "outputs", "site_publish_stage"),
            AuditReportsRoot = Path.Combine(normalizedRoot, "outputs", "site_publish_stage", "reports"),
            OperatorRuntimeContextPath = Path.Combine(normalizedRoot, "outputs", "site_publish_stage", "operator_runtime_context.json"),
            LegacyDataRoot = legacyDataRoot,
            UsesLegacyDataFallback = !useLocalData
        };
    }

    private static bool HasMinimumRuntimeContract(string dataRoot)
    {
        var required =
            new[]
            {
                Path.Combine(dataRoot, "trade_release_v1", "latest_release.json"),
                Path.Combine(dataRoot, "trade_clock", "clock_state.json"),
                Path.Combine(dataRoot, "trade_clock", "system_safety_state.json"),
                Path.Combine(dataRoot, "live_execution_bridge", "oms_v1", "snapshots", "oms_summary.json"),
                Path.Combine(dataRoot, "live_execution_bridge", "oms_v1", "snapshots", "latest_actual_portfolio_state.json")
            };

        return required.All(File.Exists);
    }

    public IReadOnlyList<OmsLedgerArtifact> GetOmsArtifacts()
    {
        return
        [
            new() { Name = "ActualState", Path = Path.Combine(ExternalOmsRoot, "snapshots", "latest_actual_portfolio_state.json"), Purpose = "OMS actual-state truth." },
            new() { Name = "OmsSummary", Path = Path.Combine(ExternalOmsRoot, "snapshots", "oms_summary.json"), Purpose = "OMS summary snapshot." },
            new() { Name = "IntentLedger", Path = Path.Combine(ExternalOmsRoot, "ledgers", "intent_ledger_latest.csv"), Purpose = "Current OMS intent ledger." },
            new() { Name = "OrderLedger", Path = Path.Combine(ExternalOmsRoot, "ledgers", "order_ledger_latest.csv"), Purpose = "Current OMS order ledger." },
            new() { Name = "FillLedger", Path = Path.Combine(ExternalOmsRoot, "ledgers", "fill_ledger_latest.csv"), Purpose = "Current OMS fill ledger." },
            new() { Name = "PositionLedger", Path = PositionLedgerLatestPath, Purpose = "Current OMS position ledger." },
            new() { Name = "MechanismRealismRollup", Path = MechanismRealismRollupPath, Purpose = "Execution realism rollup for audit attribution." }
        ];
    }
}
