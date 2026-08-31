"""Basic Pitch backing 多音高 worker。stdout 仅 JSONL。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from protocol import emit, fail, load_request, require_file  # noqa: E402

MIN_NOTE_SECONDS = 0.05


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    args = parser.parse_args()
    request = load_request(args.request)
    emit(request, "started", {"workflow": "basic_pitch"})

    audio = Path(request["inputs"]["audio"])
    midi_out = Path(request["outputs"]["midi"])
    require_file(audio, request, what="backing 音频")
    emit(request, "progress", {"message": "basic-pitch predict"})

    from basic_pitch.inference import predict

    _model_output, midi_data, note_events = predict(str(audio))
    kept = 0
    if midi_data is not None:
        for instrument in midi_data.instruments:
            filtered = [
                note
                for note in instrument.notes
                if (note.end - note.start) >= MIN_NOTE_SECONDS
            ]
            instrument.notes = filtered
            kept += len(filtered)
        midi_out.parent.mkdir(parents=True, exist_ok=True)
        midi_data.write(str(midi_out))
    else:
        fail(request, "Basic Pitch 没有返回 MIDI")

    if not midi_out.is_file() or midi_out.stat().st_size <= 0:
        fail(request, "Basic Pitch 未写出 MIDI", error_type="artifact_error")

    emit(
        request,
        "succeeded",
        {
            "midi": str(midi_out),
            "note_count": kept,
            "raw_note_events": len(note_events or []),
            "min_note_seconds": MIN_NOTE_SECONDS,
        },
    )


if __name__ == "__main__":
    main()
