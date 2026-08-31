using Microsoft.UI.Xaml;

namespace PolyScribe.App.Services;

public sealed class ThemeService
{
    private readonly AppSettings _settings;

    public ThemeService(AppSettings settings)
    {
        _settings = settings;
    }

    public IReadOnlyList<string> Options { get; } = ["System", "Dark", "Light"];

    public ElementTheme Current => Parse(_settings.Theme);

    public void Apply(Window window)
    {
        Apply(window, Current);
    }

    public void Apply(Window window, string themeName)
    {
        _settings.Theme = themeName;
        Apply(window, Parse(themeName));
    }

    private static void Apply(Window window, ElementTheme theme)
    {
        if (window.Content is FrameworkElement root)
        {
            root.RequestedTheme = theme;
        }
    }

    public static string ToLabel(string theme) => theme switch
    {
        "Dark" => "深色",
        "Light" => "浅色",
        _ => "跟随系统",
    };

    private static ElementTheme Parse(string? theme) => theme switch
    {
        "Dark" => ElementTheme.Dark,
        "Light" => ElementTheme.Light,
        _ => ElementTheme.Default,
    };
}
