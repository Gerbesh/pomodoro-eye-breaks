$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Release = Join-Path $Root "release"
$Dist = Join-Path $Root "dist"
$Build = Join-Path $Root "build"
$Icon = Join-Path $Root "assets\app.ico"
$Entry = Join-Path $Root "src\focus_breaks\main.py"

New-Item -ItemType Directory -Force $Release | Out-Null
Remove-Item -Recurse -Force $Dist, $Build -ErrorAction SilentlyContinue

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name FocusBreaks `
  --icon $Icon `
  --add-data "$Icon;assets" `
  $Entry

$Exe = Join-Path $Dist "FocusBreaks.exe"
$ReleaseExe = Join-Path $Release "FocusBreaks.exe"
Copy-Item -LiteralPath $Exe -Destination $ReleaseExe -Force

Write-Host "Built $ReleaseExe"
