from __future__ import annotations

from pathlib import Path

import pretty_midi
import pytest

from polyscribe_core.errors import PianoTrackNotFoundError
from polyscribe_core.midi_piano import extract_piano_midi
from tests.contract.midi_fixtures import write_mix_midi


def test_extract_piano_keeps_piano_drops_guitar(tmp_path: Path) -> None:
    source = write_mix_midi(tmp_path / "full.mid")
    dest = tmp_path / "piano.mid"
    stats = extract_piano_midi(source, dest)
    assert dest.is_file() and dest.stat().st_size > 0
    assert stats["note_count"] == 1
    out = pretty_midi.PrettyMIDI(str(dest))
    assert len(out.instruments) == 1
    assert out.instruments[0].name == "acoustic_piano"
    assert {note.pitch for note in out.instruments[0].notes} == {60}


def test_extract_piano_fails_without_piano_track(tmp_path: Path) -> None:
    source = write_mix_midi(tmp_path / "no_piano.mid", with_piano=False)
    with pytest.raises(PianoTrackNotFoundError):
        extract_piano_midi(source, tmp_path / "piano.mid")
