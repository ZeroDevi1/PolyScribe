# PolyScribe

PolyScribe 是一个面向 Windows 的本地 AI 音乐转录与和声分析工具，目标是把音频转换为可编辑的 MIDI、和弦时间线、MusicXML、PDF 乐谱，以及面向 Synthesizer V Studio / ACE Studio 的人声 Cover 素材。

本仓库将直接重构早期 [VoiceLab](https://github.com/ZeroDevi1/VoiceLab) demo 中的音乐处理能力。VoiceLab 不再作为 PolyScribe 的外部运行时依赖；只迁移其中仍然成立的 `vendor/` 隔离、独立 workflow、共享模型缓存及 `bootstrap/doctor` 思路，并在本仓库重新定义清晰的接口和测试。

第一版本坚持脚本优先：先稳定产出钢琴、人声、简化和声与和弦 MIDI，再扩展完整声部分配、乐谱及 Windows GUI。

## 第一版本

硬产物：`piano.mid`、`vocal.mid`、`harmony.mid`、`chords.json` / `chords.mid`。

- 钢琴 MIDI：MuScriptor 完整混音转录后抽出钢琴轨
- 人声 MIDI：人声分离 → karaoke Lead → GAME Medium（`--language zh`）
- 和声 MIDI：**简化路线** — karaoke Backing → Basic Pitch 多音高单轨；不做 DP 声部分配
- 和弦 MIDI/时间线：MuScriptor 内置 BTC marker → `chords.json` + 可导入 DAW 的 `chords.mid`（`producer: muscriptor-btc`）
- 完整混音转多轨 MIDI：MuScriptor 辅助产物，放在 `stages/transcription/`

```powershell
uv sync
uv run polyscribe bootstrap --workflows separation,muscriptor,game,basic_pitch
uv run polyscribe doctor
uv run polyscribe process "audios\天生冷血 - 陈默之.flac" --targets piano,vocal,harmony,chords
```

等价脚本：`scripts/bootstrap.py`、`scripts/doctor.py`、`scripts/process_song.py`。

前置：Hugging Face 登录并接受 [MuScriptor Medium CC BY-NC](https://huggingface.co/MuScriptor/muscriptor-medium)；本机有 ffmpeg 与 NVIDIA CUDA。GAME 权重由 bootstrap 从 GitHub Releases 下载（CC BY-NC-SA）。

第一版本脚本稳定后再实现：

- 多声部和声重建：Basic Pitch 候选 + PolyScribe Harmony Reconstruction（`harmony_1/2/3.mid`）
- 乐谱：MIDI → MusicXML → PDF
- Cover Mode：导出主唱、和声、歌词、音高曲线及相关 MIDI
- 完整 Windows GUI

## 当前状态

脚本骨架与四条 MIDI workflow 已落地。跑通一首歌仍取决于本机 GPU、Hugging Face 授权与模型下载。实施顺序、验收门槛和风险见 [Roadmap](docs/roadmap.md)。

## 文档

- [文档索引](docs/index.md)
- [产品范围](docs/product_scope.md)
- [技术架构](docs/architecture.md)
- [模型栈与许可](docs/model_stack.md)
- [任务与产物契约](docs/artifact_contract.md)
- [VoiceLab demo 迁移与重构](docs/voicelab_migration.md)
- [实施 Roadmap](docs/roadmap.md)
