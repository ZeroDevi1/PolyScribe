using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using PolyScribe.App.Services;
using PolyScribe.App.ViewModels;
using Windows.ApplicationModel.DataTransfer;
using Windows.System;

namespace PolyScribe.App.Pages;

public sealed partial class TranscribePage : Page
{
    public TranscribePage()
    {
        ViewModel = new TranscribeViewModel();
        InitializeComponent();
        Loaded += (_, _) =>
        {
            var accelerator = new KeyboardAccelerator { Key = VirtualKey.O, Modifiers = VirtualKeyModifiers.Control };
            accelerator.Invoked += async (_, args) =>
            {
                args.Handled = true;
                await ViewModel.BrowseCommand.ExecuteAsync(null);
            };
            KeyboardAccelerators.Add(accelerator);
        };
    }

    public TranscribeViewModel ViewModel { get; }

    private async void Browse_Click(object sender, RoutedEventArgs e) =>
        await ViewModel.BrowseCommand.ExecuteAsync(null);

    private void DropZone_DragOver(object sender, DragEventArgs e)
    {
        if (e.DataView.Contains(StandardDataFormats.StorageItems))
        {
            e.AcceptedOperation = DataPackageOperation.Copy;
            e.DragUIOverride.Caption = "导入到 PolyScribe";
            DropZone.BorderBrush = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["AccentFillColorDefaultBrush"];
        }
    }

    private void DropZone_DragLeave(object sender, DragEventArgs e)
    {
        DropZone.BorderBrush = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["ControlStrokeColorDefaultBrush"];
    }

    private async void DropZone_Drop(object sender, DragEventArgs e)
    {
        DropZone.BorderBrush = (Microsoft.UI.Xaml.Media.Brush)Application.Current.Resources["ControlStrokeColorDefaultBrush"];
        if (!e.DataView.Contains(StandardDataFormats.StorageItems))
        {
            return;
        }

        var items = await e.DataView.GetStorageItemsAsync();
        var file = items.FirstOrDefault();
        if (file is not null)
        {
            ViewModel.SetSource(file.Path);
        }
    }
}
