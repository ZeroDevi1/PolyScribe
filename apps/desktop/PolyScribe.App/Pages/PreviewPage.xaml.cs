using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;
using PolyScribe.App.ViewModels;
using Windows.Media.Core;

namespace PolyScribe.App.Pages;

public sealed partial class PreviewPage : Page
{
    public PreviewPage()
    {
        ViewModel = new PreviewViewModel();
        InitializeComponent();
        ViewModel.PropertyChanged += (_, args) =>
        {
            if (args.PropertyName is nameof(PreviewViewModel.AudioPath))
            {
                BindPlayer();
            }
        };
    }

    public PreviewViewModel ViewModel { get; }

    protected override void OnNavigatedTo(NavigationEventArgs e)
    {
        if (e.Parameter is string jobId && !string.IsNullOrWhiteSpace(jobId))
        {
            ViewModel.Load(jobId);
        }

        BindPlayer();
    }

    private void BindPlayer()
    {
        if (ViewModel.AudioPath is { Length: > 0 } path && File.Exists(path))
        {
            Player.Source = MediaSource.CreateFromUri(new Uri(path));
        }
        else
        {
            Player.Source = null;
        }
    }
}
