# LivePhotoConverter

实现 Android / iOS / 原生鸿蒙（HarmonyOS）平台动态照片互转的工具链。

当前处于**立项准备阶段**，仓库中只有项目文档，尚无业务代码。

## 进展

- 第一期目标：HarmonyOS（鸿蒙 7）→ iOS Live Photo；
- 里程碑：M0 脚手架与环境 → M1 设备环境调试 → M2 技术方案验证（Go/No-Go）→ M3 首个 Converter 实施。

## 技术栈

- Python 3.13+，环境管理使用 uv（`pyproject.toml` + `uv.lock` 为依赖单一真源）；
- 支持 Windows 与 macOS，环境脚本见 `scripts/`（M0 提供）；
- 媒体处理复用 ffmpeg/ffprobe、exiftool 等命令行工具。

## 目录

| 目录 | 用途 |
| --- | --- |
| `Doc/` | 技术规范、调研与验证报告、开发须知（`Doc/evidence/` 存放证据） |
| `Src/` | 源码与测试 |
| `scripts/` | 环境初始化与工程辅助脚本 |
| `native/` | 非 Python 组件，仅在确有必要时引入并显式标记（见 `Doc/30` N1.8） |
| `Tmp/` | 临时文件（`Tmp/samples/` 放样本，不入库） |
| `Log/` | 运行日志（不入库） |

## 快速开始

Windows（PowerShell）：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
uv run lpconv doctor
```

macOS / Linux：

```bash
bash scripts/setup.sh
uv run lpconv doctor
```

`setup` 会检查 Python 与 uv、同步依赖、检测外部工具（ffmpeg / ffprobe / exiftool / hdc）、创建 `Tmp/` 与 `Log/`，最后输出环境报告。当前仅 `doctor` 可用，`convert` / `probe` / `verify` 将在 M3 提供。

## 开始之前

完整的项目目标、范围、架构与开发规范见 [`Doc/00-项目总览.md`](Doc/00-项目总览.md)，文档索引在其中。环境细节与依赖清单见 [`Doc/40-环境搭建与依赖管理.md`](Doc/40-环境搭建与依赖管理.md)。

## 许可

MIT，见 [LICENSE](LICENSE)。
