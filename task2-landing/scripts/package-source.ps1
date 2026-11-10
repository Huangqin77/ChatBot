param([string]$OutputPath = '')
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if (-not $OutputPath) { $OutputPath = Join-Path (Split-Path $projectRoot -Parent) 'task2-landing-source.zip' }
$archivePath = [IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $archivePath) { throw "目标压缩包已存在，请选择新文件名：$archivePath" }

# 白名单打包，避免把凭据、node_modules、Git 元数据和测试运行产物带给面试官。
$folders = @('src', 'public', 'tests', 'scripts')
$rootFiles = @('package.json', 'package-lock.json', 'index.html', 'tsconfig.json', 'vite.config.ts', 'playwright.config.ts', 'vercel.json', '.env.example', '.gitignore', '.vercelignore', 'README.md', 'DELIVERY.md')
Add-Type -AssemblyName System.IO.Compression
$zipStream = [IO.File]::Open($archivePath, [IO.FileMode]::CreateNew)
$zip = [IO.Compression.ZipArchive]::new($zipStream, [IO.Compression.ZipArchiveMode]::Create, $false)
$entryCount = 0
try {
  $files = @($rootFiles | ForEach-Object {
    $filePath = Join-Path $projectRoot $_
    if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) { throw "缺少交付文件：$_" }
    Get-Item -LiteralPath $filePath
  })
  foreach ($folder in $folders) { $files += Get-ChildItem -LiteralPath (Join-Path $projectRoot $folder) -Recurse -File }
  foreach ($file in $files) {
    $relative = [IO.Path]::GetRelativePath($projectRoot, $file.FullName).Replace('\', '/')
    if ($relative -match '(^|/)(node_modules|\.git|\.vercel)(/|$)' -or ($file.Name -like '.env*' -and $file.Name -ne '.env.example') -or $file.Extension -in @('.pem', '.key', '.zip')) { throw "禁止打包敏感或无关文件：$relative" }
    $entry = $zip.CreateEntry("task2-landing/$relative", [IO.Compression.CompressionLevel]::Optimal)
    $entryStream = $entry.Open()
    $sourceStream = [IO.File]::OpenRead($file.FullName)
    try { $sourceStream.CopyTo($entryStream) } finally { $sourceStream.Dispose(); $entryStream.Dispose() }
    $entryCount++
  }
} finally { $zip.Dispose(); $zipStream.Dispose() }
$sha256 = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
Write-Output "Archive: $archivePath"
Write-Output "Entries: $entryCount"
Write-Output "SHA256: $sha256"
