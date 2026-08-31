# GAME workflow

主唱 WAV → 单旋律 MIDI。第一版使用 GAME 1.0 Medium，语言 `zh`。

## 输入 / 输出

- 输入：lead vocal WAV
- 输出：`vocal.mid`

## 模型

- 仓库：[openvpi/GAME](https://github.com/openvpi/GAME) MIT
- 权重：[GAME-1.0-medium.zip](https://github.com/openvpi/GAME/releases/tag/v1.0.0) **CC BY-NC-SA 4.0**
- 调用：`infer.py extract --language zh --output-formats mid`

## 已知限制

- 单旋律转录器，不能表示同时出现的多条和声
- 需要分离后的人声；伴奏残留会降低边界质量
- 第一版不走 ONNX/DirectML
