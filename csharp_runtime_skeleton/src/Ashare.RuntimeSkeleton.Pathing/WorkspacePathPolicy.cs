namespace Ashare.RuntimeSkeleton.Pathing;

public sealed record WorkspacePathPolicy
{
    public string WorkspaceRoot { get; init; } = string.Empty;
    public string LegacyRepoRoot { get; init; } = string.Empty;
    public string ExternalDataRoot { get; init; } = string.Empty;
    public bool ProtectLegacyRepo { get; init; } = true;

    public bool IsProtectedPath(string path)
    {
        if (!ProtectLegacyRepo || string.IsNullOrWhiteSpace(path) || string.IsNullOrWhiteSpace(LegacyRepoRoot))
        {
            return false;
        }

        return Path.GetFullPath(path)
            .StartsWith(Path.GetFullPath(LegacyRepoRoot), StringComparison.OrdinalIgnoreCase);
    }
}
