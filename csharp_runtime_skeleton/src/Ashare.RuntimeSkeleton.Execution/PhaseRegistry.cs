using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed record PhaseDefinition
{
    public RuntimePhase Phase { get; init; }
    public string CanonicalMode { get; init; } = string.Empty;
    public IReadOnlyList<string> FixedArgs { get; init; } = [];
    public bool EnabledByDefault { get; init; } = true;
}

public static class PhaseRegistry
{
    private static readonly IReadOnlyDictionary<RuntimePhase, PhaseDefinition> Definitions =
        new Dictionary<RuntimePhase, PhaseDefinition>
        {
            [RuntimePhase.Research] = new() { Phase = RuntimePhase.Research, CanonicalMode = "research_only" },
            [RuntimePhase.Release] = new() { Phase = RuntimePhase.Release, CanonicalMode = "release_only" },
            [RuntimePhase.PreopenGate] = new() { Phase = RuntimePhase.PreopenGate, CanonicalMode = "execution_only", FixedArgs = ["--gate-only"] },
            [RuntimePhase.Simulation] = new() { Phase = RuntimePhase.Simulation, CanonicalMode = "execution_only", FixedArgs = ["--execution-mode", "simulation"] },
            [RuntimePhase.MiddayReview] = new() { Phase = RuntimePhase.MiddayReview, CanonicalMode = "midday_review_only" },
            [RuntimePhase.AfternoonExecution] = new() { Phase = RuntimePhase.AfternoonExecution, CanonicalMode = "execution_only", FixedArgs = ["--allow-unfinished-orders-reconcile", "on"] },
            [RuntimePhase.AfternoonShadow] = new() { Phase = RuntimePhase.AfternoonShadow, CanonicalMode = "execution_only", FixedArgs = ["--execution-mode", "precision", "--precision-trade", "off", "--execution-namespace", "shadow", "--shadow-run"], EnabledByDefault = true },
            [RuntimePhase.Summary] = new() { Phase = RuntimePhase.Summary, CanonicalMode = "summary_internal" },
            [RuntimePhase.Execution] = new() { Phase = RuntimePhase.Execution, CanonicalMode = "execution_only" }
        };

    public static IReadOnlyList<RuntimePhase> OrderedAutoPhases { get; } =
    [
        RuntimePhase.Research,
        RuntimePhase.Release,
        RuntimePhase.PreopenGate,
        RuntimePhase.Simulation,
        RuntimePhase.MiddayReview,
        RuntimePhase.AfternoonExecution,
        RuntimePhase.AfternoonShadow,
        RuntimePhase.Summary
    ];

    public static bool TryGet(RuntimePhase phase, out PhaseDefinition definition) => Definitions.TryGetValue(phase, out definition!);
}
