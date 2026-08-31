# PolyScribe 实施 Roadmap

Roadmap 以“脚本能力先完成、GUI 后开始”为硬边界。项目为非商业用途，但仍必须遵守代码、模型权重与其他资产的许可条件。

## Phase 0：旧 demo 盘点与技术基线

目标：确认从 VoiceLab 保留什么、废弃什么，并验证目标模型在 Windows 上可运行。

任务：

- 按 [VoiceLab demo 迁移与重构](voicelab_migration.md) 完成只读盘点；
- 建立 8–12 个短片段和 3–5 首完整歌曲的本地基准集；
- 固定 MuScriptor、BTC、GAME、Basic Pitch 和首选分离模型版本；
- 在 Windows + RTX 5060 8GB 上记录运行时间、显存、内存与失败行为；
- 记录代码、权重、SoundFont 和工具许可；MuScriptor 非商业权重可以用于本项目，但仍由用户授权下载；
- 确定第一版三个硬输出：`piano.mid`、`vocal.mid`、`chords.mid`。

退出条件：模型均能在目标机独立运行；旧 demo 的迁移清单明确；不存在未记录来源的权重。

## Phase 1：单仓脚本运行时

目标：在 PolyScribe 内建立干净、可诊断、可测试的 workflow 基础。

任务：

- 建立 `src/`、`scripts/`、`workflows/`、`contracts/schemas/` 和测试目录；
- 实现当前仓库自己的 `bootstrap`、`doctor`、`worker run`；
- 为每个重型模型维护独立 `uv` 环境；
- 统一 vendor、assets、runtime、jobs 路径解析；
- 实现 request/event/artifact/error JSON Schema；
- 实现输入摘要、模型 SHA-256、vendor commit 和 execution provider 记录；
- 首先迁移并重构 separation workflow，不保留对 VoiceLab 路径的运行依赖。

退出条件：全新 Windows 环境可由当前仓库完成准备；doctor 能准确报告缺项；worker 对固定请求产生可验证 JSONL 事件。

## Phase 2：第一版本三条 MIDI 脚本

目标：完成钢琴、人声、和弦三条端到端脚本链路。

### 2.1 钢琴 MIDI

```text
song.flac
  -> MuScriptor
  -> select/normalize piano track
  -> piano.mid
```

可选校正支路：

```text
song.flac
  -> piano separation
  -> Basic Pitch
  -> piano.alternate.mid
```

首版可以保留 primary 与 alternate 两份结果；没有可靠融合证据前不自动覆盖主结果。

### 2.2 人声 MIDI

```text
song.flac
  -> vocal/instrumental separation
  -> optional dereverb/denoise
  -> GAME Medium
  -> vocal.mid
```

第一版优先单旋律 lead vocal。若输入含明显多声部和声，输出 warning 和候选文件，不伪造单一正确旋律。

### 2.3 和弦 MIDI

```text
song.flac
  -> BTC
  -> normalized chord timeline
  -> chords.json + chords.mid
```

`chords.mid` 使用独立 MIDI track 表示根音和和弦构成音，保留原始和弦标签及时间边界，确保 DAW 导入后仍可追溯。

### 2.4 统一入口

```powershell
uv run polyscribe process song.flac --targets piano,vocal,chords
uv run polyscribe piano song.flac
uv run polyscribe vocal song.flac
uv run polyscribe chords song.flac
```

退出条件：三条命令可独立运行，总命令可编排它们；失败可定位到具体 stage；结果均写入 manifest；4 分钟歌曲可在目标机完成。

## Phase 3：脚本可靠性与质量闭环

目标：让脚本从“能跑”达到“可长期使用”。

任务：

- 实现 job store、事件日志、取消、断点续跑和 stage 级重试；
- 完成内容摘要缓存和严格缓存失效；
- 建立 piano onset/offset/pitch、vocal note、chord recall 等回归指标；
- 处理中文/空格路径、异常编码、长音频、磁盘不足、OOM 和无 GPU；
- 固化 `balanced`、`quality`、`low-vram` 配置，实际后端和降级行为写入 manifest；
- 生成可供人工 A/B 复核的音频/MIDI 对照。

退出条件：任何失败都不产生假成功；相同输入、版本与参数具有可复现结果；回归集能阻止明显质量下降。

## Phase 4：人声和声与乐谱补全

目标：在三条核心 MIDI 稳定后扩展完整音乐生产输出。

任务：

- Lead/Backing 二阶段分离；
- Basic Pitch backing vocal 多音高候选；
- 基于 chord、音域、voice crossing 和 voice leading 的 DP/Viterbi 声部分配；
- RMVPE F0、ASR lyrics 与 note-lyric alignment；
- 输出 `harmony_*.mid` 和 `unassigned.mid`；
- MIDI → MusicXML → PDF；
- 定义 SynthV/ACE Cover 中间包。

退出条件：无法分配的和声音符显式保留；MusicXML 能在 MuseScore 打开；Cover 输出有完整来源与置信度。

## Phase 5：脚本版功能完成门槛

进入 GUI 前，必须同时满足：

- `piano.mid`、`vocal.mid`、`chords.mid` 在基准集上稳定生成；
- bootstrap、doctor、独立脚本和总 pipeline 均有自动测试；
- stage 失败、取消、重试、缓存与日志行为明确；
- 8GB 显存配置有实机数据和低显存方案；
- 所有输出 schema 已版本化；
- 不再存在 VoiceLab 运行依赖、双实现或旧路径 fallback；
- 已知质量限制已写入文档。

未达到以上门槛时，只允许开发诊断型小工具，不开始完整 GUI。

## Phase 6：Windows GUI

目标：把已经稳定的脚本能力产品化为本地桌面工具。

任务：

- 通过短期 spike 比较 WinUI 3 与 WPF，只保留一个 UI 技术栈；**已选择 WinUI 3 unpackaged**，见 [ADR 0001](adr/0001-winui3-unpackaged.md) 与 `apps/desktop/`。
- 实现拖放导入、目标选择、预设、进度、取消和错误详情；
- 提供波形、和弦时间线、钢琴卷帘与冲突标记；
- 支持任务恢复、试听、人工校正和产物打开；
- GUI 只消费稳定任务 API，不直接加载模型或解析 workflow 私有目录；
- 在干净 Windows 机器验证安装、升级和卸载。

退出条件：GUI 与 CLI 对相同请求生成相同 manifest；关闭或重启应用不丢任务；核心流水线仍可脱离 GUI 单独使用。

## Phase 7：后续方向

- ROSVOT 主唱复核；
- GAME ONNX/DirectML worker；
- singer-informed separation；
- 更好的 chord backend 与和声纠错；
- 实时 Audio-to-MIDI；
- DAW 插件和 reharmonization。

## 推荐执行顺序

```text
VoiceLab demo inventory
        -> PolyScribe runtime foundation
        -> piano/vocal/chord scripts
        -> reliability and evaluation
        -> harmony/score/cover completion
        -> script completion gate
        -> Windows GUI
```

