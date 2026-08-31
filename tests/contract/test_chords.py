from __future__ import annotations

from pathlib import Path

import pretty_midi

from polyscribe_core.chords import (
    export_chords_from_midi,
    parse_chord_label,
)
from tests.contract.midi_fixtures import write_mix_midi


def test_parse_common_btc_labels() -> None:
    assert parse_chord_label("N") == ("N", True)
    assert parse_chord_label("C") == ("C:maj", True)
    assert parse_chord_label("C:maj7") == ("C:maj7", True)
    assert parse_chord_label("A#:min") == ("A#:min", True)
    assert parse_chord_label("F:sus4") == ("F:sus4", True)
    assert parse_chord_label("Gmin7") == ("G:min7", True)


def test_export_chords_from_markers(tmp_path: Path) -> None:
    source = write_mix_midi(
        tmp_path / "full.mid",
        chords=[(0.0, "C:maj"), (2.0, "G:maj"), (4.0, "N")],
    )
    json_path = tmp_path / "chords.json"
    midi_path = tmp_path / "chords.mid"
    document, warnings = export_chords_from_midi(
        source, json_path, midi_path, end_time=6.0
    )
    assert json_path.is_file()
    assert midi_path.is_file() and midi_path.stat().st_size > 0
    labels = [seg["label"] for seg in document["segments"]]
    assert labels[0] == "C:maj"
    assert labels[1] == "G:maj"
    assert labels[2] == "N"
    assert document["segments"][0]["confidence"] is None
    assert document["producer"] == "muscriptor-btc"
    midi = pretty_midi.PrettyMIDI(str(midi_path))
    pitches = {note.pitch for note in midi.instruments[0].notes}
    assert pitches  # C 与 G 构成音
    unmapped = [item for item in warnings if "无法规范化" in item]
    assert unmapped == []


def test_unmapped_label_is_kept(tmp_path: Path) -> None:
    source = write_mix_midi(
        tmp_path / "weird.mid",
        chords=[(0.0, "not-a-chord")],
    )
    document, warnings = export_chords_from_midi(
        source,
        tmp_path / "chords.json",
        tmp_path / "chords.mid",
        end_time=2.0,
    )
    assert document["segments"][0]["raw_label"] == "not-a-chord"
    assert any("raw_label" in item for item in warnings)


def test_export_chords_falls_back_to_pitch_class_template(tmp_path: Path) -> None:
    source = write_mix_midi(tmp_path / "no_markers.mid", extra_track=None)
    document, warnings = export_chords_from_midi(
        source,
        tmp_path / "chords.json",
        tmp_path / "chords.mid",
        end_time=2.0,
    )
    assert document["producer"] == "midi-pc-template"
    assert document["segments"]
    assert any("音高模板" in item for item in warnings)
    assert document["segments"][0]["label"].startswith("C:")
