@echo off
rem Stutter diagnostics: on every slow frame the game writes to build\last_game.log what the CPU was doing
rem ([hitch-cpu] lines). A bit heavier than normal play; only for measuring stutter in battle.
cd /d "%~dp0"
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
set XCDE_HITCH_SAMPLE=1
set XCDE_SAMPLE_HZ=500
set XCDE_SAMPLE_CALLERS=1
start "" "build\xcde_launcher.exe"
