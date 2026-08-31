# PolyScribe

PolyScribe 是面向 Windows 的本地 AI 音乐转录与和声分析产品。用户导入一首歌，系统产出可追踪的 MIDI、和弦时间线与后续 Cover 素材；GUI 与 CLI 共享同一份任务契约。

## Language

**Job**:
一次针对单一输入音频的处理单元，目录内含 `manifest.json` 与 `events.jsonl`。
_Avoid_: task, run, session

**Stage**:
Job 内一个可独立记录状态的处理步骤，例如 normalize、muscriptor、separation。
_Avoid_: step, phase, workflow step

**Artifact**:
Stage 写出的可追踪产物，必须有路径、角色和生产者，不能用空文件冒充成功。
_Avoid_: output file, result, export（export 仅指用户拿走产物的动作）

**Target**:
用户选择的产物类别：`piano`、`vocal`、`harmony`、`chords`。
_Avoid_: mode, preset, pipeline

**Manifest**:
Job 的事实清单，记录状态、输入摘要、stages、artifacts 与 warnings。
_Avoid_: report, summary, metadata file

**Worker**:
通过子进程协议执行单一 workflow 的隔离运行时，stdout 只写 JSONL 事件。
_Avoid_: backend, model process, engine

**Layout**:
仓库根、jobs、vendor、assets 的路径解析结果。
_Avoid_: workspace, install path

**Cover Mode**:
面向 SynthV / ACE 的人声 Cover 流水线，与普通转录 Job 的 `mode` 区分。
_Avoid_: vocal mode, karaoke mode
