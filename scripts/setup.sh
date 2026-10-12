#!/usr/bin/env bash
# LivePhotoConverter macOS / Linux 环境初始化脚本。
#
# 检查 Python / uv，同步依赖，检测外部工具（ffmpeg / ffprobe / exiftool / hdc），
# 创建运行目录，最后执行 lpconv doctor 输出环境报告。
#
# 用法：
#   bash scripts/setup.sh              # 仅初始化与检测
#   INSTALL_TOOLS=1 bash scripts/setup.sh   # 缺失的 ffmpeg/exiftool 用 brew 安装

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

step() { printf '\n==> %s\n' "$1"; }
ok() { printf '  [OK] %s\n' "$1"; }
warn() { printf '  [WARN] %s\n' "$1"; }
fail() { printf '  [ERROR] %s\n' "$1"; }

step "1/5 检查 Python (>= 3.13)"
PYTHON_BIN=""
for candidate in python3.13 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        version="$("$candidate" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
        major="$(echo "$version" | cut -d. -f1)"
        minor="$(echo "$version" | cut -d. -f2)"
        if [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 13 ]; }; then
            PYTHON_BIN="$candidate"
            ok "Python $version ($candidate)"
            break
        fi
    fi
done
if [ -z "$PYTHON_BIN" ]; then
    fail "未找到 Python 3.13。可执行: uv python install 3.13 或 brew install python@3.13"
    exit 1
fi

step "2/5 检查 uv"
if command -v uv >/dev/null 2>&1; then
    ok "uv $(uv --version | awk '{print $2}')"
else
    fail "未找到 uv。可执行: brew install uv 或 curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

step "3/5 同步依赖并导出 requirements"
uv sync
uv export --no-dev --no-hashes --format requirements-txt -o requirements.txt
uv export --no-hashes --format requirements-txt -o requirements-dev.txt
ok "已生成 requirements.txt 与 requirements-dev.txt"

step "4/5 检测外部工具"
MISSING=()
for tool in ffmpeg ffprobe exiftool hdc; do
    if command -v "$tool" >/dev/null 2>&1; then
        ok "$tool 已安装"
    else
        warn "$tool 未安装或不在 PATH"
        MISSING+=("$tool")
    fi
done

if [ "${INSTALL_TOOLS:-0}" = "1" ] && [ ${#MISSING[@]} -gt 0 ]; then
    for tool in "${MISSING[@]}"; do
        case "$tool" in
            ffmpeg | ffprobe)
                step "安装 ffmpeg (brew)"
                brew install ffmpeg
                break
                ;;
            exiftool)
                step "安装 exiftool (brew)"
                brew install exiftool
                ;;
            hdc)
                warn "hdc 无法自动安装：请安装 DevEco Studio 或 HarmonyOS 命令行工具后加入 PATH"
                ;;
        esac
    done
elif [ ${#MISSING[@]} -gt 0 ]; then
    warn "缺失工具可稍后安装：INSTALL_TOOLS=1 bash scripts/setup.sh"
fi

step "5/5 创建运行目录并执行环境检查"
mkdir -p "$ROOT/Tmp/samples" "$ROOT/Log"
ok "Tmp/ 与 Log/ 就绪"

uv run lpconv doctor
