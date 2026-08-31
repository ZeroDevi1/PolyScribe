using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;
using PolyScribe.App.ViewModels;

namespace PolyScribe.App.Pages;

public sealed partial class JobDetailPage : Page
{
    public JobDetailPage()
    {
        ViewModel = new JobDetailViewModel("");
        InitializeComponent();
    }

    public JobDetailViewModel ViewModel { get; private set; }

    protected override void OnNavigatedTo(NavigationEventArgs e)
    {
        if (e.Parameter is string jobId && !string.IsNullOrWhiteSpace(jobId))
        {
            ViewModel.Attach(jobId);
            Bindings.Update();
        }
    }

    private async void Cancel_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new ContentDialog
        {
            Title = "取消当前任务？",
            Content = "会结束正在运行的 worker 进程。已写入磁盘的阶段产物会保留，任务不会被标成成功。",
            PrimaryButtonText = "取消任务",
            CloseButtonText = "继续运行",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = XamlRoot,
        };
        if (await dialog.ShowAsync() == ContentDialogResult.Primary)
        {
            ViewModel.CancelCommand.Execute(null);
        }
    }

    private void ArtifactList_ItemClick(object sender, ItemClickEventArgs e)
    {
        if (e.ClickedItem is ArtifactItemViewModel item)
        {
            ViewModel.OpenArtifactCommand.Execute(item);
        }
    }
}
