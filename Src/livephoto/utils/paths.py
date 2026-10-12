"""项目目录定位与初始化。"""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """返回仓库根目录（Src 的上级目录）。"""
    return Path(__file__).resolve().parents[3]


def ensure_dirs() -> tuple[Path, Path]:
    """确保 Tmp 与 Log 目录存在，返回 (tmp_dir, log_dir)。"""
    root = project_root()
    tmp_dir = root / "Tmp"
    log_dir = root / "Log"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir, log_dir


def create_run_dir(run_id: str) -> Path:
    """在 Tmp 下创建本次运行独立的目录，避免多次运行的中间文件互相干扰。"""
    run_dir = project_root() / "Tmp" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
