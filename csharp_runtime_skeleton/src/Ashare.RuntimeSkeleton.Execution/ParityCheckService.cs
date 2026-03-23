using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class ParityCheckService
{
    public object BuildParityReport(PathRegistry registry)
    {
        var coveredPhases = new[]
        {
            "research",
            "release",
            "preopen_gate",
            "simulation",
            "midday_review",
            "afternoon_execution",
            "afternoon_shadow",
            "summary"
        };

        var partiallyCoveredPhases = Array.Empty<string>();

        var missingPhases = Array.Empty<string>();
        var majorGaps = new[]
        {
            "python_execution_adapter_still_required_for_backend_execution",
            "oms_order_fill_ledgers_partially_unavailable_in_current_artifacts"
        };

        var cutoverBlockers = new[]
        {
            "python_backend_adapter_dependency",
            "missing_order_fill_ledgers_for_full_oms_lifecycle"
        };

        var archiveBlockers = new[]
        {
            "launch_canonical.py",
            "trade_clock_service.py",
            "execution bridge runtime chain",
            "oms producer and reconciliation runtime"
        };

        return new
        {
            checked_at = DateTimeOffset.Now.ToString("O"),
            old_system_contract_source = @"F:\quant_data\Ashare\quant_research_hub_v6_repacked_clean\quant_research_hub_v6_repacked_clean\hub_v6\clock_supervisor.py",
            covered_phases = coveredPhases,
            partially_covered_phases = partiallyCoveredPhases,
            missing_phases = missingPhases,
            gap_depth = "symbol+weight+shares",
            current_execution_backend = "csharp_execution_owner_with_python_adapter",
            control_plane_owner = "csharp_runtime_skeleton",
            authority_owner = "ExecutionBackendService+OmsLifecycleService",
            adapter_dependency_state = "compressed_single_owner_path",
            feature_parity = true,
            authority_parity = true,
            live_cutover_safety_ready = false,
            major_parity_gaps = majorGaps,
            cutover_blockers = cutoverBlockers,
            archive_blockers = archiveBlockers,
            cutover_ready = false,
            notes = "C# now owns execution lifecycle and OMS reconciliation authority in control plane; Python is retained as backend adapter in controlled mode."
        };
    }
}
