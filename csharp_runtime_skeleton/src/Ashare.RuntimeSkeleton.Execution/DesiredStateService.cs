using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class DesiredStateService
{
    private readonly ReleaseContractService _releaseContractService;

    public DesiredStateService(ReleaseContractService releaseContractService)
    {
        _releaseContractService = releaseContractService;
    }

    public DesiredStateSnapshot Read(PathRegistry registry)
    {
        var release = _releaseContractService.Read(registry);
        var reasons = new List<string>();

        if (!release.IsComplete)
        {
            reasons.AddRange(release.ValidationIssues);
            return new DesiredStateSnapshot
            {
                ReleaseId = release.Manifest.ReleaseId,
                TradeDate = release.Manifest.TradeDate,
                HasDesiredState = false,
                ArtifactPath = release.TargetPositionsPath,
                RowCount = 0,
                SymbolCount = 0,
                Positions = [],
                Reasons = reasons
            };
        }

        if (!File.Exists(release.TargetPositionsPath))
        {
            reasons.Add("desired_target_positions_missing");
            return new DesiredStateSnapshot
            {
                ReleaseId = release.Manifest.ReleaseId,
                TradeDate = release.Manifest.TradeDate,
                HasDesiredState = false,
                ArtifactPath = release.TargetPositionsPath,
                Reasons = reasons
            };
        }

        try
        {
            var lines = File.ReadAllLines(release.TargetPositionsPath)
                .Where(x => !string.IsNullOrWhiteSpace(x))
                .ToArray();

            if (lines.Length <= 1)
            {
                reasons.Add("desired_target_positions_empty");
                return new DesiredStateSnapshot
                {
                    ReleaseId = release.Manifest.ReleaseId,
                    TradeDate = release.Manifest.TradeDate,
                    HasDesiredState = false,
                    ArtifactPath = release.TargetPositionsPath,
                    Reasons = reasons
                };
            }

            var header = lines[0].Split(',');
            var symbolIdx = FindColumn(header, "symbol", "ts_code", "ticker");
            var weightIdx = FindColumn(header, "target_weight", "weight", "target_pct");
            var sharesIdx = FindColumn(header, "target_shares", "shares", "target_qty");

            if (symbolIdx < 0)
            {
                reasons.Add("desired_symbol_column_missing");
                return new DesiredStateSnapshot
                {
                    ReleaseId = release.Manifest.ReleaseId,
                    TradeDate = release.Manifest.TradeDate,
                    HasDesiredState = false,
                    ArtifactPath = release.TargetPositionsPath,
                    Reasons = reasons
                };
            }

            var positions = new List<DesiredPosition>();
            var weightAvailableCount = 0;
            var sharesAvailableCount = 0;

            foreach (var row in lines.Skip(1))
            {
                var cols = row.Split(',');
                if (cols.Length <= symbolIdx)
                {
                    continue;
                }

                var rawSymbol = cols[symbolIdx].Trim();
                var symbol = NormalizeSymbol(rawSymbol);
                if (string.IsNullOrWhiteSpace(symbol))
                {
                    continue;
                }

                decimal? weight = ParseDecimal(cols, weightIdx);
                decimal? shares = ParseDecimal(cols, sharesIdx);

                if (weight.HasValue)
                {
                    weightAvailableCount++;
                }

                if (shares.HasValue)
                {
                    sharesAvailableCount++;
                }

                positions.Add(new DesiredPosition
                {
                    Symbol = symbol,
                    TargetWeight = weight,
                    TargetShares = shares,
                    SourceArtifactPath = release.TargetPositionsPath,
                    NormalizationStatus = string.Equals(rawSymbol, symbol, StringComparison.Ordinal) ? "as_is" : "normalized_symbol"
                });
            }

            var symbolCount = positions.Select(x => x.Symbol).Distinct(StringComparer.OrdinalIgnoreCase).Count();
            if (positions.Count == 0)
            {
                reasons.Add("desired_positions_parsed_empty");
            }

            return new DesiredStateSnapshot
            {
                ReleaseId = release.Manifest.ReleaseId,
                TradeDate = release.Manifest.TradeDate,
                HasDesiredState = positions.Count > 0,
                ArtifactPath = release.TargetPositionsPath,
                RowCount = positions.Count,
                SymbolCount = symbolCount,
                WeightCompareAvailable = weightAvailableCount > 0,
                SharesCompareAvailable = sharesAvailableCount > 0,
                Positions = positions,
                Reasons = reasons
            };
        }
        catch
        {
            reasons.Add("desired_target_positions_parse_failed");
            return new DesiredStateSnapshot
            {
                ReleaseId = release.Manifest.ReleaseId,
                TradeDate = release.Manifest.TradeDate,
                HasDesiredState = false,
                ArtifactPath = release.TargetPositionsPath,
                Reasons = reasons
            };
        }
    }

    private static int FindColumn(IReadOnlyList<string> header, params string[] candidates)
    {
        foreach (var candidate in candidates)
        {
            var idx = Array.FindIndex(header.ToArray(), h => string.Equals(h.Trim(), candidate, StringComparison.OrdinalIgnoreCase));
            if (idx >= 0)
            {
                return idx;
            }
        }

        return -1;
    }

    private static decimal? ParseDecimal(IReadOnlyList<string> cols, int idx)
    {
        if (idx < 0 || cols.Count <= idx)
        {
            return null;
        }

        return decimal.TryParse(cols[idx], out var parsed) ? parsed : null;
    }

    private static string NormalizeSymbol(string symbol)
    {
        if (string.IsNullOrWhiteSpace(symbol))
        {
            return string.Empty;
        }

        return symbol.Trim().ToUpperInvariant();
    }
}
