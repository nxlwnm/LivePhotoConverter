<#
.SYNOPSIS
    LivePhotoConverter Windows 环境初始化脚本。

.DESCRIPTION
    检查 Python / uv，同步依赖，检测外部工具（ffmpeg / ffprobe / exiftool / hdc），
    创建运行目录，最后执行 lpconv doctor 输出环境报告。

.PARAMETER InstallTools
    尝试通过 winget 自动安装缺失的 ffmpeg / exiftool（hdc 需手动安装）。
#>
[CmdletBinding()]
param(
    [switch]$InstallTools
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Write-Step($Message) { Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-OkItem($Message) { Write-Host "  [OK] $Message" -ForegroundColor Green }
function Write-WarnItem($Message) { Write-Host "  [WARN] $Message" -ForegroundColor Yellow }
function Write-FailItem($Message) { Write-Host "  [ERROR] $Message" -ForegroundColor Red }

Write-Step "1/5 检查 Python (>= 3.13)"
$pythonOk = $false
if (Get-Command py -ErrorAction SilentlyContinue) {
    $version = & py -3.13 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
    if ($LASTEXITCODE -eq 0 -and $version) {
        Write-OkItem "Python $version (py -3.13)"
        $pythonOk = $true
    }
}
if (-not $pythonOk -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $version = & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
    Write-WarnItem "PATH 中的 python 为 $version，项目要求 >= 3.13（可用 py -3.13 或 uv python install 3.13）"
}
if (-not $pythonOk) {
    Write-FailItem "未找到 Python 3.13。请安装后重跑，或执行: uv python install 3.13"
    exit 1
}

Write-Step "2/5 检查 uv"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    $uvVersion = ((uv --version) -split ' ' | Select-Object -Index 1)
    Write-OkItem "uv $uvVersion"
}
else {
    Write-FailItem "未找到 uv。请执行: winget install astral-sh.uv"
    exit 1
}

Write-Step "3/5 同步依赖并导出 requirements"
uv sync
if ($LASTEXITCODE -ne 0) { exit 1 }
uv export --no-dev --no-hashes --format requirements-txt -o requirements.txt
uv export --no-hashes --format requirements-txt -o requirements-dev.txt
Write-OkItem "已生成 requirements.txt 与 requirements-dev.txt"

Write-Step "4/5 检测外部工具"
$tools = @("ffmpeg", "ffprobe", "exiftool", "hdc")
$missing = @()
foreach ($tool in $tools) {
    if (Get-Command $tool -ErrorAction SilentlyContinue) {
        Write-OkItem "$tool 已安装"
    }
    else {
        Write-WarnItem "$tool 未安装或不在 PATH"
        $missing += $tool
    }
}

if ($InstallTools -and $missing.Count -gt 0) {
    if ($missing -contains "ffmpeg") {
        Write-Step "安装 ffmpeg (winget)"
        winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
    }
    if ($missing -contains "exiftool") {
        Write-Step "安装 exiftool (winget)"
        winget install --id OliverBetz.ExifTool -e --accept-source-agreements --accept-package-agreements
    }
    if ($missing -contains "hdc") {
        Write-WarnItem "hdc 无法自动安装：请安装 DevEco Studio 或 HarmonyOS 命令行工具后把 hdc 加入 PATH"
    }
    Write-WarnItem "winget 安装后需重开终端使 PATH 生效"
}
elseif ($missing.Count -gt 0) {
    Write-WarnItem "缺失工具可稍后安装：重新执行 .\\scripts\\setup.ps1 -InstallTools"
}

Write-Step "5/5 创建运行目录并执行环境检查"
New-Item -ItemType Directory -Force -Path (Join-Path $Root "Tmp\\samples") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root "Log") | Out-Null
Write-OkItem "Tmp/ 与 Log/ 就绪"

uv run lpconv doctor
exit $LASTEXITCODE
