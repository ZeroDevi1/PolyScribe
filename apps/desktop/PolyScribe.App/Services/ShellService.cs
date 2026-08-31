using System.Diagnostics;
using Microsoft.UI.Xaml;
using Windows.Storage.Pickers;
using WinRT.Interop;

namespace PolyScribe.App.Services;

public sealed class ShellService
{
    public static readonly string[] AudioExtensions =
    [
        ".wav", ".flac", ".mp3", ".m4a", ".aac", ".ogg", ".wma", ".aiff", ".aif",
        ".mp4", ".mkv", ".webm", ".mov",
    ];

    private readonly Window _window;

    public ShellService(Window window)
    {
        _window = window;
    }

    public static bool IsSupportedAudio(string path)
    {
        var extension = Path.GetExtension(path);
        return AudioExtensions.Contains(extension, StringComparer.OrdinalIgnoreCase);
    }

    public async Task<string?> PickAudioAsync()
    {
        var picker = new FileOpenPicker
        {
            SuggestedStartLocation = PickerLocationId.MusicLibrary,
            ViewMode = PickerViewMode.List,
        };
        foreach (var extension in AudioExtensions)
        {
            picker.FileTypeFilter.Add(extension);
        }

        InitializeWithWindow.Initialize(picker, WindowNative.GetWindowHandle(_window));
        var file = await picker.PickSingleFileAsync();
        return file?.Path;
    }

    public async Task<string?> PickFolderAsync()
    {
        var picker = new FolderPicker
        {
            SuggestedStartLocation = PickerLocationId.ComputerFolder,
        };
        picker.FileTypeFilter.Add("*");
        InitializeWithWindow.Initialize(picker, WindowNative.GetWindowHandle(_window));
        var folder = await picker.PickSingleFolderAsync();
        return folder?.Path;
    }

    public static void OpenPath(string path)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            return;
        }

        var info = new ProcessStartInfo
        {
            FileName = path,
            UseShellExecute = true,
        };
        Process.Start(info);
    }

    public static void RevealInExplorer(string path)
    {
        if (Directory.Exists(path))
        {
            Process.Start("explorer.exe", path);
            return;
        }

        if (File.Exists(path))
        {
            Process.Start("explorer.exe", $"/select,\"{path}\"");
        }
    }
}
