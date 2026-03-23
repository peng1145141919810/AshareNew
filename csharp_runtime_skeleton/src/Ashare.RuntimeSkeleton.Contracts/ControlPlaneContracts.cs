namespace Ashare.RuntimeSkeleton.Contracts;

public enum RuntimePhase
{
    None = 0,
    Research = 1,
    Release = 2,
    PreopenGate = 3,
    Simulation = 4,
    MiddayReview = 5,
    AfternoonExecution = 6,
    AfternoonShadow = 7,
    Summary = 8,
    Execution = 9
}

public sealed record DesiredPosition
{
    public string Symbol { get; init; } = string.Empty;
    public decimal? TargetWeight { get; init; }
    public decimal? TargetShares { get; init; }
    public string SourceArtifactPath { get; init; } = string.Empty;
    public string NormalizationStatus { get; init; } = string.Empty;
}

public sealed record DesiredStateSnapshot
{
    public string ReleaseId { get; init; } = string.Empty;
    public string TradeDate { get; init; } = string.Empty;
    public bool HasDesiredState { get; init; }
    public string ArtifactPath { get; init; } = string.Empty;
    public int RowCount { get; init; }
    public int SymbolCount { get; init; }
    public bool WeightCompareAvailable { get; init; }
    public bool SharesCompareAvailable { get; init; }
    public IReadOnlyList<DesiredPosition> Positions { get; init; } = [];
    public IReadOnlyList<string> Reasons { get; init; } = [];
}

public sealed record OmsActualPosition
{
    public string Symbol { get; init; } = string.Empty;
    public decimal? ActualShares { get; init; }
    public decimal? ActualWeight { get; init; }
    public string NormalizationStatus { get; init; } = string.Empty;
}

public sealed record GapThresholdPolicy
{
    public decimal WeightMismatchWarningThreshold { get; init; }
    public decimal WeightMismatchBlockingThreshold { get; init; }
    public decimal SharesMismatchWarningThreshold { get; init; }
    public decimal SharesMismatchBlockingThreshold { get; init; }
}

public sealed record GapReport
{
    public bool HasDesiredState { get; init; }
    public bool HasActualState { get; init; }
    public bool CanCompare { get; init; }
    public int DesiredSymbolCount { get; init; }
    public int ActualSymbolCount { get; init; }
    public int OverlapSymbolCount { get; init; }
    public IReadOnlyList<string> SymbolMissingInActual { get; init; } = [];
    public IReadOnlyList<string> SymbolExtraInActual { get; init; } = [];
    public IReadOnlyList<string> WeightMismatchSymbols { get; init; } = [];
    public IReadOnlyList<string> SharesMismatchSymbols { get; init; } = [];
    public int WeightMismatchCount { get; init; }
    public int SharesMismatchCount { get; init; }
    public bool WeightCompareAvailable { get; init; }
    public bool SharesCompareAvailable { get; init; }
    public IReadOnlyDictionary<string, bool> CompareCapabilities { get; init; } = new Dictionary<string, bool>();
    public GapThresholdPolicy ThresholdPolicy { get; init; } = new();
    public IReadOnlyList<string> BlockingReasons { get; init; } = [];
    public IReadOnlyList<string> WarningReasons { get; init; } = [];
    public string MismatchSummary { get; init; } = string.Empty;
    public GateSeverity Severity { get; init; }
    public IReadOnlyList<string> Reasons { get; init; } = [];
    public string SummaryText { get; init; } = string.Empty;
}

public sealed record PhaseSelection
{
    public RuntimePhase Phase { get; init; }
    public string Reason { get; init; } = string.Empty;
    public IReadOnlyList<string> Reasons { get; init; } = [];
}

public sealed record PhaseRunResult
{
    public string RunId { get; init; } = string.Empty;
    public RuntimePhase Phase { get; init; }
    public string MappedMode { get; init; } = string.Empty;
    public bool CanRun { get; init; }
    public GateSeverity Severity { get; init; }
    public IReadOnlyList<string> Reasons { get; init; } = [];
    public string RecommendedNextAction { get; init; } = string.Empty;
    public string PythonCommandPreview { get; init; } = string.Empty;
    public string BackendSelected { get; init; } = string.Empty;
    public string BackendExecutorType { get; init; } = string.Empty;
    public bool LaunchedByControlPlane { get; init; }
    public bool SubmitDisabled { get; init; }
    public bool BrokerIsolated { get; init; }
    public bool Launched { get; init; }
    public int? PythonExitCode { get; init; }
    public string FinalStatus { get; init; } = string.Empty;
    public GapReport? Gap { get; init; }
    public DateTimeOffset TimestampStart { get; init; }
    public DateTimeOffset TimestampEnd { get; init; }
}

public sealed record OmsLifecycleResult
{
    public string LifecycleStage { get; init; } = string.Empty;
    public string DesiredSnapshotPath { get; init; } = string.Empty;
    public string ActualSnapshotPath { get; init; } = string.Empty;
    public bool CompareCapability { get; init; }
    public string MismatchSummary { get; init; } = string.Empty;
    public GateSeverity ReconciliationSeverity { get; init; }
    public IReadOnlyList<string> Reasons { get; init; } = [];
    public bool OrderDataAvailable { get; init; }
    public bool FillDataAvailable { get; init; }
    public bool AccountDataAvailable { get; init; }
}

public sealed record SchedulerTickResult
{
    public int ExitCode { get; init; }
    public string FinalStatus { get; init; } = string.Empty;
    public RuntimePhase SelectedPhase { get; init; }
    public bool Launched { get; init; }
    public bool Blocked { get; init; }
}

public sealed record ReconciliationSummary
{
    public bool HasDesiredState { get; init; }
    public bool HasActualState { get; init; }
    public bool CanReconcile { get; init; }
    public string MismatchSummary { get; init; } = string.Empty;
    public GateSeverity Severity { get; init; }
    public IReadOnlyList<string> Reasons { get; init; } = [];
}
