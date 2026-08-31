# PolyScribe Desktop

WinUI 3 桌面壳，消费仓库根目录的 `uv run polyscribe` CLI，不在 GUI 进程做推理。

## 要求

- Windows 10 1809 或更高
- .NET 10 SDK
- 已能运行 `uv run polyscribe doctor` 的仓库环境（转录时）

## 运行

```powershell
dotnet run --project apps/desktop/PolyScribe.App -c Debug
```

Visual Studio / Cursor 使用启动配置 `PolyScribe (Unpackaged)`。

## 交互

- **转录**：拖放或浏览音频，选择 piano / vocal / harmony / chords，开始后跳到任务详情。
- **任务**：读取 `jobs/*/manifest.json`；筛选、打开输出目录、进入预览。
- **预览**：规范化 WAV 波形、和弦时间线、所选 MIDI 的钢琴卷帘，以及系统播放控件。
- **设置**：主题、仓库根、任务目录、`polyscribe doctor`。

快捷键：`Ctrl+N` 转录，`Ctrl+J` 任务，`Ctrl+P` 预览，`Ctrl+O` 打开音频（转录页）。
