using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;
using PolyScribe.App.Models;

namespace PolyScribe.App.Services;

public sealed class PolyscribeCli
{
    private static readonly Regex CheckLine = new(@"^\[(OK|MISSING)\]\s+(.+)$", RegexOptions.Compiled);
    private readonly LayoutLocator _layout;

    public PolyscribeCli(LayoutLocator layout)
    {
        _layout = layout;
    }

    public string? FindUv()
    {
        var env = Environment.GetEnvironmentVariable("UV");
        if (!string.IsNullOrWhiteSpace(env) && File.Exists(env))
        {
            return env;
        }

        var local = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
            ".local",
            "bin",
            "uv.exe");
        if (File.Exists(local))
        {
            return local;
        }

        var path = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (var directory in path.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
        {
            var candidate = Path.Combine(directory.Trim('"'), "uv.exe");
            if (File.Exists(candidate))
            {
                return candidate;
            }
        }

        return null;
    }

    public async Task<IReadOnlyList<DoctorCheck>> RunDoctorAsync(CancellationToken cancellationToken)
    {
        var result = await RunAsync("doctor", cancellationToken);
        return ParseDoctor(result.StandardError);
    }

    public ProcessStartInfo CreateProcess(string arguments)
    {
        var uv = FindUv() ?? throw new InvalidOperationException("未找到 uv。请先安装 https://docs.astral.sh/uv/ 并确认已加入 PATH。");
        var root = _layout.RepositoryRoot ?? throw new InvalidOperationException("未找到 PolyScribe 仓库。请在设置中指定 POLYSCRIBE_ROOT。");
        var info = new ProcessStartInfo
        {
            FileName = uv,
            Arguments = arguments,
            WorkingDirectory = root,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
        };
        info.Environment["POLYSCRIBE_ROOT"] = root;
        info.Environment["PYTHONUTF8"] = "1";
        info.Environment["PYTHONIOENCODING"] = "utf-8";
        var jobs = _layout.JobsDirectory;
        if (jobs is not null)
        {
            info.Environment["POLYSCRIBE_JOBS"] = jobs;
        }

        return info;
    }

    public async Task<(int ExitCode, string StandardOutput, string StandardError)> RunAsync(
        string arguments,
        CancellationToken cancellationToken)
    {
        using var process = new Process { StartInfo = CreateProcess($"run polyscribe {arguments}") };
        if (!process.Start())
        {
            throw new InvalidOperationException("无法启动 uv。");
        }

        var stdout = process.StandardOutput.ReadToEndAsync(cancellationToken);
        var stderr = process.StandardError.ReadToEndAsync(cancellationToken);
        await process.WaitForExitAsync(cancellationToken);
        return (process.ExitCode, await stdout, await stderr);
    }

    public static IReadOnlyList<DoctorCheck> ParseDoctor(string stderr)
    {
        var checks = new List<DoctorCheck>();
        string? pendingHint = null;
        string? pendingDetail = null;
        DoctorCheck? last = null;

        void Flush()
        {
            if (last is null)
            {
                return;
            }

            checks.Add(last with { Hint = pendingHint, Detail = pendingDetail });
            last = null;
            pendingHint = null;
            pendingDetail = null;
        }

        foreach (var raw in stderr.Split(['\r', '\n'], StringSplitOptions.RemoveEmptyEntries))
        {
            var line = raw.TrimEnd();
            var match = CheckLine.Match(line);
            if (match.Success)
            {
                Flush();
                last = new DoctorCheck(match.Groups[2].Value, match.Groups[1].Value == "OK", null, null);
                continue;
            }

            if (last is not null && line.StartsWith("       ", StringComparison.Ordinal))
            {
                var extra = line.Trim();
                if (last.Passed)
                {
                    pendingDetail = extra;
                }
                else
                {
                    pendingHint = extra;
                }
            }
        }

        Flush();
        return checks;
    }
}
