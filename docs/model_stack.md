# 模型栈与许可

本文档是 2026-08-31 的接入基线。模型能力、权重地址和许可可能变化；实现时必须固定 commit、权重摘要和许可证快照。

## 1. 推荐矩阵

| 能力 | 首选 | 备用/复核 | 首版定位 |
|---|---|---|---|
| 完整混音多轨 MIDI | MuScriptor Medium/Large | 暂不设同级替代 | v0.1 主干 |
| 和弦时间线 | BTC | 后续增加可替换后端 | v0.1 主干 |
| Piano stem | Audio Separator / 迁移后的 MSST workflow | 其他 UVR/MDX/RoFormer 模型 | v0.1 可选 |
| 干净钢琴转 MIDI | Basic Pitch | 钢琴专精模型 | v0.1 校正支路 |
| 主唱转 MIDI | GAME Medium | ROSVOT | v0.2 主干 |
| 主唱连续 F0 | RMVPE | CREPE | v0.2 |
| 混合和声多音高 | Basic Pitch | MuScriptor 人声轨候选 | v0.2 候选生成 |
| 和声声部分配 | 自研 DP/Viterbi/最小费用流 | 人工编辑 | v0.2 核心差异化 |
| 歌词识别 | Paraformer（中文）/可插拔 ASR | Whisper/Parakeet 系 | v0.2 |
| Note-Lyric 对齐 | GAME boundary + aligner | ROSVOT alignment | v0.2 |
| 乐谱 | MuScriptor sheets 或 MIDI→MusicXML→MuseScore | 独立 exporter | v0.1 |

## 2. MuScriptor

官方仓库：[muscriptor/muscriptor](https://github.com/muscriptor/muscriptor)

已核实能力：

- 完整录音转多乐器 MIDI；
- `small` 103M、`medium` 307M、`large` 1.4B；
- instrument conditioning；
- Windows GPU 需要明确选择 CUDA PyTorch backend；
- 可输出 MIDI、MusicXML 和 PDF（PDF 依赖 MuseScore 4+）。

接入策略：

- 默认使用 Medium，作为速度、显存与质量的稳健基线；
- Large 作为 RTX 5060 的“高质量配置”，必须先以固定测试集测峰值显存和处理速度，再决定是否成为默认；
- 将 instrument list、model、dtype、batch size 和 prelude forcing 写入任务参数；
- 先保留原始 MIDI，再由 PolyScribe 做轨道规范化和冲突标注。

许可说明：代码为 MIT；官方模型权重为 CC BY-NC 4.0，且下载需要用户接受 Hugging Face 条款并认证。本项目明确为非商业用途，因此可将它作为首选后端，但仍由用户完成授权和下载，不把权重提交到 Git。

## 3. BTC

官方仓库：[jayg996/BTC-ISMIR19](https://github.com/jayg996/BTC-ISMIR19)

BTC 将 CQT 特征映射为和弦标签，可输出 major/minor 或较大词表结果。原实现来自 ISMIR 2019，依赖栈较旧，因此不能直接成为 PolyScribe 主环境依赖。

接入策略：

- 在独立 workflow 中冻结兼容依赖；
- 统一转换为 `chords.json`，不泄漏原项目的 `.lab` 细节；
- 保留无和弦 `N`、原始标签、归一化标签和置信度；
- v0.1 前用流行歌、转调、slash chord、短时和弦四类样本评估；若维护成本或准确率不达标，通过同一契约替换后端。

许可：仓库标注 MIT；模型 checkpoint 的来源与可分发性仍需单独形成资产清单。

## 4. Basic Pitch

官方仓库：[spotify/basic-pitch](https://github.com/spotify/basic-pitch)

它是轻量、乐器无关、支持 polyphonic/pitch bend 的 AMT；官方明确说明在单一乐器输入上效果最好。因此它不作为“完整混音直接提取钢琴”的主干，而用于：

- piano stem 的二次转录；
- backing vocal 的多音高候选；
- 快速 CPU/轻量回退。

候选输出必须经过最短音符、间隙合并、音域、和弦一致性与声部连续性后处理。

## 5. GAME

官方仓库：[openvpi/GAME](https://github.com/openvpi/GAME)

GAME 专门把 singing voice 转为 MIDI，支持噪声、混响或伴奏残留的 separated vocal，并能结合已知 word boundary。官方仓库支持导出 ONNX，但不提供完整 ONNX 推理实现；[openvpi/dataset-tools](https://github.com/openvpi/dataset-tools) 的 GameInfer 提供四模型 ONNX pipeline，并把 Windows 10/11 + DirectML 列为主要平台。

接入策略：

- v0.2 先以 GAME Medium 的官方 Python/PyTorch 推理建立准确率基线；
- 再用 GameInfer/ONNX 做 Windows 原生部署 spike，比较输出一致性与 DirectML/CUDA 性能；
- GAME 是单旋律主唱转录器，不直接处理同时出现多个和声音高的 backing vocal；
- 模型输出的浮点音高、边界、语言、采样步数与阈值全部进入 manifest。

GAME 代码仓库标注 MIT；发布前仍要核对所选 release 权重和任何附带模型的独立条款。

## 6. 分离模型

[python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator) 能统一调用 MDX、VR、Demucs 和 MDXC/UVR 系模型，也覆盖 vocal、piano、guitar、denoise、dereverb 等任务。早期 VoiceLab demo 中的 MSST workflow 只作为迁移参考；在 PolyScribe 内重新实现稳定入口、路径解析和测试，不直接依赖旧代码运行。

不要把“框架许可”等同于“所有可下载模型均可分发”。每个模型文件必须记录：

- 下载 URL 与发布日期；
- SHA-256；
- 模型名称和任务；
- 权重许可或来源页；
- 是否允许再分发、商用和衍生用途。

## 7. 和声重建不是单模型问题

Backing vocal 中同时存在多条声部时，Basic Pitch 只负责产生候选音符。PolyScribe 负责求解时间连续的声部：

```text
cost = pitch_jump
     + voice_crossing
     + register_penalty
     + chord_mismatch
     + onset_fragmentation
     + optional_parallel_motion
```

首版采用分帧候选 + 动态规划/Viterbi；声部数量为显式参数或由候选上限估计。无法可靠分配的音符保留在 `unassigned.mid` 并标记原因。

## 8. 评测门槛

每个 backend 合入前至少记录：

- 20–30 秒 smoke fixtures 与 3–5 分钟完整歌曲；
- 运行时间、峰值显存、峰值内存；
- MIDI note onset/offset/pitch 指标或可复核对照；
- 和弦 weighted chord symbol recall；
- 分离 SDR 或至少固定盲听样本；
- Windows 目标机、驱动、CUDA/DirectML、模型和 commit。
