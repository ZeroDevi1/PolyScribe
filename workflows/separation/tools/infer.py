"""人声分离 + karaoke Lead/Backing。stdout 仅 JSONL。"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from protocol import emit, fail, load_request, require_file  # noqa: E402

VOCAL_KEYS = ("(vocals)", "_vocals", "vocals")
INST_KEYS = ("(instrumental)", "_instrumental", "instrumental", "no vocals")


def _pick(files: list[Path], keys: tuple[str, ...], fallback_index: int) -> Path:
    lowered = [(path, path.name.lower()) for path in files]
    for path, name in lowered:
        if any(key in name for key in keys):
            return path
    if len(files) > fallback_index:
        return files[fallback_index]
    return files[0]


def _resolve_output(item: str | Path, work: Path) -> Path:
    path = Path(item)
    candidates = [path, work / path, work / path.name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return path


def _copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not src.is_file():
        raise FileNotFoundError(f"分离输出不存在: {src}")
    if src.resolve() != dest.resolve():
        shutil.copy2(src, dest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    args = parser.parse_args()
    request = load_request(args.request)
    try:
        _run(request)
    except SystemExit:
        raise
    except Exception as exc:
        fail(request, f"{type(exc).__name__}: {exc}")


def _run(request: dict) -> None:
    emit(request, "started", {"workflow": "separation"})

    audio = Path(request["inputs"]["audio"])
    require_file(audio, request, what="输入音频")
    work = Path(request["work_dir"])
    work.mkdir(parents=True, exist_ok=True)
    params = request.get("params") or {}
    vocal_model = params.get("vocal_model", "model_mel_band_roformer_ep_3005_sdr_11.4360.ckpt")
    karaoke_model = params.get("karaoke_model", "UVR_MDXNET_KARA_2.onnx")

    from audio_separator.separator import Separator

    assets = Path(os.environ.get("POLYSCRIBE_ASSETS") or (work / "models"))
    model_dir = assets / "separator-models"
    model_dir.mkdir(parents=True, exist_ok=True)
    separator = Separator(
        output_dir=str(work),
        output_format="wav",
        model_file_dir=str(model_dir),
    )
    emit(request, "progress", {"message": "vocal/instrumental", "model": vocal_model})
    separator.load_model(model_filename=vocal_model)
    vocal_files = [_resolve_output(item, work) for item in separator.separate(str(audio))]
    if len(vocal_files) < 1:
        fail(request, "人声分离没有输出文件")
    vocals_src = _pick(vocal_files, VOCAL_KEYS, 0)
    inst_src = _pick(vocal_files, INST_KEYS, 1 if len(vocal_files) > 1 else 0)
    vocals_dest = Path(request["outputs"]["vocals"])
    inst_dest = Path(request["outputs"]["instrumental"])
    _copy(vocals_src, vocals_dest)
    _copy(inst_src, inst_dest)
    require_file(vocals_dest, request, what="vocals.wav")

    emit(request, "progress", {"message": "lead/backing karaoke", "model": karaoke_model})
    separator.load_model(model_filename=karaoke_model)
    kara_files = [_resolve_output(item, work) for item in separator.separate(str(vocals_dest))]
    if len(kara_files) < 1:
        fail(request, "karaoke 分离没有输出文件")
    lead_src = _pick(kara_files, VOCAL_KEYS, 0)
    backing_src = _pick(kara_files, INST_KEYS, 1 if len(kara_files) > 1 else 0)
    lead_dest = Path(request["outputs"]["lead"])
    backing_dest = Path(request["outputs"]["backing"])
    _copy(lead_src, lead_dest)
    _copy(backing_src, backing_dest)
    require_file(lead_dest, request, what="lead.wav")
    require_file(backing_dest, request, what="backing.wav")

    emit(
        request,
        "succeeded",
        {
            "vocal_model": vocal_model,
            "karaoke_model": karaoke_model,
            "vocals": str(vocals_dest),
            "instrumental": str(inst_dest),
            "lead": str(lead_dest),
            "backing": str(backing_dest),
        },
    )


if __name__ == "__main__":
    main()
