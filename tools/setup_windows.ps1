# One-time setup of a Windows machine for building XC3Recomp (modelled on LASRecomp's tools/setup_windows.ps1).
# Installs MSYS2 (UCRT64: SDL3, FFmpeg, Vulkan loader / headers, shaderc, Vulkan Memory Allocator, Opus) and
# Python 3.12, then creates .venv (the recompiler: capstone, unicorn, lz4; the C compiler: ziglang). Safe to re-run.
# Run by "Build XC3.bat" and by the launcher's "Install & build" tab ("=== k/4" lines: its progress; exit code 0 = done).
# [XC3] MSYS2's own bash runs the build scripts afterwards: Git for Windows is not needed.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
function Step($t) { Write-Host ''; Write-Host "=== $t ===" }
# (Windows PowerShell 5.1 does not stop on a native command's failure: each one is checked)
function Check($what) { if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $what (exit code $LASTEXITCODE)"; exit 1 } }

$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$needWinget = -not (Test-Path C:\msys64\usr\bin\pacman.exe) -or -not (Test-Path $py)
if ($needWinget -and -not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host 'FAILED: winget (App Installer) is missing. Install "App Installer" from the Microsoft Store, then run this again.'
    exit 1
}

Step '1/4 MSYS2'
if (-not (Test-Path C:\msys64\usr\bin\pacman.exe)) {
    Write-Host 'Installing MSYS2 (winget)...'
    winget install --id MSYS2.MSYS2 -e --accept-source-agreements --accept-package-agreements --silent
    if (-not (Test-Path C:\msys64\usr\bin\pacman.exe)) { Write-Host 'FAILED: MSYS2 is not in C:\msys64 after winget'; exit 1 }
} else { Write-Host 'MSYS2: already installed' }
$env:MSYSTEM = 'UCRT64'
$env:CHERE_INVOKING = '1'
$bash = 'C:\msys64\usr\bin\bash.exe'

Step '2/4 Libraries (pacman: SDL3, FFmpeg, Vulkan, shaderc, Opus)'
& $bash -lc 'pacman -Syuu --noconfirm'; Check 'pacman -Syuu'
& $bash -lc 'pacman -Syuu --noconfirm'; Check 'pacman -Syuu (second pass)'  # (after a core update)
$pkgs = 'mingw-w64-ucrt-x86_64-sdl3', 'mingw-w64-ucrt-x86_64-ffmpeg', 'mingw-w64-ucrt-x86_64-vulkan-devel',
        'mingw-w64-ucrt-x86_64-shaderc', 'mingw-w64-ucrt-x86_64-vulkan-memory-allocator', 'mingw-w64-ucrt-x86_64-opus',
        'mingw-w64-ucrt-x86_64-vulkan-validation-layers'
& $bash -lc "pacman -S --needed --noconfirm $($pkgs -join ' ')"; Check 'pacman -S'

# Python for the tools: the python.org build (prebuilt unicorn / capstone wheels; MSYS2's Python can't build them)
Step '3/4 Python 3.12'
if (-not (Test-Path $py)) {
    Write-Host 'Installing Python 3.12 (winget)...'
    winget install --id Python.Python.3.12 -e --scope user --accept-source-agreements --accept-package-agreements --silent
    if (-not (Test-Path $py)) { Write-Host "FAILED: $py is missing after winget"; exit 1 }
} else { Write-Host 'Python 3.12: already installed' }

Step '4/4 Recompiler packages (.venv: capstone, unicorn, lz4, ziglang)'
if (-not (Test-Path "$root\.venv\Scripts\python.exe")) { & $py -m venv "$root\.venv"; Check 'python -m venv' }
& "$root\.venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check lz4 capstone unicorn ziglang; Check 'pip install'

Write-Host ''
Write-Host 'Done. Next: choose your game files and build (the launcher''s "Install & build" tab, or "Build XC3.bat").'
exit 0
