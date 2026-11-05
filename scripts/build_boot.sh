#!/usr/bin/env bash
# Build the recompiled game code objects (build/obj/) with the project venv's zig cc.
#   1. python tools/gen_all.py            -> generated/{main,sdk}
#   2. this script                        -> build/obj/*.o
set -e
cd "$(dirname "$0")/.."
Z=".venv/Scripts/python -m ziglang cc"; export Z
CF="-O1 -march=x86_64_v2 -ffp-contract=off -fno-strict-aliasing -fvisibility=hidden -Iruntime -w"; export CF
# [XC3] runtime code tied to XCDE addresses / romfs content is built only for that game (tools/game.py)
if [ "${XCDE_GAME:-xc3}" = xcde ]; then CF="$CF -DGAME_XCDE"; fi
# [XC3] 64-bit off_t / stat for the runtime objects too (build_rt_gfx.sh)
if [ "${XCDE_GAME:-xc3}" != xcde ]; then CF="$CF -D_FILE_OFFSET_BITS=64"; fi
mkdir -p build/obj/main build/obj/sdk build/rt
# drop objects whose chunk no longer exists (the chunk layout shifts when the generator output changes)
for o in build/obj/*/*.o; do m=$(basename "$(dirname "$o")"); b=$(basename "$o" .o); [ -f "generated/$m/$b.c" ] || rm -f "$o"; done
cc1() { f=$1; m=$(basename "$(dirname "$f")"); b=$(basename "$f" .c); o="build/obj/$m/$b.o"; [ "$o" -nt "$f" ] || $Z -c "$f" -o "$o" $CF || echo "FAIL $f"; }
export -f cc1
ls generated/main/*.c generated/sdk/*.c | xargs -P "${JOBS:-16}" -I{} bash -c 'cc1 {}'

