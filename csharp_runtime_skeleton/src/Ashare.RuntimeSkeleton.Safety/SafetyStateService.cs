using System.Text.Json;
using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.Safety;

public sealed record SafetySnapshot
{
    public bool Exists { get; init; }
    public string Path { get; init; } = string.Empty;
    public SafetyState State { get; init; } = new();
}

public sealed record SafetyPolicyView
{
    public bool FailClosed { get; init; }
    public bool IsHalt { get; init; }
    public string SystemMode { get; init; } = string.Empty;
    public IReadOnlyList<string> Reasons { get; init; } = [];
}

public sealed class SafetyStateService
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true
    };

    public SafetySnapshot Read(string path)
    {
        if (!File.Exists(path))
        {
            return new SafetySnapshot { Exists = false, Path = path };
        }

        try
        {
            var text = File.ReadAllText(path);
            var state = JsonSerializer.Deserialize<SafetyState>(text, JsonOptions) ?? new SafetyState();
            return new SafetySnapshot
            {
                Exists = true,
                Path = path,
                State = state
            };
        }
        catch
        {
            return new SafetySnapshot { Exists = false, Path = path };
        }
    }

    public SafetyPolicyView BuildPolicyView(SafetySnapshot snapshot, string scenario)
    {
        var reasons = new List<string>();

        if (!snapshot.Exists)
        {
            reasons.Add("safety_state_missing");
            return new SafetyPolicyView
            {
                FailClosed = string.Equals(scenario, "execution", StringComparison.OrdinalIgnoreCase),
                IsHalt = true,
                SystemMode = "HALT",
                Reasons = reasons
            };
        }

        if (snapshot.State.ManualHalt)
        {
            reasons.Add("manual_halt_on");
        }

        if (string.Equals(snapshot.State.SystemMode, "HALT", StringComparison.OrdinalIgnoreCase))
        {
            reasons.Add($"safety_halt:{(string.IsNullOrWhiteSpace(snapshot.State.HaltReason) ? "unknown" : snapshot.State.HaltReason)}");
        }

        var isExecution = string.Equals(scenario, "execution", StringComparison.OrdinalIgnoreCase);
        var failClosed = isExecution && (reasons.Count > 0);

        return new SafetyPolicyView
        {
            FailClosed = failClosed,
            IsHalt = reasons.Count > 0,
            SystemMode = string.IsNullOrWhiteSpace(snapshot.State.SystemMode) ? "UNKNOWN" : snapshot.State.SystemMode,
            Reasons = reasons
        };
    }
}
