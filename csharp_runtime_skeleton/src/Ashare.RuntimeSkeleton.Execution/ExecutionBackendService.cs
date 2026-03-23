using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Pathing;
using Ashare.RuntimeSkeleton.PythonBridge;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed record ExecutionBackendResult
{
    public string BackendSelected { get; init; } = string.Empty;
    public string BackendExecutorType { get; init; } = string.Empty;
    public bool Launched { get; init; }
    public bool LaunchedByControlPlane { get; init; }
    public string ControlPlaneOwner { get; init; } = string.Empty;
    public string AuthorityOwner { get; init; } = string.Empty;
    public bool AdapterUsed { get; init; }
    public bool SubmitDisabled { get; init; }
    public bool BrokerIsolated { get; init; }
    public int? ExitCode { get; init; }
    public string NormalizedFinalStatus { get; init; } = string.Empty;
    public string FailureClassification { get; init; } = string.Empty;
    public IReadOnlyList<string> Reasons { get; init; } = [];
}

public sealed class ExecutionBackendService
{
    public async Task<ExecutionBackendResult> ExecuteAsync(
        PathRegistry registry,
        PythonRuntimeSelection runtimes,
        PythonCommandFactory commandFactory,
        RuntimePhase phase,
        string mode,
        IReadOnlyList<string> args,
        bool submitDisabled,
        bool brokerIsolated)
    {
        var request = commandFactory.BuildScriptInvocation(
            registry,
            runtimes.ResearchPython,
            registry.LaunchCanonicalPath,
            "ExecutionBackendOwner",
            args);

        var result = await new PythonProcessBridge().InvokeAsync(request);
        var final = result.ExitCode == 0 ? "succeeded" : "failed";

        return new ExecutionBackendResult
        {
            BackendSelected = mode,
            BackendExecutorType = "python_canonical_adapter",
            Launched = true,
            LaunchedByControlPlane = true,
            ControlPlaneOwner = "csharp_runtime_skeleton",
            AuthorityOwner = "ExecutionBackendService",
            AdapterUsed = true,
            SubmitDisabled = submitDisabled || phase == RuntimePhase.AfternoonShadow,
            BrokerIsolated = brokerIsolated || phase == RuntimePhase.AfternoonShadow,
            ExitCode = result.ExitCode,
            NormalizedFinalStatus = final,
            FailureClassification = result.ExitCode == 0 ? "none" : "backend_executor_failed",
            Reasons = result.ExitCode == 0 ? [] : ["backend_executor_failed"]
        };
    }
}
