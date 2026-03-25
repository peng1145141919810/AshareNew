using Ashare.RuntimeSkeleton.Clock;
using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Oms;
using Ashare.RuntimeSkeleton.Pathing;
using Ashare.RuntimeSkeleton.PythonBridge;
using Ashare.RuntimeSkeleton.Safety;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed record ExecutionPlan
{
    public ExecutionGateSnapshot Gate { get; init; } = new();
    public SafetyDecision Safety { get; init; } = new();
    public OmsBoundaryMap OmsBoundary { get; init; } = new();
    public IReadOnlyList<PlannedClockPhase> DailyPhases { get; init; } = [];
    public PythonInvocationRequest? ExecutionBridgeRequest { get; init; }
}

public sealed class ExecutionCoordinator
{
    private readonly SafetyGateEvaluator _safetyGateEvaluator;
    private readonly TradeClockPlanner _tradeClockPlanner;
    private readonly PythonCommandFactory _pythonCommandFactory;

    public ExecutionCoordinator(
        SafetyGateEvaluator safetyGateEvaluator,
        TradeClockPlanner tradeClockPlanner,
        PythonCommandFactory pythonCommandFactory)
    {
        _safetyGateEvaluator = safetyGateEvaluator;
        _tradeClockPlanner = tradeClockPlanner;
        _pythonCommandFactory = pythonCommandFactory;
    }

    public ExecutionPlan BuildPlan(
        PathRegistry registry,
        PythonRuntimeSelection runtimes,
        ReleaseReference release,
        string profile,
        bool gateAllowsExecution,
        bool precisionTradeEnabled,
        bool staleAccountTruth,
        bool hasUnfinishedOrders,
        bool allowUnfinishedOrdersReconcile)
    {
        var accountMode = profile.Equals("quick_test", StringComparison.OrdinalIgnoreCase)
            ? "simulation"
            : "precision";

        var gate = new ExecutionGateSnapshot
        {
            Ok = true,
            ShouldExecute = gateAllowsExecution,
            AccountMode = accountMode,
            PrecisionTradeEnabled = precisionTradeEnabled,
            Reason = gateAllowsExecution ? "eligible" : "gate_blocked",
            Release = release
        };

        var safety = _safetyGateEvaluator.BuildDecision(
            gate,
            staleAccountTruth,
            hasUnfinishedOrders,
            allowUnfinishedOrdersReconcile);

        var shanghaiTimeZone = TimeZoneInfo.FindSystemTimeZoneById("China Standard Time");
        var tradeDate = DateOnly.TryParse(release.TradeDate, out var parsedDate)
            ? parsedDate
            : DateOnly.FromDateTime(DateTime.Today);

        return new ExecutionPlan
        {
            Gate = gate,
            Safety = safety,
            OmsBoundary = OmsBoundaryMap.Create(registry),
            DailyPhases = _tradeClockPlanner.BuildDailyPlan(tradeDate, shanghaiTimeZone),
            ExecutionBridgeRequest = _pythonCommandFactory.BuildExecutionOnly(
                registry,
                runtimes,
                profile,
                accountMode,
                precisionTradeEnabled,
                gateOnly: false)
        };
    }
}
