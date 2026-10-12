"""外部命令行工具的探测。"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass

ENV_PREFIX = "LPCONV_"


@dataclass
class ToolStatus:
    """外部工具的探测结果。"""

    name: str
    found: bool
    path: str | None = None
    version: str | None = None
    error: str | None = None


VERSION_ARGS: dict[str, list[str]] = {
    "ffmpeg": ["-version"],
    "ffprobe": ["-version"],
    "exiftool": ["-ver"],
    "hdc": ["-v"],
}


def resolve_executable(name: str) -> str | None:
    """解析可执行文件路径：优先环境变量 `LPCONV_<NAME>_PATH`，其次 PATH。"""
    override = os.environ.get(f"{ENV_PREFIX}{name.upper()}_PATH")
    return override or shutil.which(name)


def detect_tool(name: str) -> ToolStatus:
    """探测工具是否可用；未登记版本参数的工具只检测存在性。"""
    path = resolve_executable(name)
    if path is None:
        return ToolStatus(name=name, found=False, error="not found in PATH")

    args = VERSION_ARGS.get(name)
    if args is None:
        return ToolStatus(name=name, found=True, path=path)

    try:
        result = subprocess.run(
            [path, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return ToolStatus(name=name, found=True, path=path, error=str(exc))

    lines = (result.stdout or result.stderr or "").strip().splitlines()
    return ToolStatus(name=name, found=True, path=path, version=lines[0] if lines else None)
