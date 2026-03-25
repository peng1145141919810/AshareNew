using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.Clock;

public static class TradeClockSchedule
{
    public static IReadOnlyList<TradeClockPhaseDefinition> DefaultPhases { get; } =
    [
        new() { Name = "research", LockName = "research", ScheduledTime = "15:05:00", TimeoutMinutes = 420 },
        new() { Name = "release", LockName = "release", ScheduledTime = "15:10:00", TimeoutMinutes = 30 },
        new() { Name = "preopen_gate", LockName = "execution", ScheduledTime = "09:20:00", TimeoutMinutes = 15 },
        new() { Name = "simulation", LockName = "simulation", ScheduledTime = "09:30:35", TimeoutMinutes = 45 },
        new() { Name = "midday_review", LockName = "midday_review", ScheduledTime = "11:35:00", TimeoutMinutes = 10 },
        new() { Name = "afternoon_execution", LockName = "afternoon_execution", ScheduledTime = "13:05:00", TimeoutMinutes = 30 },
        new() { Name = "afternoon_shadow", LockName = "afternoon_shadow", ScheduledTime = "13:15:00", TimeoutMinutes = 20 },
        new() { Name = "summary", LockName = "summary", ScheduledTime = "15:20:00", TimeoutMinutes = 20 }
    ];

    public static IReadOnlyList<ExecutionWindowDefinition> DefaultExecutionWindows { get; } =
    [
        new() { Label = "morning_primary", Start = "09:30:30", End = "10:00:00" },
        new() { Label = "afternoon_primary", Start = "13:00:00", End = "14:50:00" }
    ];
}
