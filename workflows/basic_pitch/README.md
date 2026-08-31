# Basic Pitch workflow

Backing vocal stem 的多音高 MIDI。第一版作为简化和声产物，不做声部分配。

## 输入 / 输出

- 输入：backing WAV
- 输出：单轨 polyphonic `harmony.mid`

## 模型

- [spotify/basic-pitch](https://github.com/spotify/basic-pitch) Apache-2.0
- Windows 默认 ONNX runtime
- Python 锁定 3.10：3.11+ 会拉取 TensorFlow，其 `tensorflow-io-gcs-filesystem` 在 Windows 无 wheel

## 已知限制

- 在混合和声上会产生碎片化音符，不是按歌手拆开的声部
- backing 近静音时输出无音符的合法 MIDI，由编排层写 warning
- 不是钢琴校正支路（`piano.alternate.mid` 不在第一版）
