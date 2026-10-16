# Build the Windows release zip locally (mirrors .github/workflows/release.yml).
# Usage: powershell -ExecutionPolicy Bypass -File scripts\build-release.ps1 [-Version v0.4.0] [-WorkingTree]
param([ValidatePattern('^v[0-9]+\.[0-9]+\.[0-9]+$')][string]$Version = 'v0.4.0', [switch]$WorkingTree)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
npm --prefix web ci
if ($LASTEXITCODE -ne 0) { throw 'npm ci failed' }
npm --prefix web run build
if ($LASTEXITCODE -ne 0) { throw 'web build failed' }
$name = "VisualAtlas-$Version"
$out = Join-Path $root 'release'
$stage = [IO.Path]::GetFullPath((Join-Path $out $name))
if ((Split-Path -Parent $stage) -ne [IO.Path]::GetFullPath($out)) { throw 'Stage must stay in release.' }
if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Force $out | Out-Null
if ($WorkingTree) {
    # Local builds include reviewed uncommitted source, while respecting archive exclusions.
    $files = @(git -c core.quotePath=false ls-files --cached --others --exclude-standard | Sort-Object -Unique)
    if ($LASTEXITCODE -ne 0) { throw 'Could not list source files' }
    $excluded = @{}
    # Windows PowerShell adds CR to stdin paths; argument batches preserve exact names.
    for ($offset = 0; $offset -lt $files.Count; $offset += 50) {
        $batch = @($files | Select-Object -Skip $offset -First 50)
        $attributes = @(git -c core.quotePath=false check-attr export-ignore -- $batch)
        if ($LASTEXITCODE -ne 0) { throw 'Could not check distribution exclusions' }
        foreach ($attribute in $attributes) {
            if ($attribute -match '^(.*): export-ignore: set$') { $excluded[$Matches[1]] = $true }
        }
    }
    foreach ($file in $files) {
        if ($excluded.ContainsKey($file)) { continue }
        $source = [IO.Path]::GetFullPath((Join-Path $root $file))
        if (-not $source.StartsWith($root + [IO.Path]::DirectorySeparatorChar)) { throw 'Source outside workspace' }
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { continue } # tracked deletion
        $target = Join-Path $stage $file
        New-Item -ItemType Directory -Force (Split-Path -Parent $target) | Out-Null
        Copy-Item -LiteralPath $source -Destination $target
        if ((Get-FileHash -LiteralPath $source).Hash -ne (Get-FileHash -LiteralPath $target).Hash) { throw "Copy mismatch: $file" }
    }
} else {
git archive --format=zip --prefix="$name/" -o "$out\source.zip" HEAD
if ($LASTEXITCODE -ne 0) { throw 'git archive failed' }
Expand-Archive "$out\source.zip" -DestinationPath $out -Force
Remove-Item "$out\source.zip"
}
Copy-Item -Recurse (Join-Path $root 'web\dist') (Join-Path $stage 'web\dist')
$zip = Join-Path $out "$name.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path $stage -DestinationPath $zip
Write-Host "Built $zip"
