#!/usr/bin/env bash
# Build the launcher: build/xenoblade3_launcher.exe (SDL3 + Dear ImGui, SDL renderer). Run it with "Play XC3.bat"
cd "$(dirname "$0")/../.."
Z=".venv/Scripts/python -m ziglang c++"
I=third_party/imgui
M=${XC3_UCRT64:-/c/msys64/ucrt64}  # [XC3] MSYS2's UCRT64 prefix (CI: .github/workflows/release.yml sets /ucrt64)
OUT=build/xenoblade3_launcher.exe
mkdir -p build/launcher
for f in $I/imgui.cpp $I/imgui_draw.cpp $I/imgui_tables.cpp $I/imgui_widgets.cpp $I/backends/imgui_impl_sdl3.cpp \
         $I/backends/imgui_impl_sdlrenderer3.cpp tools/launcher/launcher.cpp; do
  o=build/launcher/$(basename ${f%.cpp}).o
  [ "$f" -nt "$o" ] || [ ! -f "$o" ] || continue
  $Z -c $f -o $o -O2 -march=x86_64_v2 -std=c++17 -I$I -I$I/backends -idirafter $M/include -w || exit 1
done
RES=build/launcher/launcher.res  # [XC3] the icon (tools/launcher/make_icon.py -> icon.ico, launcher.rc)
.venv/Scripts/python -m ziglang rc -- tools/launcher/launcher.rc $RES || exit 1
# [XC3] linked under a new name, then swapped in: Windows refuses to overwrite a running exe (the launcher rebuilding
# itself from its "Install & build" tab, or Build XC3.bat with the launcher open) but lets it be renamed
NEW=${OUT%.exe}.new.exe OLD=${OUT%.exe}.old.exe
# [XC3] SDL3 linked statically (libSDL3.a + its libiconv, the system libraries from sdl3.pc's Libs.private): the exe
# needs no SDL3.dll / libiconv-2.dll from MSYS2, so it starts on a PC that has none of the build tools yet (the
# "Install & build" tab installs them)
SDL="$M/lib/libSDL3.a $M/lib/libiconv.a -lkernel32 -luser32 -lgdi32 -lwinmm -limm32 -lole32 -loleaut32 -lversion -luuid -ladvapi32 -lsetupapi -lshell32 -ldinput8"
$Z -o $NEW build/launcher/*.o $RES $SDL -march=x86_64_v2 -Wl,--subsystem,windows -static-libstdc++ 2> build/launcher/link.err
rc=$?; [ $rc = 0 ] || { cat build/launcher/link.err | head -20; exit $rc; }
rm -f $OLD ${OLD%.exe}.pdb 2>/dev/null
[ -f $OUT ] && { mv -f $OUT $OLD 2>/dev/null; [ -f ${OUT%.exe}.pdb ] && mv -f ${OUT%.exe}.pdb ${OLD%.exe}.pdb 2>/dev/null; }
mv -f $NEW $OUT || exit 1
[ -f ${NEW%.exe}.pdb ] && mv -f ${NEW%.exe}.pdb ${OUT%.exe}.pdb
exit 0
