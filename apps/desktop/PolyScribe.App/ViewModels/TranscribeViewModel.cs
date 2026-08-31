using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using PolyScribe.App.Models;
using PolyScribe.App.Services;

namespace PolyScribe.App.ViewModels;

public sealed partial class TranscribeViewModel : ObservableObject
{
    private readonly AppSettings _settings = App.Current.Settings;
    private readonly LayoutLocator _layout = App.Current.Layout;
    private readonly JobRunner _runner = App.Current.Runner;

    public TranscribeViewModel()
    {
        Targets = new ObservableCollection<TargetOption>(StatusPresentation.DefaultTargets());
        var selected = _settings.LastTargets.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        if (selected.Length > 0)
        {
            foreach (var target in Targets)
            {
                target.IsSelected = selected.Contains(target.Id, StringComparer.OrdinalIgnoreCase);
            }
        }

        foreach (var target in Targets)
        {
            target.PropertyChanged += (_, _) => StartCommand.NotifyCanExecuteChanged();
        }

        RefreshEnvironment();
    }

    public ObservableCollection<TargetOption> Targets { get; }

    [ObservableProperty]
    [NotifyCanExecuteChangedFor(nameof(StartCommand))]
    [NotifyPropertyChangedFor(nameof(HasSource))]
    [NotifyPropertyChangedFor(nameof(SourceName))]
    [NotifyPropertyChangedFor(nameof(SourceFolder))]
    private string? sourcePath;

    [ObservableProperty]
    [NotifyCanExecuteChangedFor(nameof(StartCommand))]
    private bool isBusy;

    [ObservableProperty]
    private string? errorMessage;

    [ObservableProperty]
    private string? infoMessage;

    public bool HasSource => !string.IsNullOrWhiteSpace(SourcePath) && File.Exists(SourcePath);
    public string SourceName => HasSource ? Path.GetFileName(SourcePath!) : "尚未选择音频";
    public string SourceFolder => HasSource ? Path.GetDirectoryName(SourcePath!) ?? "" : "支持 WAV、FLAC、MP3 以及常见视频音轨";
    public string EnvironmentSummary { get; private set; } = "";
    public bool RepositoryReady => _layout.IsReady;

    public void RefreshEnvironment()
    {
        var root = _layout.RepositoryRoot;
        EnvironmentSummary = root is null
            ? "未定位到仓库。打开设置指定 PolyScribe 根目录。"
            : $"仓库：{root}";
        OnPropertyChanged(nameof(EnvironmentSummary));
        OnPropertyChanged(nameof(RepositoryReady));
        StartCommand.NotifyCanExecuteChanged();
    }

    public void SetSource(string path)
    {
        if (!ShellService.IsSupportedAudio(path))
        {
            ErrorMessage = "不支持的文件类型。请选择音频或含音轨的视频。";
            return;
        }

        SourcePath = path;
        ErrorMessage = null;
        InfoMessage = null;
    }

    [RelayCommand]
    private async Task BrowseAsync()
    {
        var path = await App.Current.Shell!.PickAudioAsync();
        if (path is not null)
        {
            SetSource(path);
        }
    }

    [RelayCommand]
    private void ClearSource()
    {
        SourcePath = null;
        ErrorMessage = null;
    }

    private bool CanStart() =>
        HasSource
        && !IsBusy
        && !_runner.IsRunning
        && RepositoryReady
        && Targets.Any(target => target.IsSelected);

    [RelayCommand(CanExecute = nameof(CanStart))]
    private async Task StartAsync()
    {
        ErrorMessage = null;
        IsBusy = true;
        try
        {
            var selected = Targets.Where(target => target.IsSelected).Select(target => target.Id).ToArray();
            _settings.LastTargets = string.Join(',', selected);
            var jobId = await _runner.StartAsync(SourcePath!, selected, CancellationToken.None);
            InfoMessage = "任务已启动，正在转到进度页。";
            WeakReferenceMessenger.Default.Send(new NavigateToJobMessage(jobId, Preview: false));
        }
        catch (Exception ex)
        {
            ErrorMessage = ex.Message;
        }
        finally
        {
            IsBusy = false;
        }
    }
}
