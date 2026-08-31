# ADR 0001：WinUI 3 unpackaged 桌面壳

## Status

Accepted

## Context

桌面端需要导入本地音频、启动子进程 CLI、读写 `jobs/` 清单，并在关闭后恢复任务。架构允许 WinUI 3 或 WPF。MSIX 包装能提供包身份，但会把工作目录和文件系统权限变成安装布局问题；本产品是非商业本地工具，GUI 必须与仓库内的 `uv` workflow 共存。

## Decision

使用 WinUI 3（Windows App SDK 2.4）作为唯一 UI 技术栈。应用以 unpackaged + self-contained 运行，通过 `uv run polyscribe` 消费已稳定的任务 API，不在 GUI 进程加载模型。

## Consequences

- 可直接访问仓库路径、任务目录和任意音频文件，FileOpenPicker 用窗口句柄关联。
- 没有 Store 身份、协议激活和清单式文件关联；若以后需要这些能力，再评估 packaged with external location。
- 分发体积包含 Windows App SDK 运行时；开发期用 `dotnet run --project apps/desktop/PolyScribe.App`。
