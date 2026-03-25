using System.Text.Json.Serialization;

namespace Ashare.RuntimeSkeleton.Contracts;

public sealed record CanonicalRuntimeManifest
{
    [JsonPropertyName("formal_operator_entry")]
    public string FormalOperatorEntry { get; init; } = string.Empty;

    [JsonPropertyName("trade_clock_service_entry")]
    public string TradeClockServiceEntry { get; init; } = string.Empty;

    [JsonPropertyName("wrapped_business_root_entry")]
    public string WrappedBusinessRootEntry { get; init; } = string.Empty;

    [JsonPropertyName("live_runtime_root")]
    public string LiveRuntimeRoot { get; init; } = string.Empty;

    [JsonPropertyName("default_mode")]
    public string DefaultMode { get; init; } = "integrated_supervisor";

    [JsonPropertyName("default_profile")]
    public string DefaultProfile { get; init; } = "quick_test";

    [JsonPropertyName("formal_output_root")]
    public string FormalOutputRoot { get; init; } = string.Empty;

    [JsonPropertyName("formal_run_manifest_name")]
    public string FormalRunManifestName { get; init; } = "run_manifest.json";
}

public sealed record RuntimePathManifest
{
    [JsonPropertyName("repo_root")]
    public string RepoRoot { get; init; } = string.Empty;

    [JsonPropertyName("live_data_root")]
    public string LiveDataRoot { get; init; } = string.Empty;

    [JsonPropertyName("active_v6_root")]
    public string ActiveV6Root { get; init; } = string.Empty;

    [JsonPropertyName("active_v5_runtime_root")]
    public string ActiveV5RuntimeRoot { get; init; } = string.Empty;

    [JsonPropertyName("archive_roots")]
    public IReadOnlyList<string> ArchiveRoots { get; init; } = [];

    [JsonPropertyName("experiment_roots")]
    public IReadOnlyList<string> ExperimentRoots { get; init; } = [];
}

public sealed record SystemManifestDocument
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; init; } = string.Empty;

    [JsonPropertyName("law_version")]
    public int LawVersion { get; init; }

    [JsonPropertyName("canonical")]
    public CanonicalRuntimeManifest Canonical { get; init; } = new();

    [JsonPropertyName("paths")]
    public RuntimePathManifest Paths { get; init; } = new();
}

public sealed record RunProfileDefinition
{
    [JsonPropertyName("description")]
    public string Description { get; init; } = string.Empty;

    [JsonPropertyName("mode_default")]
    public string ModeDefault { get; init; } = "integrated_supervisor";

    [JsonPropertyName("v5_cycles")]
    public int V5Cycles { get; init; }

    [JsonPropertyName("v6_plan_reuse_hours")]
    public int V6PlanReuseHours { get; init; }

    [JsonPropertyName("operator_use")]
    public string OperatorUse { get; init; } = string.Empty;
}

public sealed record RunProfilesDocument
{
    [JsonPropertyName("default_profile")]
    public string DefaultProfile { get; init; } = "quick_test";

    [JsonPropertyName("allowed_profiles")]
    public IReadOnlyDictionary<string, RunProfileDefinition> AllowedProfiles { get; init; } =
        new Dictionary<string, RunProfileDefinition>(StringComparer.OrdinalIgnoreCase);

    [JsonPropertyName("allowed_modes")]
    public IReadOnlyList<string> AllowedModes { get; init; } = [];
}
