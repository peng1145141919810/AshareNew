using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.Safety;

public sealed class SafetyGateEvaluator
{
    public SafetyDecision BuildDecision(
        ExecutionGateSnapshot gate,
        bool staleAccountTruth,
        bool hasUnfinishedOrders,
        bool allowUnfinishedOrdersReconcile)
    {
        if (!gate.Ok)
        {
            return new SafetyDecision
            {
                AllowExecution = false,
                SystemMode = "HALT",
                HaltReason = "gate_not_ok"
            };
        }

        if (!gate.ShouldExecute)
        {
            return new SafetyDecision
            {
                AllowExecution = false,
                SystemMode = "CAUTION",
                HaltReason = gate.Reason
            };
        }

        if (staleAccountTruth)
        {
            return new SafetyDecision
            {
                AllowExecution = false,
                SystemMode = "HALT",
                HaltReason = "stale_account_truth"
            };
        }

        if (hasUnfinishedOrders && !allowUnfinishedOrdersReconcile)
        {
            return new SafetyDecision
            {
                AllowExecution = false,
                SystemMode = "HALT",
                HaltReason = "unfinished_orders",
                AllowUnfinishedOrdersReconcile = false,
                UnfinishedOrdersReconcileAllowed = false
            };
        }

        return new SafetyDecision
        {
            AllowExecution = true,
            SystemMode = "NORMAL",
            HaltReason = string.Empty,
            AllowUnfinishedOrdersReconcile = allowUnfinishedOrdersReconcile,
            UnfinishedOrdersReconcileAllowed = hasUnfinishedOrders && allowUnfinishedOrdersReconcile
        };
    }
}
