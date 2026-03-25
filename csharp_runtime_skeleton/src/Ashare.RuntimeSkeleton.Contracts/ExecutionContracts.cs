namespace Ashare.RuntimeSkeleton.Contracts;

public sealed record ExecutionWindowDefinition
{
    public string Label { get; init; } = string.Empty;
    public string Start { get; init; } = string.Empty;
    public string End { get; init; } = string.Empty;
}

public sealed record TradeClockPhaseDefinition
{
    public string Name { get; init; } = string.Empty;
    public string ScheduledTime { get; init; } = string.Empty;
    public int TimeoutMinutes { get; init; }
    public string LockName { get; init; } = string.Empty;
}

public sealed record ReleaseReference
{
    public string ReleaseId { get; init; } = string.Empty;
    public string TradeDate { get; init; } = string.Empty;
    public string Profile { get; init; } = string.Empty;
    public string SourceMode { get; init; } = string.Empty;
    public string ManifestPath { get; init; } = string.Empty;
    public string TargetPositionsPath { get; init; } = string.Empty;
}

public sealed record ExecutionGateSnapshot
{
    public bool Ok { get; init; }
    public bool ShouldExecute { get; init; }
    public bool IgnoreWindow { get; init; }
    public bool CalendarOk { get; init; }
    public bool TradeDateOk { get; init; }
    public bool TimeWindowOk { get; init; }
    public string Reason { get; init; } = string.Empty;
    public string AccountMode { get; init; } = "precision";
    public bool PrecisionTradeEnabled { get; init; }
    public ReleaseReference Release { get; init; } = new();
}

public sealed record SafetyDecision
{
    public bool AllowExecution { get; init; }
    public bool EffectiveReduceOnly { get; init; }
    public bool PanicReduceOnlyIgnored { get; init; }
    public bool AllowUnfinishedOrdersReconcile { get; init; }
    public bool UnfinishedOrdersReconcileAllowed { get; init; }
    public string SystemMode { get; init; } = string.Empty;
    public string HaltReason { get; init; } = string.Empty;
}

public sealed record PythonCommandSpec
{
    public string EntryPointPath { get; init; } = string.Empty;
    public string PreferredPythonPath { get; init; } = string.Empty;
    public IReadOnlyList<string> Arguments { get; init; } = [];
}

public sealed record PythonInvocationRequest
{
    public string Purpose { get; init; } = string.Empty;
    public PythonCommandSpec Command { get; init; } = new();
    public string WorkingDirectory { get; init; } = string.Empty;
}

public sealed record PythonInvocationResult
{
    public int ExitCode { get; init; }
    public string StandardOutput { get; init; } = string.Empty;
    public string StandardError { get; init; } = string.Empty;
}

public sealed record OmsLedgerArtifact
{
    public string Name { get; init; } = string.Empty;
    public string Path { get; init; } = string.Empty;
    public string Purpose { get; init; } = string.Empty;
}
