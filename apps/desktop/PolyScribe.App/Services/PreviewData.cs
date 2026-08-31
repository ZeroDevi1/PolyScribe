using System.Buffers.Binary;
using System.Text;
using System.Text.Json;
using Melanchall.DryWetMidi.Core;
using Melanchall.DryWetMidi.Interaction;
using PolyScribe.App.Models;

namespace PolyScribe.App.Services;

public static class PreviewData
{
    public static float[] ReadWaveformPeaks(string wavPath, int bucketCount = 720)
    {
        using var stream = File.OpenRead(wavPath);
        using var reader = new BinaryReader(stream, Encoding.ASCII, leaveOpen: true);
        if (ReadFourCc(reader) != "RIFF")
        {
            throw new InvalidDataException("不是 PCM WAV。");
        }

        reader.ReadInt32();
        if (ReadFourCc(reader) != "WAVE")
        {
            throw new InvalidDataException("不是 WAVE 文件。");
        }

        short channels = 0;
        short bits = 0;
        byte[]? data = null;
        while (stream.Position + 8 <= stream.Length)
        {
            var chunkId = ReadFourCc(reader);
            var chunkSize = reader.ReadInt32();
            var next = stream.Position + chunkSize;
            if (chunkId == "fmt ")
            {
                reader.ReadInt16();
                channels = reader.ReadInt16();
                reader.ReadInt32();
                reader.ReadInt32();
                reader.ReadInt16();
                bits = reader.ReadInt16();
            }
            else if (chunkId == "data")
            {
                data = reader.ReadBytes(chunkSize);
                break;
            }

            stream.Position = next + (chunkSize % 2);
        }

        if (data is null || channels <= 0 || bits != 16)
        {
            throw new InvalidDataException("仅支持 16-bit PCM WAV。");
        }

        var sampleCount = data.Length / 2 / channels;
        var peaks = new float[bucketCount];
        var samplesPerBucket = Math.Max(1, sampleCount / bucketCount);
        for (var bucket = 0; bucket < bucketCount; bucket++)
        {
            var start = bucket * samplesPerBucket;
            var end = Math.Min(sampleCount, start + samplesPerBucket);
            var peak = 0f;
            for (var sample = start; sample < end; sample++)
            {
                var offset = sample * channels * 2;
                var value = BinaryPrimitives.ReadInt16LittleEndian(data.AsSpan(offset, 2));
                peak = Math.Max(peak, Math.Abs(value / 32768f));
            }

            peaks[bucket] = peak;
        }

        return peaks;
    }

    public static IReadOnlyList<MidiNote> ReadMidiNotes(string midiPath)
    {
        var file = MidiFile.Read(midiPath);
        var tempoMap = file.GetTempoMap();
        return file.GetNotes()
            .Select(note =>
            {
                var start = note.TimeAs<MetricTimeSpan>(tempoMap);
                var length = note.LengthAs<MetricTimeSpan>(tempoMap);
                var startSeconds = start.TotalMicroseconds / 1_000_000d;
                var endSeconds = startSeconds + (length.TotalMicroseconds / 1_000_000d);
                return new MidiNote
                {
                    StartSeconds = startSeconds,
                    EndSeconds = endSeconds,
                    Pitch = note.NoteNumber,
                    Velocity = note.Velocity,
                };
            })
            .OrderBy(note => note.StartSeconds)
            .ThenBy(note => note.Pitch)
            .ToList();
    }

    public static ChordTimeline? ReadChords(string jsonPath)
    {
        if (!File.Exists(jsonPath))
        {
            return null;
        }

        var json = File.ReadAllText(jsonPath);
        return JsonSerializer.Deserialize<ChordTimeline>(json, JsonOptions.Manifest);
    }

    public static string? FirstExisting(params string?[] paths) =>
        paths.FirstOrDefault(path => path is not null && File.Exists(path));

    private static string ReadFourCc(BinaryReader reader) => Encoding.ASCII.GetString(reader.ReadBytes(4));
}
