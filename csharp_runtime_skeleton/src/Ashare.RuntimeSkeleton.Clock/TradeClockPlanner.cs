namespace Ashare.RuntimeSkeleton.Clock;

public sealed record PlannedClockPhase
{
    public string Name { get; init; } = string.Empty;
    public DateTime ScheduledAt { get; init; }
    public int TimeoutMinutes { get; init; }
}

public sealed class TradeClockPlanner
{
    public IReadOnlyList<PlannedClockPhase> BuildDailyPlan(DateOnly tradeDate, TimeZoneInfo timeZone)
    {
        return TradeClockSchedule.DefaultPhases
            .Select(phase => new PlannedClockPhase
            {
                Name = phase.Name,
                ScheduledAt = BuildLocalDateTime(tradeDate, phase.ScheduledTime, timeZone),
                TimeoutMinutes = phase.TimeoutMinutes
            })
            .OrderBy(phase => phase.ScheduledAt)
            .ToArray();
    }

    private static DateTime BuildLocalDateTime(DateOnly date, string timeText, TimeZoneInfo timeZone)
    {
        var time = TimeOnly.Parse(timeText);
        var local = date.ToDateTime(time, DateTimeKind.Unspecified);
        return TimeZoneInfo.ConvertTime(local, timeZone);
    }
}
