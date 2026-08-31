"""MuScriptor BTC marker → chords.json / 可导入 DAW 的 chords.mid。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mido
import pretty_midi

from polyscribe_core.constants import MUSCRIPTOR_CHORD_PREFIX, SCHEMA_VERSION
from polyscribe_core.io import write_json

ROOT_TO_PC = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "FB": 4,
    "F": 5,
    "E#": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
    "CB": 11,
}

PC_TO_ROOT = {
    0: "C",
    1: "C#",
    2: "D",
    3: "D#",
    4: "E",
    5: "F",
    6: "F#",
    7: "G",
    8: "G#",
    9: "A",
    10: "A#",
    11: "B",
}

# 规范质量 → 相对半音
QUALITY_INTERVALS: dict[str, tuple[int, ...]] = {
    "maj": (0, 4, 7),
    "min": (0, 3, 7),
    "7": (0, 4, 7, 10),
    "maj7": (0, 4, 7, 11),
    "min7": (0, 3, 7, 10),
    "minmaj7": (0, 3, 7, 11),
    "6": (0, 4, 7, 9),
    "min6": (0, 3, 7, 9),
    "9": (0, 4, 7, 10, 14),
    "maj9": (0, 4, 7, 11, 14),
    "min9": (0, 3, 7, 10, 14),
    "dim": (0, 3, 6),
    "dim7": (0, 3, 6, 9),
    "aug": (0, 4, 8),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    "min7b5": (0, 3, 6, 10),
    "5": (0, 7),
}

QUALITY_ALIASES = {
    "": "maj",
    "M": "maj",
    "MAJ": "maj",
    "MAJOR": "maj",
    "MIN": "min",
    "MINOR": "min",
    "MIN7": "min7",
    "M7": "min7",
    "MAJ7": "maj7",
    "7": "7",
    "6": "6",
    "MAJ6": "6",
    "MIN6": "min6",
    "M6": "min6",
    "DIM": "dim",
    "DIM7": "dim7",
    "AUG": "aug",
    "SUS2": "sus2",
    "SUS4": "sus4",
    "SUS": "sus4",
    "HDI": "min7b5",
    "HDIM": "min7b5",
    "M7B5": "min7b5",
    "MIN7B5": "min7b5",
    "5": "5",
    "9": "9",
    "MAJ9": "maj9",
    "MIN9": "min9",
    "MINMAJ7": "minmaj7",
}

_ROOT_QUALITY_RE = re.compile(r"^([A-G](?:#|b)?)(.*)$", re.IGNORECASE)


@dataclass(frozen=True)
class ChordSegment:
    start: float
    end: float
    label: str
    raw_label: str
    mapped: bool

    def as_json(self) -> dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "label": self.label,
            "raw_label": self.raw_label,
            "confidence": None,
        }


def extract_chord_markers(midi_path: Path) -> list[tuple[float, str]]:
    midi = mido.MidiFile(str(midi_path))
    tempo = 500000
    seconds = 0.0
    found: list[tuple[float, str]] = []
    for msg in mido.merge_tracks(midi.tracks):
        if msg.time:
            seconds += mido.tick2second(msg.time, midi.ticks_per_beat, tempo)
        if msg.type == "set_tempo":
            tempo = msg.tempo
        text = ""
        if msg.type in {"marker", "text", "lyrics"}:
            text = (getattr(msg, "text", None) or "").strip()
        if text.startswith(MUSCRIPTOR_CHORD_PREFIX):
            found.append((seconds, text[len(MUSCRIPTOR_CHORD_PREFIX) :].strip()))
        elif text.startswith("chord="):
            found.append((seconds, text[len("chord=") :].strip()))
    return found


def parse_chord_label(raw: str) -> tuple[str, bool]:
    text = (raw or "").strip()
    if not text:
        return "N", False
    upper = text.upper().replace(" ", "")
    if upper in {"N", "NC", "NOCHORD", "NO_CHORD", "NONE", "X"}:
        return "N", True
    if ":" in text:
        root_text, quality_text = text.split(":", 1)
    else:
        match = _ROOT_QUALITY_RE.match(text)
        if not match:
            return text, False
        root_text, quality_text = match.group(1), match.group(2)
    root = _canonical_root(root_text)
    if root is None:
        return text, False
    quality = _canonical_quality(quality_text)
    if quality is None:
        leftover = quality_text.strip().lstrip(":")
        return f"{root}:{leftover}" if leftover else root, False
    return f"{root}:{quality}", True


def _canonical_root(root: str) -> str | None:
    token = root.strip().replace("♯", "#").replace("♭", "b")
    if not token:
        return None
    key = token[0].upper() + token[1:].replace("b", "B").replace("#", "#")
    if len(key) >= 2 and key[1] == "B":
        key = key[0] + "B"
    else:
        key = key.upper()
    pc = ROOT_TO_PC.get(key)
    if pc is None:
        return None
    return PC_TO_ROOT[pc]


def _canonical_quality(quality: str) -> str | None:
    token = quality.strip().lstrip(":").split("/")[0].replace(" ", "").replace("-", "")
    if token == "m":
        return "min"
    key = token.upper()
    if key in QUALITY_ALIASES:
        return QUALITY_ALIASES[key]
    lowered = token.lower()
    if lowered in QUALITY_INTERVALS:
        return lowered
    return None


def markers_to_segments(
    markers: list[tuple[float, str]],
    *,
    end_time: float,
) -> tuple[list[ChordSegment], list[str]]:
    if not markers:
        return [], ["MIDI 中没有 muscriptor:chord= marker"]
    ordered = sorted(markers, key=lambda item: item[0])
    segments: list[ChordSegment] = []
    warnings: list[str] = []
    for index, (start, raw) in enumerate(ordered):
        stop = ordered[index + 1][0] if index + 1 < len(ordered) else max(float(end_time), start)
        if stop <= start:
            stop = start + 0.05
        label, mapped = parse_chord_label(raw)
        if not mapped:
            warnings.append(f"无法规范化和弦标签，保留 raw_label: {raw}")
        if segments and segments[-1].raw_label == raw and segments[-1].label == label:
            prev = segments[-1]
            segments[-1] = ChordSegment(
                start=prev.start,
                end=stop,
                label=label,
                raw_label=raw,
                mapped=mapped and prev.mapped,
            )
            continue
        segments.append(
            ChordSegment(start=start, end=stop, label=label, raw_label=raw, mapped=mapped)
        )
    return segments, warnings


def chord_pitches(label: str, *, octave: int = 3) -> list[int]:
    parsed, mapped = parse_chord_label(label)
    if parsed == "N" or not mapped:
        return []
    root, _, quality = parsed.partition(":")
    pc = ROOT_TO_PC.get(root)
    if pc is None:
        return []
    intervals = QUALITY_INTERVALS.get(quality, (0, 4, 7))
    base = 12 * (octave + 1) + pc
    pitches: list[int] = []
    for interval in intervals:
        pitch = base + interval
        while pitch > 84:
            pitch -= 12
        while pitch < 36:
            pitch += 12
        pitches.append(pitch)
    return pitches


SKIP_CHORD_NAMES = ("voice", "vocal", "drum", "perc")
TEMPLATE_QUALITIES = ("maj", "min", "7", "maj7", "min7", "sus4", "dim", "6")


def _is_harmonic_instrument(instrument: pretty_midi.Instrument) -> bool:
    if instrument.is_drum:
        return False
    name = (instrument.name or "").lower()
    return not any(token in name for token in SKIP_CHORD_NAMES)


def _best_template_chord(chroma: list[float]) -> tuple[str, float]:
    energy = sum(chroma)
    if energy < 1e-6:
        return "N", 0.0
    best_label = "N"
    best_score = -1.0
    chroma_norm = sum(x * x for x in chroma) ** 0.5
    for root_pc, root_name in PC_TO_ROOT.items():
        for quality in TEMPLATE_QUALITIES:
            intervals = QUALITY_INTERVALS[quality]
            template = [0.0] * 12
            for interval in intervals:
                template[(root_pc + interval) % 12] = 1.0
            template_norm = sum(x * x for x in template) ** 0.5
            dot = sum(a * b for a, b in zip(chroma, template, strict=True))
            score = dot / (chroma_norm * template_norm) if chroma_norm and template_norm else 0.0
            if score > best_score:
                best_score = score
                best_label = f"{root_name}:{quality}"
    if best_score < 0.45:
        return "N", best_score
    return best_label, best_score


def chords_from_pitch_classes(
    midi_path: Path,
    *,
    end_time: float,
    hop: float = 0.5,
    window: float = 1.0,
) -> list[tuple[float, str]]:
    midi = pretty_midi.PrettyMIDI(str(midi_path))
    harmonic = [inst for inst in midi.instruments if _is_harmonic_instrument(inst)]
    duration = max(end_time, float(midi.get_end_time()), 0.0)
    if not harmonic or duration <= 0:
        return []
    markers: list[tuple[float, str]] = []
    t = 0.0
    while t < duration:
        start, stop = t, min(t + window, duration)
        chroma = [0.0] * 12
        for inst in harmonic:
            for note in inst.notes:
                overlap = min(note.end, stop) - max(note.start, start)
                if overlap <= 0:
                    continue
                chroma[note.pitch % 12] += overlap
        label, _score = _best_template_chord(chroma)
        markers.append((t, label))
        t += hop
    return markers


def write_chords_json(
    segments: list[ChordSegment],
    dest: Path,
    *,
    producer: str = "muscriptor-btc",
) -> dict[str, Any]:
    document = {
        "schema_version": SCHEMA_VERSION,
        "timebase": "seconds",
        "producer": producer,
        "segments": [item.as_json() for item in segments],
    }
    write_json(dest, document)
    return document


def write_chords_midi(segments: list[ChordSegment], dest: Path) -> None:
    midi = pretty_midi.PrettyMIDI(initial_tempo=120.0)
    instrument = pretty_midi.Instrument(program=0, name="chords")
    lyrics: list[pretty_midi.Lyric] = []
    for segment in segments:
        lyrics.append(pretty_midi.Lyric(text=segment.raw_label, time=segment.start))
        end = segment.end if segment.end > segment.start else segment.start + 0.05
        for pitch in chord_pitches(segment.label):
            instrument.notes.append(
                pretty_midi.Note(velocity=80, pitch=pitch, start=segment.start, end=end)
            )
    midi.instruments.append(instrument)
    midi.lyrics = lyrics
    dest.parent.mkdir(parents=True, exist_ok=True)
    midi.write(str(dest))
    _inject_markers(dest, segments)


def _inject_markers(path: Path, segments: list[ChordSegment]) -> None:
    midi = mido.MidiFile(str(path))
    marker_track = mido.MidiTrack()
    marker_track.append(mido.MetaMessage("track_name", name="chord_labels", time=0))
    tempo = 500000
    last_tick = 0
    for segment in segments:
        tick = int(round(mido.second2tick(segment.start, midi.ticks_per_beat, tempo)))
        delta = max(0, tick - last_tick)
        marker_track.append(
            mido.MetaMessage(
                "marker",
                text=f"{MUSCRIPTOR_CHORD_PREFIX}{segment.raw_label}",
                time=delta,
            )
        )
        last_tick = tick
    marker_track.append(mido.MetaMessage("end_of_track", time=0))
    midi.tracks.append(marker_track)
    midi.save(str(path))


def export_chords_from_midi(
    midi_path: Path,
    json_path: Path,
    midi_out: Path,
    *,
    end_time: float,
) -> tuple[dict[str, Any], list[str]]:
    markers = extract_chord_markers(midi_path)
    producer = "muscriptor-btc"
    extra_warnings: list[str] = []
    if not markers:
        markers = chords_from_pitch_classes(midi_path, end_time=end_time)
        producer = "midi-pc-template"
        extra_warnings.append(
            "MuScriptor 0.3.0 MIDI 没有 BTC marker，已用非人声/非鼓轨的音高模板估计和弦"
        )
    if not markers:
        segments: list[ChordSegment] = []
        warnings = extra_warnings + ["无法得到和弦时间线"]
    else:
        segments, warnings = markers_to_segments(markers, end_time=end_time)
        warnings = extra_warnings + warnings
    document = write_chords_json(segments, json_path, producer=producer)
    write_chords_midi(segments, midi_out)
    return document, warnings
