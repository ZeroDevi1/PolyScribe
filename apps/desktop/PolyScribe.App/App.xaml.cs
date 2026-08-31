using Microsoft.UI.Xaml;
using PolyScribe.App.Services;

namespace PolyScribe.App;

public partial class App : Application
{
    public App()
    {
        Settings = new AppSettings();
        Layout = new LayoutLocator(Settings);
        Jobs = new JobStore(Layout);
        Cli = new PolyscribeCli(Layout);
        Runner = new JobRunner(Cli, Layout);
        Theme = new ThemeService(Settings);
        InitializeComponent();
    }

    public static new App Current => (App)Application.Current;

    public MainWindow? MainWindow { get; private set; }

    public AppSettings Settings { get; }

    public LayoutLocator Layout { get; }

    public JobStore Jobs { get; }

    public PolyscribeCli Cli { get; }

    public JobRunner Runner { get; }

    public ThemeService Theme { get; }

    public ShellService? Shell { get; private set; }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        MainWindow = new MainWindow();
        Shell = new ShellService(MainWindow);
        Theme.Apply(MainWindow);
        MainWindow.Activate();
    }
}
