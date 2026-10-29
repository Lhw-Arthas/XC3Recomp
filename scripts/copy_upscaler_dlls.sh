#!/usr/bin/env bash
# [XCDE] Runtime DLLs of the temporal upscalers next to build/xcde.exe (not in git: vendor binaries, ~60 MB):
# AMD FidelityFX SDK 1.1.4 (FSR 3.1, signed prebuilt) and NVIDIA Streamline 2.14.16 (DLSS). Downloaded and
# signature-checked into sdk/ (default); SDK_DIR=<dir> for another location. Get them from AMD / NVIDIA yourself.
# [XC3] AMD FidelityFX SDK 2.x (FSR 3.1 + FSR 4: loader + upscaler DLLs, signed, Kits/FidelityFX/signedbin) from
# FFX2_DIR=<that folder>, default the SDK 2.4.0 unpacked next to this repo; the runtime prefers it over the 1.1.4 DLL.
cd "$(dirname "$0")/.."
S=${SDK_DIR:-sdk}
F=${FFX2_DIR:-../SDK/FidelityFX-SDK-2.4.0/Kits/FidelityFX/signedbin}
for f in "$F/amd_fidelityfx_loader_vk.dll" "$F/amd_fidelityfx_upscaler_vk.dll" \
         "$S/ffx/PrebuiltSignedDLL/amd_fidelityfx_vk.dll" "$S/sl/bin/x64/sl.interposer.dll" "$S/sl/bin/x64/sl.common.dll" \
         "$S/sl/bin/x64/sl.dlss.dll" "$S/sl/bin/x64/nvngx_dlss.dll" "$S/sl/bin/x64/NvLowLatencyVk.dll"; do
  b=build/$(basename "$f")
  [ -f "$b" ] && [ ! "$f" -nt "$b" ] && continue
  cp -f "$f" "$b" 2>/dev/null && echo "copied $(basename "$f")" || echo "missing $f (that upscaler will be unavailable)"
done
