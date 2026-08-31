using System.Text.Json;
using PolyScribe.App.Models;

namespace PolyScribe.App.Services;

public sealed class JobStore
{
    private readonly LayoutLocator _layout;

    public JobStore(LayoutLocator layout)
    {
        _layout = layout;
    }

    public IReadOnlyList<ManifestDocument> ListJobs()
    {
        var jobs = _layout.JobsDirectory;
        if (jobs is null || !Directory.Exists(jobs))
        {
            return [];
        }

        var results = new List<ManifestDocument>();
        foreach (var directory in Directory.EnumerateDirectories(jobs))
        {
            var document = TryRead(Path.Combine(directory, "manifest.json"));
            if (document is not null)
            {
                results.Add(document);
            }
        }

        return results
            .OrderByDescending(job => job.CreatedAt)
            .ToList();
    }

    public ManifestDocument? Read(string jobId)
    {
        var root = JobRoot(jobId);
        return root is null ? null : TryRead(Path.Combine(root, "manifest.json"));
    }

    public string? JobRoot(string jobId)
    {
        var jobs = _layout.JobsDirectory;
        if (jobs is null)
        {
            return null;
        }

        var root = Path.Combine(jobs, jobId);
        return Directory.Exists(root) ? root : null;
    }

    public IReadOnlyList<JobEvent> ReadEvents(string jobId)
    {
        var root = JobRoot(jobId);
        if (root is null)
        {
            return [];
        }

        var path = Path.Combine(root, "events.jsonl");
        if (!File.Exists(path))
        {
            return [];
        }

        var events = new List<JobEvent>();
        foreach (var line in File.ReadLines(path))
        {
            if (string.IsNullOrWhiteSpace(line))
            {
                continue;
            }

            try
            {
                var parsed = JsonSerializer.Deserialize<JobEvent>(line, JsonOptions.Manifest);
                if (parsed is not null)
                {
                    events.Add(parsed);
                }
            }
            catch (JsonException)
            {
                // 契约要求跳过非 JSONL 行，不能把任务标成失败。
            }
        }

        return events;
    }

    public static ManifestDocument? TryRead(string path)
    {
        if (!File.Exists(path))
        {
            return null;
        }

        try
        {
            var json = File.ReadAllText(path);
            return JsonSerializer.Deserialize<ManifestDocument>(json, JsonOptions.Manifest);
        }
        catch (JsonException)
        {
            return null;
        }
        catch (IOException)
        {
            return null;
        }
    }
}
