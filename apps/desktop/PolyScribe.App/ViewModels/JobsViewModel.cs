using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using PolyScribe.App.Models;
using PolyScribe.App.Services;

namespace PolyScribe.App.ViewModels;

public sealed partial class JobItemViewModel : ObservableObject
{
    public JobItemViewModel(ManifestDocument document, string? root)
    {
        JobId = document.JobId;
        RootPath = root ?? "";
        Title = StatusPresentation.FileTitle(document.Input?.Path);
        InputPath = document.Input?.Path ?? "";
        CreatedLabel = StatusPresentation.FormatRelative(document.CreatedAt);
        DurationLabel = StatusPresentation.FormatDuration(document.Input?.DurationSeconds);
        ArtifactCount = document.Artifacts.Count;
        WarningCount = document.Warnings.Count;
        Status = document.Status;
        StatusLabel = StatusPresentation.ToLabel(document.Status);
        StatusGlyph = StatusPresentation.ToGlyph(document.Status);
        IsRunning = document.Status == "running";
        ModeLabel = document.Mode == "cover" ? "Cover" : "转录";
    }

    public string JobId { get; }
    public string RootPath { get; }
    public string Title { get; }
    public string InputPath { get; }
    public string CreatedLabel { get; }
    public string DurationLabel { get; }
    public int ArtifactCount { get; }
    public int WarningCount { get; }
    public string Status { get; }
    public string StatusLabel { get; }
    public string StatusGlyph { get; }
    public bool IsRunning { get; }
    public string ModeLabel { get; }
}

public sealed partial class JobsViewModel : ObservableObject
{
    private readonly JobStore _store = App.Current.Jobs;
    private readonly LayoutLocator _layout = App.Current.Layout;
    private IReadOnlyList<JobItemViewModel> _all = [];

    public JobsViewModel()
    {
        WeakReferenceMessenger.Default.Register<JobUpdatedMessage>(this, (_, _) => Refresh());
        WeakReferenceMessenger.Default.Register<JobStartedMessage>(this, (_, _) => Refresh());
        Refresh();
    }

    public ObservableCollection<JobItemViewModel> Jobs { get; } = [];

    [ObservableProperty]
    private string filter = "all";

    [ObservableProperty]
    private string? statusMessage;

    [ObservableProperty]
    private bool isEmpty;

    [RelayCommand]
    public void Refresh()
    {
        if (!_layout.IsReady)
        {
            StatusMessage = "尚未定位仓库，任务列表为空。";
            _all = [];
            ApplyFilter();
            return;
        }

        _all = _store.ListJobs()
            .Select(job => new JobItemViewModel(job, _store.JobRoot(job.JobId)))
            .ToList();
        StatusMessage = _all.Count == 0 ? "还没有任务。从「转录」页导入一首歌即可。" : $"{_all.Count} 个任务";
        ApplyFilter();
    }

    public void SetFilter(string value)
    {
        Filter = value;
        ApplyFilter();
    }

    [RelayCommand]
    private void OpenJobsFolder()
    {
        var directory = _layout.JobsDirectory;
        if (directory is null)
        {
            return;
        }

        Directory.CreateDirectory(directory);
        ShellService.OpenPath(directory);
    }

    [RelayCommand]
    private void OpenJob(JobItemViewModel? item)
    {
        if (item is null)
        {
            return;
        }

        WeakReferenceMessenger.Default.Send(new NavigateToJobMessage(item.JobId, Preview: false));
    }

    [RelayCommand]
    private void PreviewJob(JobItemViewModel? item)
    {
        if (item is null)
        {
            return;
        }

        WeakReferenceMessenger.Default.Send(new NavigateToJobMessage(item.JobId, Preview: true));
    }

    private void ApplyFilter()
    {
        Jobs.Clear();
        foreach (var job in _all)
        {
            if (Filter is not "all" && !string.Equals(job.Status, Filter, StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            Jobs.Add(job);
        }

        IsEmpty = Jobs.Count == 0;
    }
}

public sealed partial class StageItemViewModel : ObservableObject
{
    public StageItemViewModel(StageRecord stage)
    {
        StageId = stage.StageId;
        Title = StatusPresentation.ToStageLabel(stage.StageId);
        Workflow = stage.Workflow ?? "编排";
        Status = stage.Status;
        StatusLabel = StatusPresentation.ToLabel(stage.Status);
        StatusGlyph = StatusPresentation.ToGlyph(stage.Status);
        DurationLabel = stage.DurationSeconds is null ? (stage.Status == "running" ? "进行中" : "—") : $"{stage.DurationSeconds:0.0}s";
        IsRunning = stage.Status == "running";
        ErrorText = stage.ErrorType;
        LogPath = stage.LogPath;
        Progress = stage.Status switch
        {
            "succeeded" => 1,
            "failed" or "cancelled" => 1,
            "running" => 0.45,
            _ => 0,
        };
        IsIndeterminate = stage.Status == "running";
    }

    public string StageId { get; }
    public string Title { get; }
    public string Workflow { get; }
    public string Status { get; }
    public string StatusLabel { get; }
    public string StatusGlyph { get; }
    public string DurationLabel { get; }
    public bool IsRunning { get; }
    public string? ErrorText { get; }
    public string? LogPath { get; }
    public double Progress { get; }
    public bool IsIndeterminate { get; }
}

public sealed partial class ArtifactItemViewModel : ObservableObject
{
    public ArtifactItemViewModel(ArtifactRecord artifact)
    {
        Id = artifact.Id;
        Title = StatusPresentation.ToRoleLabel(artifact.Role);
        Kind = artifact.Kind;
        Path = artifact.Path;
        Exists = File.Exists(artifact.Path);
        ConfidenceLabel = artifact.Confidence is null ? "无数值置信度" : $"{artifact.Confidence:0.00}";
        Producer = artifact.ProducerStage ?? "";
        Subtitle = Exists ? Path : "文件不在磁盘上";
    }

    public string Id { get; }
    public string Title { get; }
    public string Kind { get; }
    public string Path { get; }
    public bool Exists { get; }
    public string ConfidenceLabel { get; }
    public string Producer { get; }
    public string Subtitle { get; }
}

public sealed partial class JobDetailViewModel : ObservableObject
{
    private readonly JobStore _store = App.Current.Jobs;
    private readonly JobRunner _runner = App.Current.Runner;

    public JobDetailViewModel(string jobId)
    {
        JobId = jobId;
        WeakReferenceMessenger.Default.Register<JobUpdatedMessage>(this, (_, message) =>
        {
            if (message.JobId == JobId)
            {
                Reload();
            }
        });
        if (!string.IsNullOrWhiteSpace(jobId))
        {
            Reload();
        }
    }

    public string JobId { get; private set; }
    public ObservableCollection<StageItemViewModel> Stages { get; } = [];
    public ObservableCollection<ArtifactItemViewModel> Artifacts { get; } = [];
    public ObservableCollection<string> Warnings { get; } = [];

    [ObservableProperty]
    private string title = "任务";

    [ObservableProperty]
    private string statusLabel = "";

    [ObservableProperty]
    private string statusGlyph = "\uE946";

    [ObservableProperty]
    private string metaLabel = "";

    [ObservableProperty]
    private string? errorMessage;

    [ObservableProperty]
    private bool isRunning;

    [ObservableProperty]
    private bool canCancel;

    [ObservableProperty]
    private bool hasWarnings;

    [ObservableProperty]
    private bool hasArtifacts;

    [ObservableProperty]
    private string? rootPath;

    [RelayCommand]
    public void Attach(string jobId)
    {
        JobId = jobId;
        Reload();
    }

    [RelayCommand]
    public void Reload()
    {
        var document = _store.Read(JobId);
        RootPath = _store.JobRoot(JobId);
        if (document is null)
        {
            Title = "任务尚未写入清单";
            StatusLabel = "等待中";
            MetaLabel = "进程已启动，正在创建任务目录。";
            IsRunning = true;
            CanCancel = _runner.RunningJobId == JobId;
            return;
        }

        Title = StatusPresentation.FileTitle(document.Input?.Path);
        StatusLabel = StatusPresentation.ToLabel(document.Status);
        StatusGlyph = StatusPresentation.ToGlyph(document.Status);
        MetaLabel = $"{StatusPresentation.FormatDuration(document.Input?.DurationSeconds)} · {StatusPresentation.FormatRelative(document.CreatedAt)}";
        IsRunning = document.Status is "running" or "pending";
        CanCancel = IsRunning && _runner.RunningJobId == JobId;
        ErrorMessage = document.Status == "failed"
            ? document.Warnings.LastOrDefault()?.Message ?? "任务失败，打开阶段日志查看详情。"
            : null;

        Stages.Clear();
        foreach (var stage in document.Stages)
        {
            Stages.Add(new StageItemViewModel(stage));
        }

        Artifacts.Clear();
        foreach (var artifact in document.Artifacts)
        {
            Artifacts.Add(new ArtifactItemViewModel(artifact));
        }

        Warnings.Clear();
        foreach (var warning in document.Warnings)
        {
            Warnings.Add(warning.Message);
        }

        HasWarnings = Warnings.Count > 0;
        HasArtifacts = Artifacts.Count > 0;
    }

    [RelayCommand]
    private void Cancel()
    {
        if (CanCancel)
        {
            _runner.Cancel();
        }
    }

    [RelayCommand]
    private void OpenOutput()
    {
        if (RootPath is not null)
        {
            ShellService.OpenPath(Path.Combine(RootPath, "output"));
        }
    }

    [RelayCommand]
    private void OpenLogs()
    {
        if (RootPath is not null)
        {
            ShellService.OpenPath(Path.Combine(RootPath, "logs"));
        }
    }

    [RelayCommand]
    private void OpenArtifact(ArtifactItemViewModel? item)
    {
        if (item is { Exists: true })
        {
            ShellService.OpenPath(item.Path);
        }
    }

    [RelayCommand]
    private void Preview()
    {
        WeakReferenceMessenger.Default.Send(new NavigateToJobMessage(JobId, Preview: true));
    }
}
