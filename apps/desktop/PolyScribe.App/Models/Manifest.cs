using System.Text.Json;

namespace PolyScribe.App.Models;

public static class JsonOptions
{
    public static readonly JsonSerializerOptions Manifest = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
    };
}

public sealed class ManifestDocument
{
    public string SchemaVersion { get; set; } = "0.1.0";
    public string JobId { get; set; } = "";
    public string Mode { get; set; } = "transcribe";
    public string Status { get; set; } = "pending";
    public string CreatedAt { get; set; } = "";
    public string? InputMode { get; set; }
    public InputRecord? Input { get; set; }
    public EnvironmentRecord? Environment { get; set; }
    public List<StageRecord> Stages { get; set; } = [];
    public List<ArtifactRecord> Artifacts { get; set; } = [];
    public List<WarningRecord> Warnings { get; set; } = [];
}

public sealed class InputRecord
{
    public string Path { get; set; } = "";
    public string? Sha256 { get; set; }
    public double? DurationSeconds { get; set; }
}

public sealed class EnvironmentRecord
{
    public string? Os { get; set; }
    public string? Gpu { get; set; }
    public string? PolyscribeCommit { get; set; }
}

public sealed class StageRecord
{
    public string StageId { get; set; } = "";
    public string? Workflow { get; set; }
    public string Status { get; set; } = "pending";
    public string? StartedAt { get; set; }
    public string? FinishedAt { get; set; }
    public double? DurationSeconds { get; set; }
    public string? ErrorType { get; set; }
    public string? LogPath { get; set; }
    public int? ExitCode { get; set; }
    public bool CacheHit { get; set; }
    public List<string> OutputArtifactIds { get; set; } = [];
}

public sealed class ArtifactRecord
{
    public string Id { get; set; } = "";
    public string Kind { get; set; } = "";
    public string Role { get; set; } = "";
    public string Path { get; set; } = "";
    public string? Sha256 { get; set; }
    public string? ProducerStage { get; set; }
    public double? Confidence { get; set; }
    public Dictionary<string, JsonElement>? Metadata { get; set; }
}

public sealed class WarningRecord
{
    public string Message { get; set; } = "";
    public string? StageId { get; set; }
    public string? At { get; set; }
}

public sealed class ChordTimeline
{
    public string SchemaVersion { get; set; } = "0.1.0";
    public string Timebase { get; set; } = "seconds";
    public List<ChordSegment> Segments { get; set; } = [];
}

public sealed class ChordSegment
{
    public double Start { get; set; }
    public double End { get; set; }
    public string Label { get; set; } = "";
    public string? RawLabel { get; set; }
    public double? Confidence { get; set; }
}

public sealed class JobEvent
{
    public string SchemaVersion { get; set; } = "0.1.0";
    public string JobId { get; set; } = "";
    public string StageId { get; set; } = "";
    public string EventType { get; set; } = "";
    public string Timestamp { get; set; } = "";
}

public sealed class MidiNote
{
    public double StartSeconds { get; init; }
    public double EndSeconds { get; init; }
    public int Pitch { get; init; }
    public int Velocity { get; init; }
}

public sealed record DoctorCheck(string Label, bool Passed, string? Hint, string? Detail)
{
    public string Glyph => Passed ? "\uE73E" : "\uE783";
}

public sealed class TargetOption : CommunityToolkit.Mvvm.ComponentModel.ObservableObject
{
    private bool _isSelected = true;

    public TargetOption(string id, string title, string description, string glyph)
    {
        Id = id;
        Title = title;
        Description = description;
        Glyph = glyph;
    }

    public string Id { get; }
    public string Title { get; }
    public string Description { get; }
    public string Glyph { get; }

    public bool IsSelected
    {
        get => _isSelected;
        set => SetProperty(ref _isSelected, value);
    }
}
