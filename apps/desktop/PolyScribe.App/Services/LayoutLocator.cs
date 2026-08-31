using System.Text.RegularExpressions;

namespace PolyScribe.App.Services;

public sealed class LayoutLocator
{
    private readonly AppSettings _settings;

    public LayoutLocator(AppSettings settings)
    {
        _settings = settings;
    }

    public string? RepositoryRoot => FindRepositoryRoot();

    public string? JobsDirectory
    {
        get
        {
            if (!string.IsNullOrWhiteSpace(_settings.JobsDirectory) && Directory.Exists(_settings.JobsDirectory))
            {
                return Path.GetFullPath(_settings.JobsDirectory);
            }

            var root = RepositoryRoot;
            return root is null ? null : Path.Combine(root, "jobs");
        }
    }

    public bool IsReady => RepositoryRoot is not null;

    public string? FindRepositoryRoot()
    {
        foreach (var candidate in Candidates())
        {
            if (IsRepository(candidate))
            {
                return candidate;
            }
        }

        return null;
    }

    public IEnumerable<string> Candidates()
    {
        if (!string.IsNullOrWhiteSpace(_settings.RepositoryRoot))
        {
            yield return Path.GetFullPath(_settings.RepositoryRoot);
        }

        var env = Environment.GetEnvironmentVariable("POLYSCRIBE_ROOT");
        if (!string.IsNullOrWhiteSpace(env))
        {
            yield return Path.GetFullPath(env);
        }

        foreach (var start in new[] { AppContext.BaseDirectory, Environment.CurrentDirectory })
        {
            foreach (var directory in WalkUp(start))
            {
                yield return directory;
            }
        }
    }

    public static bool IsRepository(string directory)
    {
        var project = Path.Combine(directory, "pyproject.toml");
        if (!File.Exists(project))
        {
            return false;
        }

        var text = File.ReadAllText(project);
        return Regex.IsMatch(text, @"name\s*=\s*""polyscribe""", RegexOptions.IgnoreCase);
    }

    private static IEnumerable<string> WalkUp(string start)
    {
        DirectoryInfo? current = new(start);
        while (current is not null)
        {
            yield return current.FullName;
            current = current.Parent;
        }
    }
}
