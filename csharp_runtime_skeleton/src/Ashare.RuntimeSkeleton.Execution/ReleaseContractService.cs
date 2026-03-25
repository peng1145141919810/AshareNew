using System.Text.Json;
using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed record ReleaseContractSnapshot
{
    public bool PointerExists { get; init; }
    public bool ManifestExists { get; init; }
    public bool TargetPositionsExists { get; init; }
    public string PointerPath { get; init; } = string.Empty;
    public string ManifestPath { get; init; } = string.Empty;
    public string TargetPositionsPath { get; init; } = string.Empty;
    public LatestReleasePointer Pointer { get; init; } = new();
    public ReleaseManifest Manifest { get; init; } = new();
    public IReadOnlyList<string> ValidationIssues { get; init; } = [];

    public bool IsComplete => PointerExists && ManifestExists && TargetPositionsExists && ValidationIssues.Count == 0;
}

public sealed class ReleaseContractService
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true
    };

    public ReleaseContractSnapshot Read(PathRegistry registry)
    {
        var pointerPath = Path.Combine(registry.ExternalTradeReleaseRoot, "latest_release.json");
        var issues = new List<string>();

        var pointerExists = File.Exists(pointerPath);
        var pointer = pointerExists ? ReadJsonOrDefault<LatestReleasePointer>(pointerPath) : new LatestReleasePointer();
        var manifestPath = pointer.ManifestPath;
        if (string.IsNullOrWhiteSpace(manifestPath))
        {
            issues.Add("manifest_path_missing_in_pointer");
        }

        var manifestExists = !string.IsNullOrWhiteSpace(manifestPath) && File.Exists(manifestPath);
        var manifest = manifestExists ? ReadJsonOrDefault<ReleaseManifest>(manifestPath) : new ReleaseManifest();

        var targetPositionsPath = string.Empty;
        if (manifestExists)
        {
            try
            {
                using var doc = JsonDocument.Parse(File.ReadAllText(manifestPath));
                if (doc.RootElement.TryGetProperty("artifacts", out var artifacts)
                    && artifacts.TryGetProperty("target_positions_path", out var targetPathProp)
                    && targetPathProp.ValueKind == JsonValueKind.String)
                {
                    targetPositionsPath = targetPathProp.GetString() ?? string.Empty;
                }
            }
            catch
            {
                issues.Add("manifest_artifacts_parse_failed");
            }
        }

        var targetExists = !string.IsNullOrWhiteSpace(targetPositionsPath) && File.Exists(targetPositionsPath);

        if (!pointerExists)
        {
            issues.Add("latest_release_missing");
        }

        if (!manifestExists)
        {
            issues.Add("release_manifest_missing");
        }

        if (manifestExists && !targetExists)
        {
            issues.Add("target_positions_missing");
        }

        if (pointerExists && manifestExists)
        {
            if (!string.IsNullOrWhiteSpace(pointer.ReleaseId)
                && !string.IsNullOrWhiteSpace(manifest.ReleaseId)
                && !string.Equals(pointer.ReleaseId, manifest.ReleaseId, StringComparison.OrdinalIgnoreCase))
            {
                issues.Add("release_id_mismatch_pointer_manifest");
            }

            if (!string.IsNullOrWhiteSpace(pointer.TradeDate)
                && !string.IsNullOrWhiteSpace(manifest.TradeDate)
                && !string.Equals(pointer.TradeDate, manifest.TradeDate, StringComparison.OrdinalIgnoreCase))
            {
                issues.Add("trade_date_mismatch_pointer_manifest");
            }
        }

        return new ReleaseContractSnapshot
        {
            PointerExists = pointerExists,
            ManifestExists = manifestExists,
            TargetPositionsExists = targetExists,
            PointerPath = pointerPath,
            ManifestPath = manifestPath,
            TargetPositionsPath = targetPositionsPath,
            Pointer = pointer,
            Manifest = manifest,
            ValidationIssues = issues
        };
    }

    private static T ReadJsonOrDefault<T>(string path) where T : new()
    {
        try
        {
            var text = File.ReadAllText(path);
            var value = JsonSerializer.Deserialize<T>(text, JsonOptions);
            return value ?? new T();
        }
        catch
        {
            return new T();
        }
    }
}
