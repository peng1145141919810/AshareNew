using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Governance;
using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.PythonBridge;

public sealed class PythonCommandFactory
{
    public PythonInvocationRequest BuildLaunchCanonical(
        PathRegistry registry,
        PythonRuntimeSelection runtimes,
        RuntimeSelection selection)
    {
        return new PythonInvocationRequest
        {
            Purpose = "CanonicalLaunch",
            WorkingDirectory = registry.Policy.WorkspaceRoot,
            Command = new PythonCommandSpec
            {
                EntryPointPath = registry.LaunchCanonicalPath,
                PreferredPythonPath = runtimes.ResearchPython,
                Arguments =
                [
                    registry.LaunchCanonicalPath,
                    "--profile", selection.Profile,
                    "--mode", selection.Mode
                ]
            }
        };
    }

    public PythonInvocationRequest BuildTradeClock(PathRegistry registry, PythonRuntimeSelection runtimes, string profile)
    {
        return new PythonInvocationRequest
        {
            Purpose = "TradeClockService",
            WorkingDirectory = registry.Policy.WorkspaceRoot,
            Command = new PythonCommandSpec
            {
                EntryPointPath = registry.TradeClockServicePath,
                PreferredPythonPath = runtimes.ResearchPython,
                Arguments =
                [
                    registry.TradeClockServicePath,
                    "--profile", profile
                ]
            }
        };
    }

    public PythonInvocationRequest BuildExecutionOnly(
        PathRegistry registry,
        PythonRuntimeSelection runtimes,
        string profile,
        string executionMode,
        bool precisionTradeEnabled,
        bool gateOnly)
    {
        var mode = string.IsNullOrWhiteSpace(executionMode) ? "precision" : executionMode.Trim();

        var args = new List<string>
        {
            registry.LaunchCanonicalPath,
            "--mode", "execution_only",
            "--profile", profile,
            "--execution-mode", mode,
            "--precision-trade", precisionTradeEnabled ? "on" : "off"
        };

        if (gateOnly)
        {
            args.Add("--gate-only");
        }

        return new PythonInvocationRequest
        {
            Purpose = "ExecutionOnly",
            WorkingDirectory = registry.Policy.WorkspaceRoot,
            Command = new PythonCommandSpec
            {
                EntryPointPath = registry.LaunchCanonicalPath,
                PreferredPythonPath = mode.Equals("precision", StringComparison.OrdinalIgnoreCase)
                    ? runtimes.GmtradePython
                    : runtimes.ResearchPython,
                Arguments = args
            }
        };
    }

    public PythonInvocationRequest BuildScriptInvocation(
        PathRegistry registry,
        string pythonPath,
        string entryPointPath,
        string purpose,
        IReadOnlyList<string> passthroughArgs)
    {
        var args = new List<string> { entryPointPath };
        if (passthroughArgs.Count > 0)
        {
            args.AddRange(passthroughArgs);
        }

        return new PythonInvocationRequest
        {
            Purpose = purpose,
            WorkingDirectory = registry.Policy.WorkspaceRoot,
            Command = new PythonCommandSpec
            {
                EntryPointPath = entryPointPath,
                PreferredPythonPath = pythonPath,
                Arguments = args
            }
        };
    }
}
