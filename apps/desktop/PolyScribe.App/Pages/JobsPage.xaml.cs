using Microsoft.UI.Xaml.Controls;
using PolyScribe.App.ViewModels;

namespace PolyScribe.App.Pages;

public sealed partial class JobsPage : Page
{
    public JobsPage()
    {
        ViewModel = new JobsViewModel();
        InitializeComponent();
    }

    public JobsViewModel ViewModel { get; }

    private void FilterBar_SelectionChanged(SelectorBar sender, SelectorBarSelectionChangedEventArgs args)
    {
        if (sender.SelectedItem?.Tag is string tag)
        {
            ViewModel.SetFilter(tag);
        }
    }

    private void JobList_ItemClick(object sender, ItemClickEventArgs e)
    {
        if (e.ClickedItem is JobItemViewModel item)
        {
            ViewModel.OpenJobCommand.Execute(item);
        }
    }
}
