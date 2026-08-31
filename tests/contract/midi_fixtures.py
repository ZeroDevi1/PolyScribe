"""MIDI fixture helpers for contract tests."""

from __future__ import annotations

from pathlib import Path

import mido


def write_mix_midi(
    path: Path,
    *,
    with_piano: bool = True,
    piano_name: str = "acoustic_piano",
    extra_track: str | None = "distorted_electric_guitar",
    chords: list[tuple[float, str]] | None = None,
) -> Path:
    midi = mido.MidiFile(ticks_per_beat=480)
    meta = mido.MidiTrack()
    midi.tracks.append(meta)
    meta.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    last_tick = 0
    for seconds, label in chords or []:
        tick = int(round(seconds * 480 / 0.5))  # 120 BPM, 480 ticks = 0.5s
        delta = max(0, tick - last_tick)
        meta.append(
            mido.MetaMessage("marker", text=f"muscriptor:chord={label}", time=delta)
        )
        last_tick = tick
    meta.append(mido.MetaMessage("end_of_track", time=0))

    if with_piano:
        piano = mido.MidiTrack()
        midi.tracks.append(piano)
        piano.append(mido.MetaMessage("track_name", name=piano_name, time=0))
        piano.append(mido.Message("program_change", program=0, channel=0, time=0))
        piano.append(mido.Message("note_on", note=60, velocity=80, channel=0, time=0))
        piano.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=1920))
        piano.append(mido.MetaMessage("end_of_track", time=0))

    if extra_track:
        guitar = mido.MidiTrack()
        midi.tracks.append(guitar)
        guitar.append(mido.MetaMessage("track_name", name=extra_track, time=0))
        guitar.append(mido.Message("program_change", program=30, channel=1, time=0))
        guitar.append(mido.Message("note_on", note=40, velocity=70, channel=1, time=0))
        guitar.append(mido.Message("note_off", note=40, velocity=0, channel=1, time=960))
        guitar.append(mido.MetaMessage("end_of_track", time=0))

    path.parent.mkdir(parents=True, exist_ok=True)
    midi.save(str(path))
    return path
