# VoiceLab demo 迁移与重构

## 1. 定位

[VoiceLab](https://github.com/ZeroDevi1/VoiceLab) 是早期验证语音和音频 workflow 的 demo。其代码实现、CLI 组织和平台适配不作为 PolyScribe 的长期基础，也不作为外部运行时依赖。

PolyScribe 在当前仓库内重新实现第一版本需要的能力。迁移对象是经过验证的设计经验、配置和必要脚本逻辑，不是原样复制整个仓库。

本次盘点参考 VoiceLab `f6432ca489b9fcff1da44e995b116d9b2c2cdbcc`（2026-03-17）。真正迁移时必须重新核对源文件和上游版本。

## 2. 可以保留的设计

- `vendor/` 与自有代码分离，上游仓库保持只读且不进入 Git；
- 不同模型使用独立 workflow 和 `uv` 环境，隔离冲突依赖；
- 大模型进入共享 assets cache，runtime 只保存链接、复制品或必要配置；
- 用 `bootstrap` 统一准备 vendor、环境、资产和 runtime；
- 用只读 `doctor` 检查系统依赖、GPU、模型和 runtime；
- 路径遵循 CLI 参数、环境变量、仓库默认值的明确优先级；
- workflow 通过脚本和测试包装上游实现，不直接修改 vendor。

## 3. 不迁移的实现

- VoiceLab 当前的大型单文件 CLI；
- WSL 或个人盘符硬编码；
- 面向 CosyVoice、RVC、GPT-SoVITS 训练的无关流程；
- 针对个人角色数据、训练产物和同步脚本的约定；
- 依赖隐式目录布局的 runtime 调用；
- 未定义 schema 的 stdout 文本解析；
- 无测试或靠“文件存在”判断成功的逻辑。

原 demo 保持只读参考，迁移完成后 PolyScribe 不通过环境变量或路径回连 VoiceLab。

## 4. 在 PolyScribe 中重构的 workflow

```text
workflows/
|-- separation/       # vocal/instrumental、lead/backing、可选 piano stem
|-- muscriptor/       # piano 与多轨 MIDI
|-- chord_btc/        # chord timeline
|-- game/             # lead vocal MIDI
|-- basic_pitch/      # piano/和声候选校正
`-- score/            # 后续 MusicXML/PDF
```

每个 workflow 至少包含：

- `pyproject.toml`、`uv.lock` 和固定 Python 版本；
- `README.md`，说明输入、输出、模型、平台、许可和已知限制；
- `tools/bootstrap.py` 或等价资产准备入口；
- `tools/infer.py` 或等价稳定推理入口；
- 面向统一请求/事件/产物 schema 的 adapter；
- 20–30 秒 fixture smoke test；
- Windows + NVIDIA CUDA 的实机验证记录。

## 5. 重构顺序

### Step 1：只读盘点

- 列出 VoiceLab 中与 MSST、资产缓存、runtime 初始化有关的源文件；
- 标记可复用配置、纯函数、平台绑定逻辑和应废弃逻辑；
- 记录上游 vendor commit 与模型文件来源。

### Step 2：先定义契约

- 在 `contracts/schemas/` 定义 request、event、artifact 和 error；
- 写 contract tests；
- 再实现 workflow adapter，避免从旧 CLI 反推接口。

### Step 3：逐条迁移

迁移顺序为：

1. separation；
2. muscriptor；
3. chord_btc；
4. game；
5. basic_pitch；
6. score。

每条 workflow 独立通过 smoke test 后再接入总 pipeline。

### Step 4：删除兼容桥

迁移期间若存在临时 VoiceLab adapter，必须有删除条件和测试覆盖。第一版发布前不保留双实现、旧路径 fallback 或同时维护两套 bootstrap。

## 6. 新 CLI

统一入口直接属于 PolyScribe：

```powershell
uv run polyscribe bootstrap --workflows separation,muscriptor,chord_btc,game
uv run polyscribe doctor
uv run polyscribe worker run --workflow game --request request.json
uv run polyscribe process song.flac --targets piano,vocal,chords
```

`doctor` 只检查并给出修复建议；不得下载模型、修改环境或自动登录。`worker` stdout 只输出 JSONL，普通日志写 stderr。

## 7. 第一版本迁移完成标准

- PolyScribe 不需要 VoiceLab 目录即可运行；
- 新环境只通过当前仓库的 bootstrap/doctor 完成准备和诊断；
- `piano.mid`、`vocal.mid`、`chords.mid` 均由当前仓库脚本生成；
- 所有输出可追踪到输入摘要、workflow 版本、vendor commit、权重摘要和参数；
- VoiceLab 中被迁移的旧逻辑不再有第二份运行事实源；
- 中文路径、空格路径、Windows Native 和 RTX 5060 8GB 场景有实机证据。

