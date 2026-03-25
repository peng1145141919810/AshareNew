namespace Ashare.RuntimeSkeleton.Pathing;

public sealed record RuntimeIoPaths
{
    public string OutputRoot { get; init; } = string.Empty;
    public string RuntimeRoot { get; init; } = string.Empty;
    public string PhaseRunsRoot { get; init; } = string.Empty;
    public string RunManifestsRoot { get; init; } = string.Empty;
    public string GuardedRunResultPath { get; init; } = string.Empty;
    public string ClockHostResultPath { get; init; } = string.Empty;
    public string ReconciliationResultPath { get; init; } = string.Empty;

    public static RuntimeIoPaths Build(PathRegistry registry)
    {
        var outputRoot = Path.Combine(registry.Policy.WorkspaceRoot, "csharp_runtime_skeleton", "outputs");
        var runtimeRoot = Path.Combine(outputRoot, "runtime");
        return new RuntimeIoPaths
        {
            OutputRoot = outputRoot,
            RuntimeRoot = runtimeRoot,
            PhaseRunsRoot = Path.Combine(runtimeRoot, "phase_runs"),
            RunManifestsRoot = Path.Combine(runtimeRoot, "run_manifests"),
            GuardedRunResultPath = Path.Combine(runtimeRoot, "guarded_run_result.json"),
            ClockHostResultPath = Path.Combine(runtimeRoot, "clock_host_result.json"),
            ReconciliationResultPath = Path.Combine(runtimeRoot, "reconciliation_result.json")
        };
    }
}
