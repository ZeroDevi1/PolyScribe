from __future__ import annotations

from pathlib import Path

from polyscribe_core.job import create_job
from polyscribe_core.paths import resolve_layout


def test_create_job_uses_reference_input(tmp_path: Path) -> None:
    source = tmp_path / "song.flac"
    source.write_bytes(b"fake-flac")
    layout = resolve_layout()
    # 把 jobs 指到临时目录，避免污染仓库
    from polyscribe_core.paths import Layout

    test_layout = Layout(
        root=layout.root,
        jobs=tmp_path / "jobs",
        vendor=layout.vendor,
        assets=layout.assets,
        contracts=layout.contracts,
        workflows=layout.workflows,
        resources=layout.resources,
    )
    job = create_job(test_layout, source, job_id="test-job", duration_seconds=1.5)
    manifest = job.load_manifest()
    assert manifest["input_mode"] == "reference"
    assert manifest["input"]["path"] == str(source.resolve())
    assert manifest["input"]["sha256"]
    assert not (job.root / "input" / "source.flac").exists()
    assert (job.root / "output" / "instruments").is_dir()
    assert (job.root / "events.jsonl").is_file()
