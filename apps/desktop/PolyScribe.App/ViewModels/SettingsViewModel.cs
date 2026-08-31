using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PolyScribe.App.Models;
using PolyScribe.App.Services;

namespace PolyScribe.App.ViewModels;

public sealed partial class ThemeChoice
{
    public ThemeChoice(string id, string label)
    {
        Id = id;
        Label = label;
    }

    public string Id { get; }
    public string Label { get; }
}

public sealed partial class SettingsViewModel : ObservableObject
{
    private readonly AppSettings _settings = App.Current.Settings;
    private readonly LayoutLocator _layout = App.Current.Layout;
    private readonly ThemeService _theme = App.Current.Theme;
    private readonly PolyscribeCli _cli = App.Current.Cli;

    public SettingsViewModel()
    {
        Themes =
        [
            new ThemeChoice("System", "跟随系统"),
            new ThemeChoice("Dark", "深色"),
            new ThemeChoice("Light", "浅色"),
        ];
        SelectedTheme = Themes.First(item => item.Id == _settings.Theme);
        RefreshPaths();
    }

    public ObservableCollection<ThemeChoice> Themes { get; }
    public ObservableCollection<DoctorCheck> DoctorChecks { get; } = [];

    [ObservableProperty]
    private ThemeChoice selectedTheme = null!;

    [ObservableProperty]
    private string? repositoryRoot;

    [ObservableProperty]
    private string? jobsDirectory;

    [ObservableProperty]
    private string uvPath = "未找到";

    [ObservableProperty]
    private string? doctorSummary;

    [ObservableProperty]
    private bool isDoctorBusy;

    [ObservableProperty]
    private bool doctorHasIssues;

    public string VersionLabel => "PolyScribe 0.1.0 · WinUI 3 · Windows App SDK 2.4";

    partial void OnSelectedThemeChanged(ThemeChoice value)
    {
        if (App.Current.MainWindow is { } window)
        {
            _theme.Apply(window, value.Id);
        }
    }

    public void RefreshPaths()
    {
        RepositoryRoot = _layout.RepositoryRoot ?? "未找到。请选择包含 pyproject.toml 的仓库根目录。";
        JobsDirectory = _layout.JobsDirectory ?? "跟随仓库 /jobs";
        UvPath = _cli.FindUv() ?? "未找到 uv.exe";
    }

    [RelayCommand]
    private async Task PickRepositoryAsync()
    {
        var path = await App.Current.Shell!.PickFolderAsync();
        if (path is null)
        {
            return;
        }

        if (!LayoutLocator.IsRepository(path))
        {
            DoctorSummary = "所选文件夹不是 PolyScribe 仓库（缺少 name = \"polyscribe\" 的 pyproject.toml）。";
            return;
        }

        _settings.RepositoryRoot = path;
        RefreshPaths();
    }

    [RelayCommand]
    private async Task PickJobsAsync()
    {
        var path = await App.Current.Shell!.PickFolderAsync();
        if (path is null)
        {
            return;
        }

        _settings.JobsDirectory = path;
        RefreshPaths();
    }

    [RelayCommand]
    private void ResetJobs()
    {
        _settings.JobsDirectory = null;
        RefreshPaths();
    }

    [RelayCommand]
    private async Task RunDoctorAsync()
    {
        IsDoctorBusy = true;
        DoctorSummary = "正在运行 polyscribe doctor…";
        try
        {
            var checks = await _cli.RunDoctorAsync(CancellationToken.None);
            DoctorChecks.Clear();
            foreach (var check in checks)
            {
                DoctorChecks.Add(check);
            }

            var missing = checks.Count(item => !item.Passed);
            DoctorHasIssues = missing > 0;
            DoctorSummary = missing == 0
                ? "诊断通过。脚本环境已就绪。"
                : $"有 {missing} 项缺失。GUI 不会静默补齐，请按提示运行 bootstrap。";
        }
        catch (Exception ex)
        {
            DoctorHasIssues = true;
            DoctorSummary = ex.Message;
        }
        finally
        {
            IsDoctorBusy = false;
        }
    }
}
