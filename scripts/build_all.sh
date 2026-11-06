#!/usr/bin/env bash
# Everything from a checked dump in targets/ to a playable build: recompile the game code (generated/), compile it
# and the runtime (build/xc3.exe), build the launcher. "Build XC3.bat" runs it; it also works on its own:
#   scripts/build_all.sh            (XC3_EXE=build/other.exe: link the game under another name, e.g. for tests)
# Needs: MSYS2 UCRT64 at C:\msys64 with the libraries, and .venv with capstone unicorn lz4 ziglang (see README).
set -e
cd "$(dirname "$0")/.."
step() { echo; echo "=== $* ==="; }
[ -x .venv/Scripts/python ] || [ -f .venv/Scripts/python.exe ] || { echo "missing .venv (run \"Build XC3.bat\" or see the README)"; exit 1; }
step "1/5 Checking the game files (targets/)"
export XC3_GAME=${XC3_GAME:-xc3}
echo "game: games/$XC3_GAME"
.venv/Scripts/python -X utf8 tools/extract/check_dump.py targets
step "2/5 Recompiling the game code into C (generated/, ~1 min)"
(cd tools && ../.venv/Scripts/python -X utf8 gen_all.py --out ../generated)
step "3/5 Compiling the game code (build/obj/, several minutes the first time)"
XCDE_SKIP_BOOT_LINK=1 scripts/build_boot.sh
step "4/5 Compiling the runtime and linking ${XC3_EXE:-${XCDE_EXE:-build/xc3.exe}}"
scripts/build_rt_gfx.sh
exe=${XC3_EXE:-${XCDE_EXE:-build/xc3.exe}}
[ -f "$exe" ] || { echo "the link failed (see build/link_gfx.err)"; exit 1; }
launcher=build/xenoblade3_launcher.exe; play="Play XC3.bat"  # [XC3] (tools/launcher/build.sh)
step "5/5 Building the launcher ($launcher)"
tools/launcher/build.sh
echo
echo "Done: $exe and $launcher. Start the game with \"$play\" (the first time: Precompile shaders)."
