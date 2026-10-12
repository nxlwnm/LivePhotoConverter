"""骨架冒烟测试：验证目录、异常与工具探测的基本行为。"""

from __future__ import annotations

import subprocess
import sys

from livephoto.core.errors import ErrorCode, LivePhotoError
from livephoto.media.tools import detect_tool
from livephoto.utils.paths import create_run_dir, ensure_dirs, project_root


def test_project_root_has_pyproject() -> None:
    assert (project_root() / "pyproject.toml").is_file()


def test_ensure_dirs_creates_tmp_and_log() -> None:
    tmp_dir, log_dir = ensure_dirs()
    assert tmp_dir.is_dir() and log_dir.is_dir()


def test_create_run_dir_isolated_under_tmp() -> None:
    run_dir = create_run_dir("test-run-id")
    assert run_dir.is_dir()
    assert run_dir.parent.name == "Tmp"


def test_error_carries_code() -> None:
    error = LivePhotoError(ErrorCode.INPUT_NOT_FOUND, "missing")
    assert error.code == "E_INPUT_NOT_FOUND"
    assert "missing" in str(error)


def test_detect_tool_missing() -> None:
    status = detect_tool("definitely-not-a-real-tool-xyz")
    assert status.found is False


def test_cli_doctor_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "livephoto.cli.main", "doctor"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=project_root() / "Src",
        check=False,
    )
    assert result.returncode == 0
    assert "run_id" in result.stdout
