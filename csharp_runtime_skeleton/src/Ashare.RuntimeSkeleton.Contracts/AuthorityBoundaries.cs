namespace Ashare.RuntimeSkeleton.Contracts;

public sealed record AuthorityRoleDefinition
{
    public string RoleName { get; init; } = string.Empty;
    public string Owns { get; init; } = string.Empty;
    public string MustNotOwn { get; init; } = string.Empty;
}

public static class AuthorityBoundaries
{
    public static IReadOnlyList<AuthorityRoleDefinition> Default { get; } =
    [
        new()
        {
            RoleName = "Research",
            Owns = "Hypotheses, rankings, desired target weights, desired lifecycle suggestions, V6 and V5 research outputs.",
            MustNotOwn = "Broker, account, order, fill, and actual-state truth."
        },
        new()
        {
            RoleName = "Release",
            Owns = "Frozen execution contract for a trade date and release identifier.",
            MustNotOwn = "Broker feedback, OMS actual-state truth, and lifecycle truth."
        },
        new()
        {
            RoleName = "Safety",
            Owns = "Permission to attempt execution, execution gates, fail-closed system state, and override evaluation.",
            MustNotOwn = "Broker/account truth or research ranking truth."
        },
        new()
        {
            RoleName = "OMS",
            Owns = "Desired-vs-actual reconciliation, account snapshots, order/fill ledgers, intent lifecycle, and actual-state truth.",
            MustNotOwn = "Research ranking generation or global safety authority."
        },
        new()
        {
            RoleName = "Broker Dispatch",
            Owns = "Order submission and broker reply transport under OMS governance.",
            MustNotOwn = "Portfolio lifecycle truth or release authority."
        }
    ];
}
