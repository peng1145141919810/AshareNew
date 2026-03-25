using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.Oms;

public sealed class OmsLedgerCatalog
{
    private readonly PathRegistry _registry;

    public OmsLedgerCatalog(PathRegistry registry)
    {
        _registry = registry;
    }

    public IReadOnlyList<OmsLedgerArtifact> GetArtifacts()
    {
        return _registry.GetOmsArtifacts();
    }
}
