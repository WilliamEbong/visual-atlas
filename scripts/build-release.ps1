# Build the Windows release zip locally (mirrors .github/workflows/release.yml).
# Usage: powershell -ExecutionPolicy Bypass -File scripts\build-release.ps1 [-Version v0.1.0]
param([string]$Version = 'v0.1.0')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
npm --prefix web ci
if ($LASTEXITCODE -ne 0) { throw 'npm ci failed' }
npm --prefix web run build
if ($LASTEXITCODE -ne 0) { throw 'web build failed' }
$name = "VisualAtlas-$Version"
$out = Join-Path $root 'release'
$stage = Join-Path $out $name
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force $out | Out-Null
git archive --format=zip --prefix="$name/" -o "$out\source.zip" HEAD
if ($LASTEXITCODE -ne 0) { throw 'git archive failed' }
Expand-Archive "$out\source.zip" -DestinationPath $out -Force
Remove-Item "$out\source.zip"
Copy-Item -Recurse (Join-Path $root 'web\dist') (Join-Path $stage 'web\dist')
$zip = Join-Path $out "$name.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path $stage -DestinationPath $zip
Write-Host "Built $zip"
