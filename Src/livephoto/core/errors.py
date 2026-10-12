"""统一错误码与异常类型。"""

from __future__ import annotations


class ErrorCode:
    """错误码常量，集中维护，新增需同步文档。"""

    ENV_PYTHON_VERSION = "E_ENV_PYTHON_VERSION"
    ENV_TOOL_MISSING = "E_ENV_TOOL_MISSING"
    ENV_DIR_NOT_WRITABLE = "E_ENV_DIR_NOT_WRITABLE"
    INPUT_NOT_FOUND = "E_INPUT_NOT_FOUND"
    PARSE_FAILED = "E_PARSE_FAILED"
    TRANSFORM_FAILED = "E_TRANSFORM_FAILED"
    WRITE_FAILED = "E_WRITE_FAILED"
    DEVICE_UNAVAILABLE = "E_DEVICE_UNAVAILABLE"


class LivePhotoError(Exception):
    """项目异常基类，携带可机读错误码。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class EnvError(LivePhotoError):
    """环境不可用：Python 版本、外部工具、目录权限等。"""


class InputError(LivePhotoError):
    """输入不满足要求：文件不存在、格式不可识别等。"""


class ParseError(LivePhotoError):
    """解析失败。"""


class TransformError(LivePhotoError):
    """兼容化变换失败。"""


class WriteError(LivePhotoError):
    """生成目标格式失败。"""


class DeviceError(LivePhotoError):
    """设备接入失败。"""
