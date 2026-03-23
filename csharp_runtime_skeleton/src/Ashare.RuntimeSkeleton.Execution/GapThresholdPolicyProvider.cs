using System.Text.Json;
using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class GapThresholdPolicyProvider
{
    private const decimal DefaultWeightWarning = 0.010m;
    private const decimal DefaultWeightBlocking = 0.030m;
    private const decimal DefaultSharesWarning = 100m;
    private const decimal DefaultSharesBlocking = 1000m;

    public GapThresholdPolicy Load(PathRegistry registry)
    {
        var path = Path.Combine(registry.Policy.WorkspaceRoot, "csharp_runtime_skeleton", "config", "gap_thresholds.json");
        if (!File.Exists(path))
        {
            return Defaults();
        }

        try
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var root = doc.RootElement;
            return new GapThresholdPolicy
            {
                WeightMismatchWarningThreshold = ReadDecimal(root, "weight_mismatch_warning_threshold", DefaultWeightWarning),
                WeightMismatchBlockingThreshold = ReadDecimal(root, "weight_mismatch_blocking_threshold", DefaultWeightBlocking),
                SharesMismatchWarningThreshold = ReadDecimal(root, "shares_mismatch_warning_threshold", DefaultSharesWarning),
                SharesMismatchBlockingThreshold = ReadDecimal(root, "shares_mismatch_blocking_threshold", DefaultSharesBlocking)
            };
        }
        catch
        {
            return Defaults();
        }
    }

    private static decimal ReadDecimal(JsonElement root, string name, decimal fallback)
    {
        if (!root.TryGetProperty(name, out var node))
        {
            return fallback;
        }

        if (node.ValueKind == JsonValueKind.Number && node.TryGetDecimal(out var val))
        {
            return val;
        }

        if (node.ValueKind == JsonValueKind.String && decimal.TryParse(node.GetString(), out var parsed))
        {
            return parsed;
        }

        return fallback;
    }

    private static GapThresholdPolicy Defaults()
    {
        return new GapThresholdPolicy
        {
            WeightMismatchWarningThreshold = DefaultWeightWarning,
            WeightMismatchBlockingThreshold = DefaultWeightBlocking,
            SharesMismatchWarningThreshold = DefaultSharesWarning,
            SharesMismatchBlockingThreshold = DefaultSharesBlocking
        };
    }
}
