using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.Governance;

public sealed class LegacyRepoProtectionPolicy
{
    private readonly WorkspacePathPolicy _policy;

    public LegacyRepoProtectionPolicy(WorkspacePathPolicy policy)
    {
        _policy = policy;
    }

    public void AssertWritablePath(string candidatePath)
    {
        if (_policy.IsProtectedPath(candidatePath))
        {
            throw new InvalidOperationException(
                $"Refusing to modify protected legacy repo path: {candidatePath}");
        }
    }
}
