using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.Oms;

public sealed record OmsBoundaryMap
{
    public string DesiredStateOwner { get; init; } = "Research / V2A";
    public string ReleaseOwner { get; init; } = "Release";
    public string SafetyOwner { get; init; } = "Safety / Trade Clock";
    public string ActualStateOwner { get; init; } = "OMS";
    public string DispatchOwner { get; init; } = "Broker Bridge under OMS governance";
    public IReadOnlyList<OmsLedgerArtifact> LedgerArtifacts { get; init; } = [];

    public static OmsBoundaryMap Create(PathRegistry registry)
    {
        return new OmsBoundaryMap
        {
            LedgerArtifacts = registry.GetOmsArtifacts()
        };
    }
}
