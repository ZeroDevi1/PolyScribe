"""从 MuScriptor 多轨 MIDI 抽出钢琴轨。找不到钢琴时失败，不顶替其他乐器。"""

from __future__ import annotations

from pathlib import Path

import pretty_midi

from polyscribe_core.constants import PIANO_NAME_ALIASES, PIANO_PROGRAMS
from polyscribe_core.errors import PianoTrackNotFoundError


def _normalize_name(name: str | None) -> str:
    return (name or "").strip().lower().replace("-", "_").replace(" ", "_")


def is_piano_instrument(instrument: pretty_midi.Instrument) -> bool:
    if instrument.is_drum:
        return False
    name = _normalize_name(instrument.name)
    if name:
        if any(alias.replace(" ", "_") == name or alias.replace(" ", "_") in name for alias in PIANO_NAME_ALIASES):
            if "guitar" in name or "violin" in name or "synth" in name and "piano" not in name:
                return False
            return True
        return False
    return instrument.program in PIANO_PROGRAMS


def select_piano_instruments(midi: pretty_midi.PrettyMIDI) -> list[pretty_midi.Instrument]:
    named = [inst for inst in midi.instruments if is_piano_instrument(inst) and _normalize_name(inst.name)]
    if named:
        return named
    return [inst for inst in midi.instruments if is_piano_instrument(inst)]


def extract_piano_midi(source: Path, dest: Path) -> dict[str, int | str]:
    midi = pretty_midi.PrettyMIDI(str(source))
    pianos = select_piano_instruments(midi)
    if not pianos:
        names = [inst.name or f"program:{inst.program}" for inst in midi.instruments]
        raise PianoTrackNotFoundError(
            "未找到 acoustic_piano 或等价钢琴轨，拒绝用其他乐器顶替",
            details={"tracks": names},
        )
    out = pretty_midi.PrettyMIDI(initial_tempo=_initial_tempo(midi))
    merged = pretty_midi.Instrument(program=pianos[0].program, name="acoustic_piano")
    note_count = 0
    for inst in pianos:
        for note in inst.notes:
            merged.notes.append(
                pretty_midi.Note(
                    velocity=note.velocity,
                    pitch=note.pitch,
                    start=note.start,
                    end=note.end,
                )
            )
            note_count += 1
        merged.pitch_bends.extend(inst.pitch_bends)
        merged.control_changes.extend(inst.control_changes)
    if note_count <= 0:
        raise PianoTrackNotFoundError("钢琴轨存在但没有任何音符")
    out.instruments.append(merged)
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.write(str(dest))
    return {
        "note_count": int(note_count),
        "source_tracks": int(len(pianos)),
        "program": int(merged.program),
    }


def _initial_tempo(midi: pretty_midi.PrettyMIDI) -> float:
    if midi.get_tempo_changes()[1].size:
        return float(midi.get_tempo_changes()[1][0])
    return 120.0
