# 产品范围

## 1. 产品目标

PolyScribe 面向以下离线工作流：

1. 用户导入 WAV、FLAC、MP3 或常见视频音轨。
2. 软件分析节拍、调性和和弦，转录钢琴及其他乐器 MIDI。
3. Cover Mode 进一步分离主唱与和声，生成可在 Synthesizer V Studio / ACE Studio 中继续编辑的素材。
4. 用户复核低置信度片段后，导出 MIDI、MusicXML、PDF 和结构化 JSON。

一句话定义：

> PolyScribe — AI-powered music transcription and harmonic analysis for Windows.

## 2. 用户场景

### 2.1 编曲与扒谱

输入完整歌曲，得到：

- 多轨 MIDI，至少可识别钢琴、贝斯、吉他、鼓和人声类别；
- 和弦时间线、调性、速度与拍号候选；
- 可编辑 MusicXML 和用于阅读的 PDF；
- 每个结果的来源、后端版本与置信度。

### 2.2 钢琴伴奏还原

主路线使用完整混音多乐器转录；可选校正路线先得到 piano stem，再以轻量多音高模型生成第二份钢琴 MIDI。系统对齐两份结果，但不静默覆盖冲突音符。

### 2.3 Vocal Cover

输入完整歌曲，输出：

- `lead_vocal.wav`、`backing_vocal.wav`；
- 主唱 MIDI、连续 F0/音高曲线、歌词与音符对齐；
- 若和声为多音高混合，输出和声候选与拆分后的多声部 MIDI；
- 面向 SynthV / ACE 的导出包和人工复核提示。

## 3. MVP 边界

### v0.1 Script/CLI MVP

- Windows 本地批处理，不包含实时监听或插件形态。
- 单文件任务；任务可恢复，可读取进度和错误。
- 钢琴 MIDI：MuScriptor 主结果，可选 stem + Basic Pitch 校正。
- 人声 MIDI：分离后的 lead vocal 经 GAME 转录。
- 和弦：BTC 时间线，同时生成可导入 DAW 的 `chords.mid`。
- 保留 MuScriptor 多轨 MIDI 作为辅助产物。
- 统一 `manifest.json`、`events.jsonl` 与结果目录。

### v0.2 Script Pipeline Complete

- 完成 Vocal/Instrumental 与 Lead/Backing 分离。
- F0、歌词和音符-歌词对齐的可替换接口。
- Basic Pitch 和声候选及首版声部分配。
- MusicXML/PDF 和 Cover 素材导出。
- 三条主流水线的回归、断点续跑和错误诊断达到稳定门槛。

### v0.3 Desktop Preview

- Windows 桌面壳、文件导入、任务进度、波形/钢琴卷帘预览。
- 冲突音符和低置信度片段的人工复核。
- MIDI、MusicXML、PDF、SynthV/ACE 中间包导出。

## 4. 非目标

首个稳定版不承诺：

- 实时 Audio-to-MIDI 或 DAW 插件；
- 完整乐谱编辑器能力；
- 自动生成“无需人工修改”的出版级乐谱；
- 从混合和声中保证恢复真实歌手人数与每条原始声部；
- 训练自有基础模型；
- 商业化、付费服务或商业发行包。

## 5. 成功指标

- 在目标 Windows + RTX 5060 环境中，一首 4 分钟歌曲可完整跑通且不会因 8GB 显存直接失败；必要时能自动建议降级配置，但不能静默改变后端。
- 同一输入、相同后端版本与参数得到可复现的清单和产物结构。
- 任一 workflow 失败时，任务状态、失败阶段、命令退出码和日志均可定位。
- 用户可以只重跑失败或参数变化的阶段，不必重新执行整条流水线。
- 所有脚本环境均能生成模型、权重、许可证和来源清单。
