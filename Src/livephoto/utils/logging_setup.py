"""日志初始化：控制台 + Log/<date>.log，按 run_id 串联。"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def new_run_id() -> str:
    """生成一次运行的唯一标识。"""
    return f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"


def setup_logging(log_dir: Path, run_id: str | None = None, level: int = logging.INFO) -> str:
    """初始化根日志器，返回本次运行的 run_id。"""
    log_dir.mkdir(parents=True, exist_ok=True)
    current_run_id = run_id or new_run_id()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = logging.FileHandler(log_dir / f"{datetime.now():%Y-%m-%d}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    return current_run_id


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器。"""
    return logging.getLogger(name)
