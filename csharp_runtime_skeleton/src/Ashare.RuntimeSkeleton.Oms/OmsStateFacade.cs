using System.Text.Json;
using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.Oms;

public sealed record OmsSnapshot
{
    public bool SummaryExists { get; init; }
    public bool ActualStateExists { get; init; }
    public string SummaryPath { get; init; } = string.Empty;
    public string ActualStatePath { get; init; } = string.Empty;
    public OmsSummary Summary { get; init; } = new();
    public ActualPortfolioState ActualState { get; init; } = new();
    public IReadOnlyList<OmsActualPosition> ActualPositions { get; init; } = [];
    public int SymbolCount { get; init; }
    public bool WeightCompareAvailable { get; init; }
    public bool SharesCompareAvailable { get; init; }
    public IReadOnlyList<string> Reasons { get; init; } = [];
}

public sealed class OmsStateFacade
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true
    };

    public OmsSnapshot Read(string summaryPath, string actualStatePath)
    {
        var reasons = new List<string>();
        var summaryExists = File.Exists(summaryPath);
        var actualExists = File.Exists(actualStatePath);

        if (!summaryExists)
        {
            reasons.Add("oms_summary_missing");
        }

        if (!actualExists)
        {
            reasons.Add("actual_state_missing");
        }

        var summary = summaryExists ? ReadJsonOrDefault<OmsSummary>(summaryPath) : new OmsSummary();
        var actualState = actualExists ? ReadJsonOrDefault<ActualPortfolioState>(actualStatePath) : new ActualPortfolioState();
        var parsed = actualExists ? ParseActualPositions(actualStatePath) : (new List<OmsActualPosition>(), false, false);

        return new OmsSnapshot
        {
            SummaryExists = summaryExists,
            ActualStateExists = actualExists,
            SummaryPath = summaryPath,
            ActualStatePath = actualStatePath,
            Summary = summary,
            ActualState = actualState,
            ActualPositions = parsed.Item1,
            SymbolCount = parsed.Item1.Count,
            WeightCompareAvailable = parsed.Item2,
            SharesCompareAvailable = parsed.Item3,
            Reasons = reasons
        };
    }

    private static (List<OmsActualPosition> Positions, bool WeightAvailable, bool SharesAvailable) ParseActualPositions(string actualStatePath)
    {
        try
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(actualStatePath));
            if (!doc.RootElement.TryGetProperty("positions", out var positionsNode)
                || positionsNode.ValueKind != JsonValueKind.Array)
            {
                return ([], false, false);
            }

            var list = new List<OmsActualPosition>();
            var weightAvailableCount = 0;
            var sharesAvailableCount = 0;

            foreach (var item in positionsNode.EnumerateArray())
            {
                var symbol = ReadString(item, "symbol", "ts_code", "ticker");
                if (string.IsNullOrWhiteSpace(symbol))
                {
                    continue;
                }

                var normalized = symbol.Trim().ToUpperInvariant();
                var actualShares = ReadDecimal(item, "actual_shares", "shares", "quantity", "position_qty");
                var actualWeight = ReadDecimal(item, "actual_weight", "weight", "position_weight");

                if (actualShares.HasValue)
                {
                    sharesAvailableCount++;
                }

                if (actualWeight.HasValue)
                {
                    weightAvailableCount++;
                }

                list.Add(new OmsActualPosition
                {
                    Symbol = normalized,
                    ActualShares = actualShares,
                    ActualWeight = actualWeight,
                    NormalizationStatus = string.Equals(normalized, symbol, StringComparison.Ordinal) ? "as_is" : "normalized_symbol"
                });
            }

            return (list, weightAvailableCount > 0, sharesAvailableCount > 0);
        }
        catch
        {
            return ([], false, false);
        }
    }

    private static string ReadString(JsonElement element, params string[] names)
    {
        foreach (var name in names)
        {
            if (element.TryGetProperty(name, out var node) && node.ValueKind == JsonValueKind.String)
            {
                return node.GetString() ?? string.Empty;
            }
        }

        return string.Empty;
    }

    private static decimal? ReadDecimal(JsonElement element, params string[] names)
    {
        foreach (var name in names)
        {
            if (!element.TryGetProperty(name, out var node))
            {
                continue;
            }

            if (node.ValueKind == JsonValueKind.Number && node.TryGetDecimal(out var dec))
            {
                return dec;
            }

            if (node.ValueKind == JsonValueKind.String && decimal.TryParse(node.GetString(), out var parsed))
            {
                return parsed;
            }
        }

        return null;
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

public sealed class ReconciliationSkeleton
{
    public ReconciliationSummary Evaluate(bool hasDesiredState, string desiredReleaseId, OmsSnapshot oms)
    {
        var reasons = new List<string>();

        if (!hasDesiredState)
        {
            reasons.Add("desired_state_missing");
        }

        if (!oms.ActualStateExists)
        {
            reasons.Add("actual_state_missing");
        }

        if (!oms.SummaryExists)
        {
            reasons.Add("oms_summary_missing");
        }

        string mismatch = "none";
        if (hasDesiredState && oms.ActualStateExists && !string.IsNullOrWhiteSpace(desiredReleaseId))
        {
            var actualReleaseId = oms.ActualState.ReleaseId;
            if (!string.IsNullOrWhiteSpace(actualReleaseId)
                && !string.Equals(actualReleaseId, desiredReleaseId, StringComparison.OrdinalIgnoreCase))
            {
                reasons.Add("release_id_mismatch_between_desired_and_actual");
                mismatch = $"desired={desiredReleaseId}, actual={actualReleaseId}";
            }
        }

        var canReconcile = reasons.Count == 0;
        var severity = canReconcile ? GateSeverity.Normal : GateSeverity.Warning;
        if (!hasDesiredState || !oms.ActualStateExists)
        {
            severity = GateSeverity.Blocking;
        }

        return new ReconciliationSummary
        {
            HasDesiredState = hasDesiredState,
            HasActualState = oms.ActualStateExists,
            CanReconcile = canReconcile,
            MismatchSummary = mismatch,
            Severity = severity,
            Reasons = reasons
        };
    }
}
