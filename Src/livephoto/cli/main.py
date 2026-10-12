"""命令行入口。"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass

from livephoto import __version__
from livephoto.device.hdc_bridge import CONNECTED, UNAUTHORIZED, list_devices
from livephoto.media.tools import detect_tool
from livephoto.utils.logging_setup import get_logger, setup_logging
from livephoto.utils.paths import create_run_dir, ensure_dirs

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


def _check_harmonyos_devices() -> list[CheckResult]:
    """列出 hdc 可见的设备，并标注授权状态。"""
    try:
        devices = list_devices()
    except (OSError, subprocess.SubprocessError) as exc:
        return [CheckResult("device:harmonyos", "WARN", f"hdc 调用失败：{exc}")]

    if not devices:
        return [CheckResult("device:harmonyos", "WARN", "未检测到设备（hdc list targets 为空）")]

    results = []
    for device in devices:
        if device.state == CONNECTED:
            results.append(CheckResult(f"device:{device.serial}", "OK", CONNECTED))
        elif device.state == UNAUTHORIZED:
            results.append(
                CheckResult(f"device:{device.serial}", "WARN", "未授权：请在设备上允许 USB 调试（必要时重插数据线）")
            )
        else:
            results.append(CheckResult(f"device:{device.serial}", "WARN", device.state))
    return results


def _check_ios_device() -> CheckResult | None:
    """Windows 下通过 Apple Mobile Device Service 判断 iOS 设备服务是否可用。"""
    if platform.system() != "Windows":
        return None

    result = subprocess.run(
        ["sc", "query", "Apple Mobile Device Service"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    running = "RUNNING" in (result.stdout or "").upper()
    detail = (
        "Apple Mobile Device Service 运行中（仅表示服务可用，不代表设备已连接）"
        if running
        else "未检测到 Apple Mobile Device Service（需安装 iTunes 或 Apple 设备支持）"
    )
    return CheckResult("device:ios", "OK" if running else "WARN", detail)


def _cmd_doctor(args: argparse.Namespace) -> int:
    tmp_dir, log_dir = ensure_dirs()
    run_id = setup_logging(log_dir)
    run_dir = create_run_dir(run_id)
    logger = get_logger(__name__)
    logger.info("doctor 开始，run_id=%s", run_id)

    checks = [
        _check_python(),
        *_check_tools(),
        *_check_dirs(tmp_dir, log_dir),
        CheckResult("dir:run", "OK", str(run_dir)),
    ]
    ios = _check_ios_device()
    if ios is not None:
        checks.append(ios)
    checks.extend(_check_harmonyos_devices())

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
