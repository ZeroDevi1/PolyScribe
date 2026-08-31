# Separation workflow

两段分离：人声/伴奏，再在人声 stem 上做 Lead/Backing（karaoke 模型）。

## 输入 / 输出

- 输入：规范化 WAV
- 输出：`vocals.wav`、`instrumental.wav`、`lead.wav`、`backing.wav`

## 默认模型

- 人声/伴奏：`model_mel_band_roformer_ep_3005_sdr_11.4360.ckpt`
- Lead/Backing：`UVR_MDXNET_KARA_2.onnx`（8GB 显存更稳）

Karaoke 应用到人声 stem 后：Vocals → lead，Instrumental → backing。

## 许可

[python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator) MIT。各权重许可不自动等于框架许可，bootstrap/首次下载后应记入资产清单。

## 已知限制

- GPU stage 必须与其他 PyTorch worker 串行
- Karaoke（`UVR_MDXNET_KARA_2.onnx`）使用 CPU `onnxruntime`：ORT-GPU 1.29 需要 CUDA 13，与本仓库的 torch cu128 不兼容
- 和声泄漏、主唱残留都会进入后续 GAME / Basic Pitch
- 第一版不做 ensemble
