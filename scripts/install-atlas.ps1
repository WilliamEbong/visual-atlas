# One-time Visual Atlas setup for Windows: run by double-clicking "Install Visual Atlas.cmd" in the Visual Atlas folder.
# Installs uv (which brings Python), Visual Atlas itself and the starter library, adds Desktop/Start-menu shortcuts,
# then opens Visual Atlas. Safe to run again (for example after downloading a newer version).
# Adapted from Qualia's installer (same owner).

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Step($number, $text) { Write-Host ''; Write-Host "[$number/5] $text" -ForegroundColor Cyan }
function Run($exe) {
    & $exe @args
    if ($LASTEXITCODE -ne 0) { throw "'$exe $args' did not finish successfully (exit code $LASTEXITCODE)." }
}
function Have($name) { [bool](Get-Command $name -ErrorAction SilentlyContinue) }

try {
    Write-Host 'Setting up Visual Atlas. This takes a few minutes the first time; later runs are quicker.'

    Step 1 'Checking uv (the tool that installs Visual Atlas and Python)'
    if (-not (Have 'uv')) {
        Write-Host 'Installing uv from astral.sh...'
        powershell -NoProfile -ExecutionPolicy Bypass -Command 'irm https://astral.sh/uv/install.ps1 | iex'
        $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
        if (-not (Have 'uv')) { throw 'uv could not be installed. Check your internet connection and run Install Visual Atlas again.' }
    }
    Write-Host 'uv is ready.'

    Step 2 'Installing Visual Atlas and Python (only what Visual Atlas needs to run)'
    Run uv sync --locked --no-dev --inexact

    Step 3 'Preparing the Visual Atlas screens'
    if (-not (Test-Path 'web\dist\index.html')) {
        if (-not (Have 'npm')) { throw 'This copy of Visual Atlas has no prebuilt screens. Download the Visual Atlas zip from the GitHub Releases page instead.' }
        Run npm --prefix web ci
        Run npm --prefix web run build
    }
    Write-Host 'Screens are ready.'

    Step 4 'Adding the starter library (licence-checked images with their analyses)'
    try {
        Run .venv\Scripts\atlas.exe starter-import
    } catch {
        Write-Warning "The starter library could not be added ($($_.Exception.Message)). Visual Atlas still works; run Install Visual Atlas again later to add it."
    }

    Step 5 'Creating the Visual Atlas shortcuts'
    $app = Join-Path $root '.venv\Scripts\visual-atlas.exe'
    $shell = New-Object -ComObject WScript.Shell
    foreach ($folder in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {
        $shortcut = $shell.CreateShortcut((Join-Path $folder 'Visual Atlas.lnk'))
        $shortcut.TargetPath = $app
        $shortcut.WorkingDirectory = $root
        $shortcut.IconLocation = (Join-Path $root 'web\public\visual-atlas.ico')
        $shortcut.Description = 'Visual Atlas - find free-to-use images and learn why they work'
        $shortcut.Save()
    }
    Write-Host 'Added Visual Atlas to your Desktop and Start menu.'

    Write-Host ''
    Write-Host 'All done. Visual Atlas is opening now. Next time, double-click the Visual Atlas icon.' -ForegroundColor Green
    Write-Host 'Closing the Visual Atlas window stops it. Your library is stored in the VisualAtlas folder in your user profile.'
    Write-Host 'Optional: to analyse images, sign in once to Codex ("codex login") or Claude Code ("claude"). See Settings > AI setup.'
    Start-Process $app
} catch {
    Write-Host ''
    Write-Host "Setup stopped: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Fix the problem above, then double-click Install Visual Atlas again. Your library was not changed.'
    exit 1
}
