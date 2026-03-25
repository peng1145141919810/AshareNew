using System.Text.Json;
using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.Governance;

public sealed class ManifestDocumentLoader
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true
    };

    public SystemManifestDocument LoadSystemManifest(string path)
    {
        return Load<SystemManifestDocument>(path);
    }

    public RunProfilesDocument LoadRunProfiles(string path)
    {
        return Load<RunProfilesDocument>(path);
    }

    private static T Load<T>(string path)
    {
        var text = File.ReadAllText(path);
        var model = JsonSerializer.Deserialize<T>(text, JsonOptions);
        if (model is null)
        {
            throw new InvalidOperationException($"Failed to deserialize manifest: {path}");
        }

        return model;
    }
}
