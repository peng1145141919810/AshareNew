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
    public string ExternalTradeReleaseRoot { get; init; } = string.Empty;
    public string ExternalTradeClockRoot { get; init; } = string.Empty;
    public string ExternalOmsRoot { get; init; } = string.Empty;
    public string ExternalDataRoot { get; init; } = string.Empty;
    public string ResearchSqlStorePath { get; init; } = string.Empty;
    public string AffordableSqlStorePath { get; init; } = string.Empty;
    public string AffordableSnapshotRoot { get; init; } = string.Empty;
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
            ExternalTradeReleaseRoot = Path.Combine(externalDataRoot, "trade_release_v1"),
            ExternalTradeClockRoot = Path.Combine(externalDataRoot, "trade_clock"),
            ExternalOmsRoot = Path.Combine(externalDataRoot, "live_execution_bridge", "oms_v1"),
            ExternalDataRoot = externalDataRoot,
            ResearchSqlStorePath = Path.Combine(externalDataRoot, "sql_store", "research_data_v1.sqlite3"),
            AffordableSqlStorePath = Path.Combine(externalDataRoot, "sql_store", "affordable_data_v1.sqlite3"),
            AffordableSnapshotRoot = Path.Combine(externalDataRoot, "affordable_feeds", "latest"),
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
            new() { Name = "IntentLedger", Path = Path.Combine(ExternalOmsRoot, "intent_ledger_latest.csv"), Purpose = "Current OMS intent ledger." },
            new() { Name = "OrderLedger", Path = Path.Combine(ExternalOmsRoot, "order_ledger_latest.csv"), Purpose = "Current OMS order ledger." },
            new() { Name = "FillLedger", Path = Path.Combine(ExternalOmsRoot, "fill_ledger_latest.csv"), Purpose = "Current OMS fill ledger." }
        ];
    }
}
