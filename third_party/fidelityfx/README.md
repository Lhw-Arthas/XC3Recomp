# AMD FidelityFX SDK 2.4.0 - signed Vulkan DLLs

`amd_fidelityfx_loader_vk.dll` and `amd_fidelityfx_upscaler_vk.dll`, unchanged from the SDK's
`Kits/FidelityFX/signedbin/` (FSR 3.1 and FSR 4 through the FidelityFX API). `scripts/copy_upscaler_dlls.sh`
(run by `scripts/build_all.sh`) copies them next to `build/xc3.exe`, where `runtime/nvn/vulkan/temporal.c` loads them.

License: `license.md` (the SDK's `Kits/FidelityFX/docs/license.md`, unchanged). It lists both DLLs among the files
under its MIT license; the SDK's default license also permits redistribution in binary form with its notices.
Copyright (C) Advanced Micro Devices, Inc.
