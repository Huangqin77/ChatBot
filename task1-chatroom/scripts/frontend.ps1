$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '../frontend')
try {
    & npm.cmd run dev
} finally {
    Pop-Location
}
