"""命令行入口。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass

from livephoto import __version__
from livephoto.media.tools import detect_tool
from livephoto.utils.logging_setup import get_logger, setup_logging
from livephoto.utils.paths import ensure_dirs

EXTERNAL_TOOLS = ("ffmpeg", "ffprobe", "exiftool", "hdc")
REQUIRED_PYTHON = (3, 13)


@dataclass
class CheckResult:
    """单项检查结果。"""

    name: str
    status: str
    detail: str


def _check_python() -> CheckResult:
    version = ".".join(str(part) for part in sys.version_info[:3])
    ok = sys.version_info[:2] >= REQUIRED_PYTHON
    required = ".".join(str(part) for part in REQUIRED_PYTHON)
    return CheckResult(
        name="python",
        status="OK" if ok else "ERROR",
        detail=f"{version} (required >= {required})",
    )


def _check_tools() -> list[CheckResult]:
    results = []
    for tool in EXTERNAL_TOOLS:
        status = detect_tool(tool)
        if status.found:
            detail = status.version or status.path or "found"
            results.append(CheckResult(tool, "OK", detail))
        else:
            results.append(CheckResult(tool, "WARN", "未安装或不在 PATH（M1/M2 前需要）"))
    return results


def _check_dirs(tmp_dir, log_dir) -> list[CheckResult]:
    results = []
    for label, path in (("Tmp", tmp_dir), ("Log", log_dir)):
        writable = os.access(path, os.W_OK)
        results.append(
            CheckResult(
                name=f"dir:{label}",
                status="OK" if writable else "ERROR",
                detail=str(path),
            )
        )
    return results


def _cmd_doctor(args: argparse.Namespace) -> int:
    tmp_dir, log_dir = ensure_dirs()
    run_id = setup_logging(log_dir)
    logger = get_logger(__name__)
    logger.info("doctor 开始，run_id=%s", run_id)

    checks = [_check_python(), *_check_tools(), *_check_dirs(tmp_dir, log_dir)]

    if args.json:
        print(json.dumps({"run_id": run_id, "checks": [vars(c) for c in checks]}, ensure_ascii=False, indent=2))
    else:
        print(f"run_id: {run_id}")
        for check in checks:
            print(f"[{check.status:5}] {check.name:12} {check.detail}")

    failed = [c for c in checks if c.status == "ERROR"]
    logger.info("doctor 结束，ERROR 项 %d 个", len(failed))
    return 1 if failed else 0


def _cmd_not_implemented(args: argparse.Namespace) -> int:
    print(f"命令 `{args.command}` 尚未实现（计划于 M3 提供）")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lpconv", description="动态照片转换工具")
    parser.add_argument("--version", action="version", version=f"lpconv {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="检查运行环境")
    doctor.add_argument("--json", action="store_true", help="以 JSON 输出检查结果")
    doctor.set_defaults(func=_cmd_doctor)

    for name, help_text in (
        ("convert", "执行转换"),
        ("probe", "查看源文件信息"),
        ("verify", "校验转换产物"),
    ):
        pending = sub.add_parser(name, help=f"{help_text}（M3 实现）")
        pending.set_defaults(func=_cmd_not_implemented)

    return parser


def _force_utf8_streams() -> None:
    """Windows 下管道捕获默认按本地代码页解码，强制 UTF-8 输出避免中文乱码。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    """程序入口，返回进程退出码。"""
    _force_utf8_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
