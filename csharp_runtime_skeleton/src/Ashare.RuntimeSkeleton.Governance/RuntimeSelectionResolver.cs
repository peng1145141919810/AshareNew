using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.Governance;

public sealed record RuntimeSelection
{
    public string Mode { get; init; } = string.Empty;
    public string Profile { get; init; } = string.Empty;
}

public sealed class RuntimeSelectionResolver
{
    public RuntimeSelection Resolve(RunProfilesDocument profiles, string? explicitMode, string? explicitProfile)
    {
        var profile = string.IsNullOrWhiteSpace(explicitProfile)
            ? profiles.DefaultProfile
            : explicitProfile.Trim();

        if (!profiles.AllowedProfiles.TryGetValue(profile, out var profileDefinition))
        {
            throw new InvalidOperationException($"Unsupported profile: {profile}");
        }

        var mode = string.IsNullOrWhiteSpace(explicitMode)
            ? profileDefinition.ModeDefault
            : explicitMode.Trim();

        if (!profiles.AllowedModes.Contains(mode, StringComparer.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException($"Unsupported mode: {mode}");
        }

        return new RuntimeSelection
        {
            Mode = mode,
            Profile = profile
        };
    }
}
