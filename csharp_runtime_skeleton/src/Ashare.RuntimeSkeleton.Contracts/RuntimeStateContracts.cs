using System.Text.Json.Serialization;

namespace Ashare.RuntimeSkeleton.Contracts;

public sealed record LatestReleasePointer
{
    [JsonPropertyName("release_id")]
    public string ReleaseId { get; init; } = string.Empty;

    [JsonPropertyName("trade_date")]
    public string TradeDate { get; init; } = string.Empty;

    [JsonPropertyName("manifest_path")]
    public string ManifestPath { get; init; } = string.Empty;

    [JsonPropertyName("generated_at")]
    public string GeneratedAt { get; init; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; init; } = string.Empty;
}

public sealed record ReleaseManifest
{
    [JsonPropertyName("release_id")]
    public string ReleaseId { get; init; } = string.Empty;

    [JsonPropertyName("trade_date")]
    public string TradeDate { get; init; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; init; } = string.Empty;

    [JsonPropertyName("generated_at")]
    public string GeneratedAt { get; init; } = string.Empty;

    [JsonPropertyName("simulation_ready")]
    public bool SimulationReady { get; init; }
}

public sealed record ClockGateRelease
{
    [JsonPropertyName("release_id")]
    public string ReleaseId { get; init; } = string.Empty;

    [JsonPropertyName("trade_date")]
    public string TradeDate { get; init; } = string.Empty;

    [JsonPropertyName("manifest_path")]
    public string ManifestPath { get; init; } = string.Empty;
}

public sealed record ClockGateSnapshot
{
    [JsonPropertyName("should_execute")]
    public bool ShouldExecute { get; init; }

    [JsonPropertyName("reason")]
    public string Reason { get; init; } = string.Empty;

    [JsonPropertyName("trade_date_ok")]
    public bool TradeDateOk { get; init; }

    [JsonPropertyName("time_window_ok")]
    public bool TimeWindowOk { get; init; }

    [JsonPropertyName("precision_trade_enabled")]
    public bool PrecisionTradeEnabled { get; init; }

    [JsonPropertyName("release")]
    public ClockGateRelease Release { get; init; } = new();
}

public sealed record ClockState
{
    [JsonPropertyName("last_heartbeat_at")]
    public string LastHeartbeatAt { get; init; } = string.Empty;

    [JsonPropertyName("market_stage")]
    public string MarketStage { get; init; } = string.Empty;

    [JsonPropertyName("next_due_phase")]
    public string NextDuePhase { get; init; } = string.Empty;

    [JsonPropertyName("next_due_trade_date")]
    public string NextDueTradeDate { get; init; } = string.Empty;

    [JsonPropertyName("gate")]
    public ClockGateSnapshot Gate { get; init; } = new();
}

public sealed record SafetyState
{
    [JsonPropertyName("system_mode")]
    public string SystemMode { get; init; } = string.Empty;

    [JsonPropertyName("market_safety_regime")]
    public string MarketSafetyRegime { get; init; } = string.Empty;

    [JsonPropertyName("manual_halt")]
    public bool ManualHalt { get; init; }

    [JsonPropertyName("gate_open")]
    public bool GateOpen { get; init; }

    [JsonPropertyName("halt_reason")]
    public string HaltReason { get; init; } = string.Empty;

    [JsonPropertyName("updated_at")]
    public string UpdatedAt { get; init; } = string.Empty;
}

public sealed record OmsSummary
{
    [JsonPropertyName("generated_at")]
    public string GeneratedAt { get; init; } = string.Empty;

    [JsonPropertyName("release_id")]
    public string ReleaseId { get; init; } = string.Empty;
}

public sealed record ActualPortfolioState
{
    [JsonPropertyName("generated_at")]
    public string GeneratedAt { get; init; } = string.Empty;

    [JsonPropertyName("release_id")]
    public string ReleaseId { get; init; } = string.Empty;
}

public sealed record UnifiedRuntimeState
{
    public bool ReleasePointerExists { get; init; }
    public bool ReleaseManifestExists { get; init; }
    public string ReleaseId { get; init; } = string.Empty;
    public string TradeDate { get; init; } = string.Empty;
    public string ClockHeartbeatAt { get; init; } = string.Empty;
    public string ClockPhase { get; init; } = string.Empty;
    public string GateReason { get; init; } = string.Empty;
    public string SafetyMode { get; init; } = string.Empty;
    public bool AllowExecution { get; init; }
    public bool OmsSummaryExists { get; init; }
    public bool ActualStateExists { get; init; }
    public IReadOnlyList<string> BlockingReasons { get; init; } = [];

    public string ReleasePointerPath { get; init; } = string.Empty;
    public string ReleaseManifestPath { get; init; } = string.Empty;
    public string ClockStatePath { get; init; } = string.Empty;
    public string SafetyStatePath { get; init; } = string.Empty;
    public string OmsSummaryPath { get; init; } = string.Empty;
    public string ActualStatePath { get; init; } = string.Empty;
}

public enum GateSeverity
{
    Normal = 0,
    Warning = 1,
    Blocking = 2
}

public sealed record GateEvaluation
{
    public bool CanExecute { get; init; }
    public GateSeverity Severity { get; init; }
    public IReadOnlyList<string> Reasons { get; init; } = [];
    public string RecommendedNextAction { get; init; } = string.Empty;
}
