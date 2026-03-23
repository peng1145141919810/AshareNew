using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class TickPhaseSelector
{
    public PhaseSelection SelectAuto(UnifiedRuntimeState state)
    {
        var due = ParsePhaseName(state.ClockPhase);
        if (due != RuntimePhase.None)
        {
            if (due == RuntimePhase.AfternoonShadow && !PhaseRegistry.TryGet(due, out var shadowDef))
            {
                return new PhaseSelection { Phase = RuntimePhase.None, Reason = "shadow_phase_not_registered", Reasons = ["shadow_phase_not_registered"] };
            }

            if (due == RuntimePhase.AfternoonShadow && PhaseRegistry.TryGet(due, out var def) && !def.EnabledByDefault)
            {
                return new PhaseSelection
                {
                    Phase = RuntimePhase.Summary,
                    Reason = "shadow_disabled_default_fallback_to_summary",
                    Reasons = ["afternoon_shadow_disabled_default"]
                };
            }

            return new PhaseSelection
            {
                Phase = due,
                Reason = "clock_due_phase",
                Reasons = string.IsNullOrWhiteSpace(state.ClockPhase) ? [] : [$"clock_due:{state.ClockPhase}"]
            };
        }

        if (state.ReleasePointerExists && state.ReleaseManifestExists && state.AllowExecution)
        {
            return new PhaseSelection
            {
                Phase = RuntimePhase.Execution,
                Reason = "release_ready_and_gate_open",
                Reasons = []
            };
        }

        if (state.ReleasePointerExists && state.ReleaseManifestExists)
        {
            return new PhaseSelection
            {
                Phase = RuntimePhase.Release,
                Reason = "release_refresh_needed_or_gate_closed",
                Reasons = state.BlockingReasons
            };
        }

        if (!state.ReleasePointerExists || !state.ReleaseManifestExists)
        {
            return new PhaseSelection
            {
                Phase = RuntimePhase.Research,
                Reason = "build_or_refresh_release_from_research",
                Reasons = ["release_not_ready"]
            };
        }

        return new PhaseSelection
        {
            Phase = RuntimePhase.None,
            Reason = "no_phase_selected",
            Reasons = ["no_phase_selected"]
        };
    }

    public PhaseSelection SelectManual(string phase)
    {
        var parsed = ParsePhaseName(phase);
        if (parsed != RuntimePhase.None)
        {
            return new PhaseSelection { Phase = parsed, Reason = "manual" };
        }

        return new PhaseSelection
        {
            Phase = RuntimePhase.None,
            Reason = "unsupported_phase",
            Reasons = ["unsupported_phase"]
        };
    }

    private static RuntimePhase ParsePhaseName(string phase)
    {
        return phase.Trim().ToLowerInvariant() switch
        {
            "research" => RuntimePhase.Research,
            "release" => RuntimePhase.Release,
            "preopen_gate" => RuntimePhase.PreopenGate,
            "simulation" => RuntimePhase.Simulation,
            "midday_review" => RuntimePhase.MiddayReview,
            "afternoon_execution" => RuntimePhase.AfternoonExecution,
            "afternoon_shadow" => RuntimePhase.AfternoonShadow,
            "summary" => RuntimePhase.Summary,
            "execution" => RuntimePhase.Execution,
            _ => RuntimePhase.None
        };
    }
}
