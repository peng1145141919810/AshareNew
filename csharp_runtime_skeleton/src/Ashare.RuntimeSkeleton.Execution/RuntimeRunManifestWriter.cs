using System.Text.Json;
using Ashare.RuntimeSkeleton.Contracts;
using Ashare.RuntimeSkeleton.Pathing;

namespace Ashare.RuntimeSkeleton.Execution;

public sealed class RuntimeRunManifestWriter
{
    public string Write(PathRegistry registry, string action, object payload)
    {
        var io = RuntimeIoPaths.Build(registry);
        Directory.CreateDirectory(io.RunManifestsRoot);
        var runId = $"{DateTime.Now:yyyyMMdd_HHmmss}_{action}";
        var path = Path.Combine(io.RunManifestsRoot, $"{runId}.json");
        var doc = new
        {
            run_id = runId,
            action,
            timestamp = DateTimeOffset.Now.ToString("O"),
            payload
        };

        File.WriteAllText(path, JsonSerializer.Serialize(doc, new JsonSerializerOptions { WriteIndented = true }));
        return path;
    }
}
