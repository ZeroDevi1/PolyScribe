using Microsoft.UI.Xaml.Controls;
using PolyScribe.App.ViewModels;

namespace PolyScribe.App.Pages;

public sealed partial class SettingsPage : Page
{
    public SettingsPage()
    {
        ViewModel = new SettingsViewModel();
        InitializeComponent();
    }

    public SettingsViewModel ViewModel { get; }
}
