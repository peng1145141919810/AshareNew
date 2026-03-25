using System.Diagnostics;
using Ashare.RuntimeSkeleton.Contracts;

namespace Ashare.RuntimeSkeleton.PythonBridge;

public sealed class PythonProcessBridge
{
    public async Task<PythonInvocationResult> InvokeAsync(
        PythonInvocationRequest request,
        CancellationToken cancellationToken = default)
    {
        var startInfo = new ProcessStartInfo
        {
            FileName = request.Command.PreferredPythonPath,
            WorkingDirectory = request.WorkingDirectory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false
        };

        foreach (var argument in request.Command.Arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        using var process = new Process { StartInfo = startInfo };
        process.Start();

        var stdOutTask = process.StandardOutput.ReadToEndAsync(cancellationToken);
        var stdErrTask = process.StandardError.ReadToEndAsync(cancellationToken);
        await process.WaitForExitAsync(cancellationToken);

        return new PythonInvocationResult
        {
            ExitCode = process.ExitCode,
            StandardOutput = await stdOutTask,
            StandardError = await stdErrTask
        };
    }
}
