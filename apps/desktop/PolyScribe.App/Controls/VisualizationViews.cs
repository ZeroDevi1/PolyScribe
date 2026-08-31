using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Shapes;
using PolyScribe.App.Models;

namespace PolyScribe.App.Controls;

public sealed class WaveformView : Canvas
{
    public static readonly DependencyProperty PeaksProperty = DependencyProperty.Register(
        nameof(Peaks),
        typeof(float[]),
        typeof(WaveformView),
        new PropertyMetadata(null, OnChanged));

    public float[]? Peaks
    {
        get => (float[]?)GetValue(PeaksProperty);
        set => SetValue(PeaksProperty, value);
    }

    public WaveformView()
    {
        SizeChanged += (_, _) => Redraw();
        HorizontalAlignment = HorizontalAlignment.Stretch;
        MinHeight = 96;
    }

    private static void OnChanged(DependencyObject d, DependencyPropertyChangedEventArgs e) =>
        ((WaveformView)d).Redraw();

    private void Redraw()
    {
        Children.Clear();
        var peaks = Peaks;
        if (peaks is null || peaks.Length == 0 || ActualWidth <= 0 || ActualHeight <= 0)
        {
            return;
        }

        var brush = (Brush)Application.Current.Resources["AccentFillColorDefaultBrush"];
        var midline = ActualHeight / 2;
        var points = new PointCollection();
        var count = peaks.Length;
        for (var i = 0; i < count; i++)
        {
            var x = (float)(i / (double)Math.Max(1, count - 1) * ActualWidth);
            var y = (float)(midline - (peaks[i] * midline * 0.92));
            points.Add(new Windows.Foundation.Point(x, y));
        }

        for (var i = count - 1; i >= 0; i--)
        {
            var x = (float)(i / (double)Math.Max(1, count - 1) * ActualWidth);
            var y = (float)(midline + (peaks[i] * midline * 0.92));
            points.Add(new Windows.Foundation.Point(x, y));
        }

        Children.Add(new Polygon
        {
            Points = points,
            Fill = brush,
            Opacity = 0.55,
        });
    }
}

public sealed class PianoRollView : Canvas
{
    public static readonly DependencyProperty NotesProperty = DependencyProperty.Register(
        nameof(Notes),
        typeof(IReadOnlyList<MidiNote>),
        typeof(PianoRollView),
        new PropertyMetadata(null, OnChanged));

    public static readonly DependencyProperty DurationProperty = DependencyProperty.Register(
        nameof(Duration),
        typeof(double),
        typeof(PianoRollView),
        new PropertyMetadata(0d, OnChanged));

    public IReadOnlyList<MidiNote>? Notes
    {
        get => (IReadOnlyList<MidiNote>?)GetValue(NotesProperty);
        set => SetValue(NotesProperty, value);
    }

    public double Duration
    {
        get => (double)GetValue(DurationProperty);
        set => SetValue(DurationProperty, value);
    }

    public PianoRollView()
    {
        SizeChanged += (_, _) => Redraw();
        MinHeight = 220;
        HorizontalAlignment = HorizontalAlignment.Stretch;
    }

    private static void OnChanged(DependencyObject d, DependencyPropertyChangedEventArgs e) =>
        ((PianoRollView)d).Redraw();

    private void Redraw()
    {
        Children.Clear();
        if (ActualWidth <= 0 || ActualHeight <= 0)
        {
            return;
        }

        var notes = Notes ?? [];
        var minPitch = notes.Count == 0 ? 36 : Math.Max(0, notes.Min(note => note.Pitch) - 2);
        var maxPitch = notes.Count == 0 ? 84 : Math.Min(127, notes.Max(note => note.Pitch) + 2);
        var pitchSpan = Math.Max(1, maxPitch - minPitch);
        var duration = Duration > 0 ? Duration : Math.Max(1, notes.Count == 0 ? 1 : notes.Max(note => note.EndSeconds));
        var gridBrush = (Brush)Application.Current.Resources["DividerStrokeColorDefaultBrush"];
        var noteBrush = (Brush)Application.Current.Resources["AccentFillColorDefaultBrush"];
        var laneBrush = Application.Current.Resources["CardBackgroundFillColorSecondaryBrush"] as Brush;
        var laneHeight = ActualHeight / pitchSpan;

        for (var pitch = minPitch; pitch <= maxPitch; pitch++)
        {
            var y = (maxPitch - pitch) / (double)pitchSpan * ActualHeight;
            if (IsBlackKey(pitch) && laneBrush is not null)
            {
                var lane = new Rectangle
                {
                    Width = ActualWidth,
                    Height = laneHeight,
                    Fill = laneBrush,
                    Opacity = 0.35,
                };
                SetTop(lane, y);
                Children.Add(lane);
            }

            Children.Add(new Line
            {
                X1 = 0,
                X2 = ActualWidth,
                Y1 = y,
                Y2 = y,
                Stroke = gridBrush,
                StrokeThickness = 1,
                Opacity = 0.4,
            });
        }

        foreach (var note in notes.Take(2500))
        {
            var x = note.StartSeconds / duration * ActualWidth;
            var width = Math.Max(2, (note.EndSeconds - note.StartSeconds) / duration * ActualWidth);
            var y = (maxPitch - note.Pitch) / (double)pitchSpan * ActualHeight;
            var height = Math.Max(3, laneHeight - 1);
            var rect = new Rectangle
            {
                Width = width,
                Height = height,
                Fill = noteBrush,
                Opacity = 0.35 + (note.Velocity / 127d * 0.55),
                RadiusX = 1,
                RadiusY = 1,
            };
            SetLeft(rect, x);
            SetTop(rect, y);
            Children.Add(rect);
        }
    }

    private static bool IsBlackKey(int pitch)
    {
        var pc = pitch % 12;
        return pc is 1 or 3 or 6 or 8 or 10;
    }
}
