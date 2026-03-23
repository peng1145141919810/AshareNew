using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed record ShadowGuardResult
{
    public bool LaunchAllowed { get; init; }
    public bool SubmitDisabled { get; init; }
    public bool BrokerIsolated { get; init; }
    public IReadOnlyList<string> Reasons { get; init; } = [];
}

public sealed class ShadowExecutionGuardService
{
    public ShadowGuardResult Evaluate(RuntimePhase phase, IReadOnlyList<string> args)
    {
        if (phase != RuntimePhase.AfternoonShadow)
        {
            return new ShadowGuardResult { LaunchAllowed = true, SubmitDisabled = false, BrokerIsolated = false };
        }

        var reasons = new List<string>();
        var hasShadowRun = args.Contains("--shadow-run", StringComparer.OrdinalIgnoreCase);
        var namespaceValue = ReadOption(args, "--execution-namespace");
        var precisionValue = ReadOption(args, "--precision-trade");

        var brokerIsolated = !string.IsNullOrWhiteSpace(namespaceValue)
                             && (namespaceValue.Contains("shadow", StringComparison.OrdinalIgnoreCase)
                                 || namespaceValue.Contains("simulation", StringComparison.OrdinalIgnoreCase));
        var submitDisabled = hasShadowRun && string.Equals(precisionValue, "off", StringComparison.OrdinalIgnoreCase);

        if (!hasShadowRun)
        {
            reasons.Add("shadow_guard_missing_shadow_run_flag");
        }
        if (!brokerIsolated)
        {
            reasons.Add("shadow_guard_namespace_not_isolated");
        }
        if (!submitDisabled)
        {
            reasons.Add("shadow_guard_submit_not_disabled");
        }

        return new ShadowGuardResult
        {
            LaunchAllowed = reasons.Count == 0,
            SubmitDisabled = submitDisabled,
            BrokerIsolated = brokerIsolated,
            Reasons = reasons
        };
    }

    private static string ReadOption(IReadOnlyList<string> args, string key)
    {
        for (var i = 0; i < args.Count - 1; i++)
        {
            if (string.Equals(args[i], key, StringComparison.OrdinalIgnoreCase))
            {
                return args[i + 1];
            }
        }

        return string.Empty;
    }
}
