# 技术架构

## 1. 总体结构

```text
Scripts / CLI (第一阶段)
        |
        v
PolyScribe Orchestrator
  |-- Job Store
  |-- Pipeline Planner
  |-- Artifact Registry
  |-- Confidence/Fusion
  `-- Exporters
        |
        | Python API + JSONL subprocess boundary
        v
PolyScribe Workflow Workers
  |-- separation
  |-- muscriptor
  |-- chord
  |-- game
  |-- basic_pitch
  `-- score
        |
        v
vendor repos + shared model assets + isolated uv environments
```

VoiceLab 是旧版验证 demo，不再作为运行时依赖。PolyScribe 在当前仓库内重构 workflow、资产管理和诊断能力。编排层不直接导入重型 workflow 的内部包，而通过子进程调用稳定 worker 协议，避免 PyTorch、ONNX Runtime、CUDA 和不同 Python 版本在一个进程内冲突。

## 2. 单仓分层职责

### Orchestrator

- 定义用户任务和 pipeline；
- 维护统一输入、事件和产物契约；
- 选择 workflow 与参数，但不关心其内部张量格式；
- 负责缓存命中、断点续跑、融合、校正与导出；
- 提供 CLI 和 Windows UI；
- 保存许可证清单与运行时来源。

### Workflow Runtime

- 同步只读上游仓库；
- 为每个 workflow 维护独立 `uv` 环境；
- 下载、校验并复用模型资产；
- 初始化 runtime，屏蔽 symlink/copy 与平台差异；
- 提供 `bootstrap`、`doctor` 和稳定推理 worker；
- 保留必要的评估工具，但第一版本不训练基础模型。

旧 demo 的迁移边界见 [VoiceLab demo 迁移与重构](voicelab_migration.md)。

## 3. PolyScribe 目标目录

```text
PolyScribe/
|-- apps/
|   `-- desktop/                 # 后续 .NET Windows UI
|-- contracts/
|   `-- schemas/                 # JSON Schema，跨进程事实源
|-- workflows/
|   |-- separation/
|   |-- muscriptor/
|   |-- chord_btc/
|   |-- game/
|   |-- basic_pitch/
|   `-- score/
|-- src/
|   |-- polyscribe_core/         # 任务、编排、缓存、产物
|   `-- polyscribe_cli/          # CLI 入口
|-- tests/
|   |-- contract/
|   |-- integration/
|   `-- fixtures/
|-- docs/
|-- resources/
|   `-- licenses/                # 分发时的第三方许可快照
|-- vendor/                      # 只读上游仓库，不进入 Git
|-- scripts/                     # 第一版本的可执行流水线入口
|-- pyproject.toml
`-- uv.lock
```

模型代码、权重、用户音频、虚拟环境和运行产物不进入 Git。

## 4. Pipeline

### 4.1 第一版本脚本模式

```text
ingest
  -> normalize_audio
  -> [muscriptor, chord, vocal_separation]    # 可并行
  -> piano_primary + optional_piano_correction
  -> lead_vocal_game
  -> chord_timeline_to_midi
  -> export
```

第一版本的硬交付物是 `piano.mid`、`vocal.mid` 和 `chords.mid`。MusicXML、PDF、歌词、和声拆分和 GUI 均不能阻塞这三条主链路的完成。

### 4.2 Cover 模式

```text
ingest
  -> normalize_audio
  -> vocal_instrumental_separation
  -> lead_backing_separation
  -> [lead_game, lead_f0, lyrics_asr, chord]  # 可并行
  -> lyric_note_alignment
  -> backing_multipitch
  -> harmony_reconstruction
  -> export_cover_package
```

## 5. Worker 协议

MVP 使用“一次执行一个 stage”的子进程模型：

```powershell
uv run -m polyscribe worker run `
  --workflow muscriptor `
  --request C:\jobs\<job-id>\requests\muscriptor.json
```

worker 只向 stdout 写 JSONL 事件，诊断文本写 stderr。每行必须包含：

- `schema_version`
- `job_id`
- `stage_id`
- `event_type`
- `timestamp`
- `payload`

进程退出码非零即为失败；不能以生成空文件或 `success: true` 掩盖异常。

## 6. 状态与恢复

任务状态：

```text
pending -> running -> succeeded
                   -> failed
                   -> cancelled
```

每个 stage 以以下内容计算缓存键：

- 输入文件内容摘要；
- workflow 名与版本/commit；
- 权重文件摘要；
- 规范化参数；
- 契约版本。

只有缓存键完全一致才允许复用。部分文件存在但 manifest 不完整时视为失败产物，不视为缓存命中。

## 7. GPU 与资源调度

- GPU stage 默认串行，避免多个 PyTorch worker 争抢 8GB 显存。
- CPU/I/O stage 可并行，但并发数由配置显式控制。
- OOM 必须记录当前模型、dtype、batch/chunk 参数；UI 提供“以 Medium 重试”等明确动作。
- 自动降级仅生成建议。若未来允许自动降级，必须把实际后端写入 manifest 并提示用户。

## 8. UI 技术路线

桌面端使用 **WinUI 3**（Windows App SDK，unpackaged self-contained），决策见 [ADR 0001](adr/0001-winui3-unpackaged.md)。工程在 `apps/desktop/`。GUI 只消费稳定任务 API 和 `jobs/` 清单，通过 `uv run polyscribe` 启动子进程；不直接加载模型或解析 workflow 私有目录。

脚本和 CLI 的钢琴、人声、和弦 MIDI 流水线仍是产品验收门槛。桌面壳可以并行开发，但不能用 GUI 成功状态掩盖 worker 失败。
