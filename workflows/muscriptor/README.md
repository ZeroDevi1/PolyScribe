# MuScriptor workflow

完整混音转多轨 MIDI。第一版默认 Medium；钢琴轨由 PolyScribe 抽取，必要时再跑 instrument-conditioned 钢琴转录。

## 输入 / 输出

- 输入：规范化 WAV（`inputs.audio`）
- 输出：多轨 MIDI（`outputs.midi`）

## 模型与许可

- 代码：[muscriptor/muscriptor](https://github.com/muscriptor/muscriptor) MIT
- 权重：[MuScriptor/muscriptor-medium](https://huggingface.co/MuScriptor/muscriptor-medium) **CC BY-NC 4.0**，需用户接受 Hugging Face 条款

## 平台

Windows + CUDA（`uv sync` 时使用 `UV_TORCH_BACKEND=cu128`）。RTX 5060 8GB 上默认 Medium；Large 不作为第一版默认。

## 已知限制

- 非商业用途才能使用官方权重
- 节拍检测（`beat_this`）需要 `torchaudio`；bootstrap 会随 CUDA torch 一起安装，不能只留 CPU/`torch` 本体
- PyPI `muscriptor` 0.3.0 **没有** BTC 和弦 marker。第一版在缺失 marker 时用非人声/非鼓轨做音高模板估计，并在 manifest 写 warning
- 完整混音若没有钢琴轨，会再跑一次 `--instruments acoustic_piano`，不会把吉他轨改名为钢琴
