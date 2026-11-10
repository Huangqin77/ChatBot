$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '../backend')
try {
    if (-not (Test-Path -LiteralPath './.venv/Scripts/python.exe')) {
        throw '请先按 README 创建 backend/.venv 并安装依赖。'
    }
    & ./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --ws-max-size 16384
} finally {
    Pop-Location
}
