using System.Text.Json;

namespace PolyScribe.App.Services;

public sealed class AppSettings
{
    private readonly string _path;
    private readonly Dictionary<string, string> _values;

    public AppSettings()
    {
        var directory = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "PolyScribe");
        Directory.CreateDirectory(directory);
        _path = Path.Combine(directory, "settings.json");
        _values = Load();
    }

    public string Theme
    {
        get => Read("theme", "System");
        set => Write("theme", value);
    }

    public string? RepositoryRoot
    {
        get => ReadOrNull("repository_root");
        set => WriteOrClear("repository_root", value);
    }

    public string? JobsDirectory
    {
        get => ReadOrNull("jobs_directory");
        set => WriteOrClear("jobs_directory", value);
    }

    public string LastTargets
    {
        get => Read("last_targets", "piano,vocal,harmony,chords");
        set => Write("last_targets", value);
    }

    public bool WelcomeSeen
    {
        get => Read("welcome_seen", "false") == "true";
        set => Write("welcome_seen", value ? "true" : "false");
    }

    private string Read(string key, string fallback) =>
        _values.TryGetValue(key, out var value) && !string.IsNullOrWhiteSpace(value) ? value : fallback;

    private string? ReadOrNull(string key) =>
        _values.TryGetValue(key, out var value) && !string.IsNullOrWhiteSpace(value) ? value : null;

    private void Write(string key, string value)
    {
        _values[key] = value;
        Persist();
    }

    private void WriteOrClear(string key, string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            _values.Remove(key);
        }
        else
        {
            _values[key] = value;
        }

        Persist();
    }

    private Dictionary<string, string> Load()
    {
        if (!File.Exists(_path))
        {
            return new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        }

        try
        {
            var json = File.ReadAllText(_path);
            return JsonSerializer.Deserialize<Dictionary<string, string>>(json)
                ?? new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        }
        catch (JsonException)
        {
            return new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        }
    }

    private void Persist()
    {
        var json = JsonSerializer.Serialize(_values, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(_path, json);
    }
}
