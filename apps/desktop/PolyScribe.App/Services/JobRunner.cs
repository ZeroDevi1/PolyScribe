using System.Diagnostics;
using CommunityToolkit.Mvvm.Messaging;
using PolyScribe.App.Models;

namespace PolyScribe.App.Services;

public sealed record JobStartedMessage(string JobId);
public sealed record JobUpdatedMessage(string JobId);
public sealed record NavigateToJobMessage(string JobId, bool Preview);

public sealed class JobRunner
{
    private readonly PolyscribeCli _cli;
    private readonly LayoutLocator _layout;
    private readonly object _gate = new();
    private Process? _process;
    private string? _runningJobId;

    public JobRunner(PolyscribeCli cli, LayoutLocator layout)
    {
        _cli = cli;
        _layout = layout;
    }

    public bool IsRunning
    {
        get
        {
            lock (_gate)
            {
                return _process is { HasExited: false };
            }
        }
    }

    public string? RunningJobId
    {
        get
        {
            lock (_gate)
            {
                return _runningJobId;
            }
        }
    }

    public async Task<string> StartAsync(string audioPath, IReadOnlyList<string> targets, CancellationToken cancellationToken)
    {
        if (IsRunning)
        {
            throw new InvalidOperationException("已有任务正在运行。GPU 阶段默认串行，不能并行启动第二条流水线。");
        }

        if (!File.Exists(audioPath))
        {
            throw new FileNotFoundException("找不到输入音频。", audioPath);
        }

        if (targets.Count == 0)
        {
            throw new InvalidOperationException("至少选择一个产物目标。");
        }

        var jobs = _layout.JobsDirectory ?? throw new InvalidOperationException("任务目录不可用。");
        Directory.CreateDirectory(jobs);
        var jobId = Guid.NewGuid().ToString();
        var targetList = string.Join(',', targets);
        var quotedAudio = audioPath.Contains('"') ? audioPath : $"\"{audioPath}\"";
        var info = _cli.CreateProcess($"run polyscribe process {quotedAudio} --targets {targetList} --job-id {jobId}");
        var process = new Process { StartInfo = info, EnableRaisingEvents = true };
        if (!process.Start())
        {
            throw new InvalidOperationException("无法启动转录进程。");
        }

        lock (_gate)
        {
            _process = process;
            _runningJobId = jobId;
        }

        WeakReferenceMessenger.Default.Send(new JobStartedMessage(jobId));
        _ = DrainAsync(process, jobId, cancellationToken);
        return jobId;
    }

    public void Cancel()
    {
        Process? process;
        lock (_gate)
        {
            process = _process;
        }

        if (process is { HasExited: false })
        {
            process.Kill(entireProcessTree: true);
        }
    }

    private async Task DrainAsync(Process process, string jobId, CancellationToken cancellationToken)
    {
        try
        {
            var stdoutTask = process.StandardOutput.ReadToEndAsync(cancellationToken);
            var stderrTask = process.StandardError.ReadToEndAsync(cancellationToken);
            using var timer = new PeriodicTimer(TimeSpan.FromMilliseconds(400));
            while (await timer.WaitForNextTickAsync(cancellationToken))
            {
                WeakReferenceMessenger.Default.Send(new JobUpdatedMessage(jobId));
                if (process.HasExited)
                {
                    break;
                }
            }

            await process.WaitForExitAsync(cancellationToken);
            await Task.WhenAll(stdoutTask, stderrTask);
            WeakReferenceMessenger.Default.Send(new JobUpdatedMessage(jobId));
        }
        catch (OperationCanceledException)
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
            }
        }
        finally
        {
            lock (_gate)
            {
                if (ReferenceEquals(_process, process))
                {
                    _process = null;
                    _runningJobId = null;
                }
            }

            process.Dispose();
        }
    }
}
