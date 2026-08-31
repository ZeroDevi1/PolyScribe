using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Media;
using PolyScribe.App.Models;
using Windows.UI;

namespace PolyScribe.App.Services;

public static class StatusPresentation
{
    public static string ToLabel(string? status) => status switch
    {
        "pending" => "等待中",
        "running" => "进行中",
        "succeeded" => "已完成",
        "failed" => "失败",
        "cancelled" => "已取消",
        _ => string.IsNullOrWhiteSpace(status) ? "未知" : status,
    };

    public static string ToGlyph(string? status) => status switch
    {
        "pending" => "\uE823",
        "running" => "\uE916",
        "succeeded" => "\uE73E",
        "failed" => "\uE783",
        "cancelled" => "\uE711",
        _ => "\uE946",
    };

    public static string ToRoleLabel(string? role) => role switch
    {
        "instrument.piano.primary" => "钢琴 MIDI",
        "vocals.lead" => "人声 MIDI",
        "vocals.harmony.simplified" => "和声 MIDI",
        "harmony.chords.timeline" => "和弦时间线",
        "harmony.chords.midi" => "和弦 MIDI",
        "audio.normalized" => "规范化音频",
        "audio.vocals" => "人声 stem",
        "audio.instrumental" => "伴奏 stem",
        "audio.lead_vocal" => "主唱 stem",
        "audio.backing_vocal" => "和声 stem",
        "transcription.full" => "完整混音 MIDI",
        _ => role ?? "产物",
    };

    public static string ToStageLabel(string? stageId) => stageId switch
    {
        "normalize" => "规范化音频",
        "muscriptor" => "MuScriptor 转录",
        "muscriptor_piano" => "钢琴条件转录",
        "piano_extract" => "抽出钢琴轨",
        "chord_export" => "导出和弦",
        "separation" => "人声分离",
        "game" => "GAME 人声 MIDI",
        "basic_pitch" => "Basic Pitch 和声",
        "export" => "导出",
        "process" => "编排",
        _ => stageId ?? "阶段",
    };

    public static string FileTitle(string? path)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            return "未命名任务";
        }

        return Path.GetFileNameWithoutExtension(path);
    }

    public static string FormatDuration(double? seconds)
    {
        if (seconds is null or < 0)
        {
            return "时长未知";
        }

        var span = TimeSpan.FromSeconds(seconds.Value);
        return span.TotalHours >= 1
            ? span.ToString(@"h\:mm\:ss")
            : span.ToString(@"m\:ss");
    }

    public static string FormatRelative(string? timestamp)
    {
        if (!DateTimeOffset.TryParse(timestamp, out var value))
        {
            return timestamp ?? "";
        }

        var delta = DateTimeOffset.Now - value.ToLocalTime();
        if (delta.TotalMinutes < 1)
        {
            return "刚刚";
        }

        if (delta.TotalHours < 1)
        {
            return $"{(int)delta.TotalMinutes} 分钟前";
        }

        if (delta.TotalDays < 1)
        {
            return $"{(int)delta.TotalHours} 小时前";
        }

        if (delta.TotalDays < 7)
        {
            return $"{(int)delta.TotalDays} 天前";
        }

        return value.ToLocalTime().ToString("yyyy-MM-dd HH:mm");
    }

    public static SolidColorBrush StatusBrush(string? status, FrameworkElement owner)
    {
        var resource = status switch
        {
            "succeeded" => "SystemFillColorSuccessBrush",
            "failed" => "SystemFillColorCriticalBrush",
            "cancelled" => "SystemFillColorCautionBrush",
            "running" => "AccentFillColorDefaultBrush",
            _ => "TextFillColorSecondaryBrush",
        };

        if (owner.Resources.TryGetValue(resource, out var local) && local is SolidColorBrush localBrush)
        {
            return localBrush;
        }

        if (Application.Current.Resources.TryGetValue(resource, out var app) && app is SolidColorBrush appBrush)
        {
            return appBrush;
        }

        return new SolidColorBrush(Color.FromArgb(255, 128, 128, 128));
    }

    public static IReadOnlyList<TargetOption> DefaultTargets() =>
    [
        new("piano", "钢琴 MIDI", "MuScriptor 完整混音后抽出钢琴轨", "\uE142"),
        new("vocal", "人声 MIDI", "分离主唱后由 GAME Medium 转录", "\uE189"),
        new("harmony", "和声 MIDI", "Backing stem 上的 Basic Pitch 多音高", "\uE8D6"),
        new("chords", "和弦", "BTC 时间线与可导入 DAW 的和弦 MIDI", "\uE8AB"),
    ];
}
