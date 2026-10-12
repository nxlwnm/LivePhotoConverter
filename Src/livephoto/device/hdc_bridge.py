"""鸿蒙设备接入：基于 hdc 的最小实现。"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from livephoto.media.tools import resolve_executable

CONNECTED = "Connected"
UNAUTHORIZED = "Unauthorized"
USB = "USB"
KNOWN_STATES = (CONNECTED, UNAUTHORIZED, "Offline", "Disconnected", "Ready")


@dataclass
class DeviceInfo:
    """一台已连接的设备。"""

    serial: str
    state: str


def _parse_line(line: str) -> DeviceInfo | None:
    """解析 `hdc list targets -v` 的一行，只保留 USB 传输的设备（串口等非 USB 设备忽略）。"""
    parts = [part.strip() for part in line.split("\t") if part.strip()]
    if len(parts) < 3 or parts[1] != USB:
        return None

    state = next((part for part in parts[2:] if part in KNOWN_STATES), "Unknown")
    return DeviceInfo(serial=parts[0], state=state)


def list_devices(executable: str | None = None) -> list[DeviceInfo]:
    """列出 hdc 可见的 USB 设备；hdc 不可用时返回空列表。"""
    exe = executable or resolve_executable("hdc")
    if exe is None:
        return []

    result = subprocess.run(
        [exe, "list", "targets", "-v"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )

    devices: list[DeviceInfo] = []
    for line in (result.stdout or "").splitlines():
        device = _parse_line(line)
        if device is not None:
            devices.append(device)
    return devices
