using CommunityToolkit.Mvvm.Messaging;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media.Animation;
using PolyScribe.App.Pages;
using PolyScribe.App.Services;
using Windows.Graphics;

namespace PolyScribe.App;

public sealed partial class MainWindow : Window
{
    private bool _suppressSelection;

    public MainWindow()
    {
        InitializeComponent();
        ExtendsContentIntoTitleBar = true;
        SetTitleBar(AppTitleBar);
        AppWindow.TitleBar.PreferredHeightOption = TitleBarHeightOption.Tall;
        AppWindow.SetIcon("Assets/AppIcon.ico");
        AppWindow.Resize(new SizeInt32(1280, 840));
        if (AppWindow.Presenter is OverlappedPresenter presenter)
        {
            presenter.PreferredMinimumWidth = 960;
            presenter.PreferredMinimumHeight = 640;
        }

        WeakReferenceMessenger.Default.Register<NavigateToJobMessage>(this, (_, message) =>
        {
            DispatcherQueue.TryEnqueue(() => NavigateToJob(message));
        });

        NavFrame.Navigated += (_, _) => AppTitleBar.IsBackButtonVisible = NavFrame.CanGoBack;
    }

    private void TitleBar_PaneToggleRequested(TitleBar sender, object args)
    {
        NavView.IsPaneOpen = !NavView.IsPaneOpen;
    }

    private void TitleBar_BackRequested(TitleBar sender, object args)
    {
        if (NavFrame.CanGoBack)
        {
            NavFrame.GoBack();
        }
    }

    private void NavView_SelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
    {
        if (_suppressSelection)
        {
            return;
        }

        if (args.IsSettingsSelected)
        {
            NavFrame.Navigate(typeof(SettingsPage), null, new EntranceNavigationTransitionInfo());
            return;
        }

        if (args.SelectedItem is NavigationViewItem { Tag: string tag })
        {
            NavigateTag(tag);
        }
    }

    private void NavigateTag(string tag)
    {
        var pageType = tag switch
        {
            "transcribe" => typeof(TranscribePage),
            "jobs" => typeof(JobsPage),
            "preview" => typeof(PreviewPage),
            _ => throw new InvalidOperationException($"未知导航项: {tag}"),
        };
        NavFrame.Navigate(pageType, null, new EntranceNavigationTransitionInfo());
    }

    private void NavigateToJob(NavigateToJobMessage message)
    {
        _suppressSelection = true;
        try
        {
            var tag = message.Preview ? "preview" : "jobs";
            foreach (var item in NavView.MenuItems.OfType<NavigationViewItem>())
            {
                if (item.Tag as string == tag)
                {
                    item.IsSelected = true;
                }
            }

            if (message.Preview)
            {
                NavFrame.Navigate(typeof(PreviewPage), message.JobId, new EntranceNavigationTransitionInfo());
            }
            else
            {
                NavFrame.Navigate(typeof(JobDetailPage), message.JobId, new SlideNavigationTransitionInfo
                {
                    Effect = SlideNavigationTransitionEffect.FromRight,
                });
            }
        }
        finally
        {
            _suppressSelection = false;
        }
    }
}
