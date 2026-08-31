using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Mvvm.Messaging;
using PolyScribe.App.Models;
using PolyScribe.App.Services;

namespace PolyScribe.App.ViewModels;

public sealed partial class PreviewTrackViewModel : ObservableObject
{
    public PreviewTrackViewModel(string id, string title, string? midiPath)
    {
        Id = id;
        Title = title;
        MidiPath = midiPath;
        Available = midiPath is not null && File.Exists(midiPath);
    }

    public string Id { get; }
    public string Title { get; }
    public string? MidiPath { get; }
    public bool Available { get; }
}

public sealed partial class PreviewViewModel : ObservableObject
{
    private readonly JobStore _store = App.Current.Jobs;

    public PreviewViewModel()
    {
        WeakReferenceMessenger.Default.Register<NavigateToJobMessage>(this, (_, message) =>
        {
            if (message.Preview || JobId is null)
            {
                Load(message.JobId);
            }
        });
        WeakReferenceMessenger.Default.Register<JobUpdatedMessage>(this, (_, message) =>
        {
            if (message.JobId == JobId)
            {
                Load(JobId);
            }
        });
    }

    public ObservableCollection<PreviewTrackViewModel> Tracks { get; } = [];
    public ObservableCollection<ChordSegment> Chords { get; } = [];

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(HasJob))]
    private string? jobId;

    [ObservableProperty]
    private string title = "选择一个任务以预览";

    [ObservableProperty]
    private string subtitle = "波形来自规范化 WAV，钢琴卷帘来自产物 MIDI。";

    [ObservableProperty]
    private string? audioPath;

    [ObservableProperty]
    private string? emptyMessage = "还没有可预览的任务。先完成一次转录，或从任务库打开。";

    [ObservableProperty]
    private PreviewTrackViewModel? selectedTrack;

    [ObservableProperty]
    private IReadOnlyList<MidiNote> notes = [];

    [ObservableProperty]
    private float[] peaks = [];

    [ObservableProperty]
    private double durationSeconds;

    public bool HasJob => !string.IsNullOrWhiteSpace(JobId);

    partial void OnSelectedTrackChanged(PreviewTrackViewModel? value)
    {
        Notes = value is { Available: true, MidiPath: not null }
            ? PreviewData.ReadMidiNotes(value.MidiPath)
            : [];
    }

    [RelayCommand]
    public void Load(string jobId)
    {
        JobId = jobId;
        var document = _store.Read(jobId);
        var root = _store.JobRoot(jobId);
        if (document is null || root is null)
        {
            EmptyMessage = "任务清单还不存在，稍后再打开预览。";
            return;
        }

        Title = StatusPresentation.FileTitle(document.Input?.Path);
        Subtitle = $"{StatusPresentation.ToLabel(document.Status)} · {StatusPresentation.FormatDuration(document.Input?.DurationSeconds)}";
        DurationSeconds = document.Input?.DurationSeconds ?? 0;
        AudioPath = PreviewData.FirstExisting(
            Path.Combine(root, "stages", "normalize", "audio.wav"),
            document.Input?.Path);
        EmptyMessage = null;

        try
        {
            Peaks = AudioPath is not null && AudioPath.EndsWith(".wav", StringComparison.OrdinalIgnoreCase)
                ? PreviewData.ReadWaveformPeaks(AudioPath)
                : [];
        }
        catch (Exception ex)
        {
            Peaks = [];
            EmptyMessage = $"无法读取波形：{ex.Message}";
        }

        Tracks.Clear();
        AddTrack("piano", "钢琴", Path.Combine(root, "output", "instruments", "piano.mid"));
        AddTrack("vocal", "人声", Path.Combine(root, "output", "vocals", "vocal.mid"));
        AddTrack("harmony", "和声", Path.Combine(root, "output", "vocals", "harmony.mid"));
        AddTrack("chords", "和弦", Path.Combine(root, "output", "harmony", "chords.mid"));
        SelectedTrack = Tracks.FirstOrDefault(track => track.Available) ?? Tracks.FirstOrDefault();

        Chords.Clear();
        var chords = PreviewData.ReadChords(Path.Combine(root, "output", "harmony", "chords.json"));
        if (chords is not null)
        {
            foreach (var segment in chords.Segments)
            {
                Chords.Add(segment);
            }
        }
    }

    private void AddTrack(string id, string title, string path) =>
        Tracks.Add(new PreviewTrackViewModel(id, title, File.Exists(path) ? path : null));
}
