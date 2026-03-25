using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.PythonBridge;

public sealed record PythonRuntimeSelection
{
    public string ResearchPython { get; init; } = string.Empty;
    public string GmtradePython { get; init; } = string.Empty;
}

public sealed class PythonRuntimeLocator
{
    public PythonRuntimeSelection Locate(SystemManifestDocument manifest)
    {
        var repoRootFromManifest = manifest.Paths.RepoRoot;
        var workspaceRepoRoot = TryMapLegacyRepoRoot(repoRootFromManifest);

        var researchPython = Environment.GetEnvironmentVariable("ASHARE_RESEARCH_PYTHON");
        var gmtradePython = Environment.GetEnvironmentVariable("ASHARE_GMTRADE_PYTHON");

        if (string.IsNullOrWhiteSpace(researchPython))
        {
            researchPython = @"C:\Users\Administrator\PyCharmMiscProject\.venv\Scripts\python.exe";
        }

        if (string.IsNullOrWhiteSpace(gmtradePython))
        {
            var gmtradeRoot = string.IsNullOrWhiteSpace(workspaceRepoRoot)
                ? @"F:\quant_data\Ashare"
                : workspaceRepoRoot;
            gmtradePython = Path.Combine(gmtradeRoot, "venvs", "gmtrade39", "Scripts", "python.exe");
        }

        return new PythonRuntimeSelection
        {
            ResearchPython = researchPython,
            GmtradePython = gmtradePython
        };
    }

    private static string TryMapLegacyRepoRoot(string repoRootFromManifest)
    {
        if (string.IsNullOrWhiteSpace(repoRootFromManifest))
        {
            return string.Empty;
        }

        return repoRootFromManifest
            .Replace(@"F:\quant_data\AshareC#", @"F:\quant_data\Ashare", StringComparison.OrdinalIgnoreCase)
            .Trim();
    }
}
