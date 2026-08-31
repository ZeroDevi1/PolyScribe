using Microsoft.UI.Xaml;

namespace PolyScribe.App;

public static class BindHelpers
{
    public static Visibility VisibleIf(bool value) =>
        value ? Visibility.Visible : Visibility.Collapsed;

    public static Visibility VisibleIf(string? value) =>
        string.IsNullOrWhiteSpace(value) ? Visibility.Collapsed : Visibility.Visible;

    public static Visibility CollapsedIf(bool value) =>
        value ? Visibility.Collapsed : Visibility.Visible;
}
