# PolyScribe 文档

## 从这里开始

1. [产品范围](product_scope.md)：要解决的问题、MVP 与非目标。
2. [技术架构](architecture.md)：进程边界、模块划分与数据流。
3. [模型栈与许可](model_stack.md)：各任务的首选/备用模型、接入方式和风险。
4. [任务与产物契约](artifact_contract.md)：任务目录、清单文件与中间结果格式。
5. [VoiceLab demo 迁移与重构](voicelab_migration.md)：哪些思路保留、哪些实现废弃，以及如何迁入本仓库。
6. [实施 Roadmap](roadmap.md)：阶段、交付物和验收标准。
7. [ADR 0001：WinUI 3 unpackaged 桌面壳](adr/0001-winui3-unpackaged.md)

## 核心原则

- Windows Native 优先，RTX 5060 8GB 为首个 GPU 验证基线；CPU 模式只承诺诊断和轻量后端。
- 模型可以替换，PolyScribe 的任务和产物契约不能绑定某个模型的内部对象。
- 上游仓库保持只读；本项目不把补丁直接写入 `vendor/`。
- 所有模型输出先落为可追踪的中间产物，再做融合和导出。
- 对低置信度结果显式标注，不用静默修正制造“看似正确”的 MIDI。
- 项目明确为非商业用途；仍需记录并遵守每个代码仓库、模型权重和资产的许可条件。
- 在钢琴、人声、和弦三条脚本流水线验收完成前，不进入完整 GUI 开发。
