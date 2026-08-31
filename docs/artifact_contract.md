# 任务与产物契约

## 1. 任务目录

```text
jobs/<job-id>/
|-- input/
|   `-- source.flac
|-- requests/
|-- logs/
|-- stages/
|   |-- normalize/
|   |-- separation/
|   |-- transcription/
|   |-- chord/
|   |-- vocal/
|   `-- score/
|-- output/
|   |-- audio/
|   |-- instruments/
|   |-- vocals/
|   |-- harmony/
|   `-- score/
|-- events.jsonl
`-- manifest.json
```

实际用户目录可配置；以上结构是逻辑契约。原始输入默认不复制时，`manifest.json` 必须保存绝对路径和内容摘要，并明确 `input_mode: reference`。

## 2. Manifest 最小字段

```json
{
  "schema_version": "0.1.0",
  "job_id": "uuid",
  "mode": "transcribe",
  "status": "succeeded",
  "created_at": "RFC3339 timestamp",
  "input": {
    "path": "C:\\Music\\song.flac",
    "sha256": "hex",
    "duration_seconds": 240.0
  },
  "environment": {
    "os": "Windows",
    "gpu": "NVIDIA GeForce RTX 5060",
    "polyscribe_commit": "git sha"
  },
  "stages": [],
  "artifacts": [],
  "warnings": []
}
```

路径在 JSON 中使用规范化绝对路径；展示层可以转换为用户友好的相对路径。

## 3. Stage 记录

每个 stage 必须记录：

- `stage_id`、`workflow`、`status`；
- `started_at`、`finished_at`、`duration_seconds`；
- 参数的规范化 JSON；
- vendor commit、包版本、权重 SHA-256；
- 输入和输出 artifact id；
- 退出码、错误类型和日志路径；
- 峰值显存/内存（可获取时）；
- `cache_key` 与是否缓存命中。

## 4. Artifact 记录

```json
{
  "id": "piano-midi-primary",
  "kind": "midi",
  "role": "instrument.piano.primary",
  "path": "output/instruments/piano.mid",
  "sha256": "hex",
  "producer_stage": "muscriptor",
  "confidence": 0.82,
  "metadata": {
    "model": "muscriptor-medium",
    "instrument": "acoustic_piano"
  }
}
```

`confidence` 必须说明语义。若后端不提供可比较置信度，则值为 `null`，不能人为填入看似精确的数字。

## 5. 标准输出

### Transcribe

```text
output/
|-- instruments/
|   |-- piano.mid
|   |-- piano.alternate.mid
|   |-- bass.mid
|   |-- guitar.mid
|   `-- drums.mid
|-- vocals/
|   |-- vocal.mid
|   `-- harmony.mid
|-- harmony/
|   |-- chords.json
|   |-- chords.mid
|   |-- key.json
|   `-- tempo.json
`-- score/
    |-- full.musicxml
    |-- full.pdf
    `-- lead_sheet.musicxml
```

第一版本的必需产物是：

- `instruments/piano.mid`
- `vocals/vocal.mid`
- `vocals/harmony.mid`（Backing stem 上的 Basic Pitch 多音高，单轨简化候选；**不是** Cover 模式的 `harmony_1/2/3` 声部分配）
- `harmony/chords.json`
- `harmony/chords.mid`

其他乐器轨、alternate MIDI、`unassigned.mid` 和 `score/` 属于可选或后续阶段产物；缺少它们不能让核心任务失败。Backing 近静音时允许 `harmony.mid` 无音符，但必须是合法 MIDI 并在 manifest 中写 warning。

### Cover

```text
output/
|-- audio/
|   |-- instrumental.wav
|   |-- lead_vocal.wav
|   `-- backing_vocal.wav
|-- vocals/
|   |-- lead.mid
|   |-- lead_pitch.json
|   |-- lead_lyrics.json
|   |-- harmony_1.mid
|   |-- harmony_2.mid
|   |-- harmony_3.mid
|   `-- unassigned.mid
`-- packages/
    |-- synthv/
    `-- ace/
```

## 6. `chords.json`

```json
{
  "schema_version": "0.1.0",
  "timebase": "seconds",
  "segments": [
    {
      "start": 0.0,
      "end": 4.0,
      "label": "C:maj7",
      "raw_label": "C:maj7",
      "confidence": null
    }
  ]
}
```

和弦采用统一规范标签；无法映射时保留 `raw_label` 并添加 warning，不得丢弃。

## 7. 版本策略

- `schema_version` 使用语义版本。
- 新增可选字段属于 minor 变更；删除字段、改变单位或状态语义属于 major 变更。
- 读取方必须拒绝未知 major 版本，并给出明确迁移提示。
- 所有时间默认秒，浮点值以原始音频起点为零；MIDI tick 只存在于 MIDI 文件或明确的 tempo map 中。
