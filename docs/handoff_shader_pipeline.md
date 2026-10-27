# Handoff: shader cache for every PC + the pipeline-link stutters (graphics session -> other session, 2026-10-21 ~22:30)

The user is handing this task to the other Claude session. **For this task you own** runtime/nvn/vulkan/exec.c
(pipeline / prewarm / GPL code only), runtime/nvn/vulkan/precompile.c, runtime/nvn/vulkan/device.c (pipeline cache
save/load only), data/variants_seed.bin, tools/merge_variants.py and the launcher's precompile button.
The graphics session keeps working in temporal.c, dlss.cpp, shaders.c (post shaders), textures.c, and the
DLSS / HUD / post-process parts of exec.c (draw_ velocity table, tmp_* calls, post_process). If you need to touch those
regions, write it in HANDOFF.md "Requests". Same rules as at the top of HANDOFF.md:
- Build with `XCDE_EXE=build/xcde_p*.exe scripts/build_rt_gfx.sh <objects>`.
- Use `git add` on your files only.
- Run at most 3 game runs at once.
- Don't run while the user plays.
- Replace build/xcde.exe only with a verified build, and log it.

## Goal (user's words, translated)
"Eradicate every shader-compilation hitch, even in areas never visited, without having played the whole game to
compile; it must work on any PC (NVIDIA / AMD / Intel, low end: Ryzen 3200G + Vega 8 + 8 GB RAM) and high end."
The spike while a loading screen is up is accepted ("normal"). Stutters while playing are not.

## How it works now (all committed, build/xcde.exe = 9d41615)
Two different things get built:
1. **Shaders** (Maxwell -> GLSL -> SPIR-V, plus the GPL pre-rasterization / fragment-shader libraries).
   `xcde.exe --precompile targets` (precompile.c, T187/T211) scans every SPCH container in the romfs:
   - It does this for all shader programs of the game, every area.
   - It builds the translation variants it can predict:
     - a guess, plus loc1 uint, plus extra versions from input names (n* inputs -> integer);
     - stencil samplers (…Stencil, not ExpStencil) -> tex_uint;
     - plus the 5,007 variants of data/variants_seed.bin, built exactly.
   - Result: SPIR-V in cache/spirv. The pre/fs libraries go **only into the driver's own shader cache** (NVIDIA:
     %LOCALAPPDATA%\NVIDIA\GLCache), because putting them into cache/vk_pipelines.bin made it 698 MB.
   - Measured on the "never visited" setup (<work dir>/coldroot, junctions into the repo; remove those junctions
     with `cmd /c rmdir`, never recursively): [variant-miss] went from 25 to ~3 per new area.
     **Shaders are solved.** The user's last session had 0 [variant-miss].
2. **Pipelines** = shader + that draw's state (vertex format, blend, render targets, depth/stencil, samples). There
   are far more of these than shaders and they can only be made at runtime. Each one is made in one of three ways:
   - **link** (gpl_link: four libraries vi / pre / fs / fo, ~0.3 ms when pre and fs are already in memory; the LTO
     pipeline is swapped in later by gpl_optimize at low priority), or
   - **cached whole** (pipeline_whole with FAIL_ON_PIPELINE_COMPILE_REQUIRED: the driver finds the whole pipeline
     in its cache, 2-17 ms each), or
   - **whole compile** (worst case, tens of ms).
   build_pipeline (exec.c ~2511) uses link only when `libs_ready` (both pre and fs libraries already built and
   in memory). Otherwise it tries cached-whole first.

## The remaining problem (root cause, from the user's build/last_game.log)
[hitch] lines ~32 s after loading, while turning the camera (frames 1908-1919):
```
frame 1908: 175.6 ms | draws waited 157.4 ms (51) | pipelines cached 42 (145.9 ms)
frame 1911: 160.8 ms | cached 116 (108.6 ms)
frame 1914: 226.4 ms | cached 51 (153.3 ms)
frame 1917: 148.3 ms | cached 41 (100.0 ms)
frame 1919: 112.5 ms | cached 35 (88.7 ms)
```
~280 pipelines came "cached whole" (2-3 ms each) in ~10 frames. Draws then waited for them.
Why: prewarm_drain (exec.c ~2757) prebuilds the pre/fs libraries (gpl_prebuild, T211) **only for programs with no
known variant** (`else if (prebuild_libs_on() ...)`). Programs with recorded variants (cache/variants.bin or the
seed) take the `any` branch instead: their pipelines are queued whole (pw_pending -> build_pipeline). Their
libraries were never put in memory, so `libs_ready` is false and every new state combination of those programs goes
the slow cached-whole route.

## Fix 1 (was next on my list): always link first on GPL GPUs
- In prewarm_drain, when prebuild_libs_on(), queue gpl_prebuild for **every** Prog the registration creates. That
  includes the variant branch: prebuild for each distinct (prog, poly_fill, samples, a2c) of its variants, not only
  the 1/1/0 guess.
- Optional: in build_pipeline, if the libraries are being built (state 0), wait on / link them instead of falling back
  to cached-whole.
- Check that gpl_prebuild's guess key (poly_fill 1, samples 1, a2c 0) matches what most draws use. If not, prebuild
  the combinations the variants record.
- Measure with the [hitch] log plus vk_hitch_counters (link n/ns vs cached n/ns), on the user's area. Saves:
  <work dir>/saves/user_20261021_1520 and faces_1515, with tests/routes/load_a.txt plus a camera turn. Also measure
  on coldroot. Done means: no frame with "cached" > a few after the loading screen.
- RAM: libraries stay in memory (GPL_TAB). Count their memory on a long run. prebuild_libs_on() is already off on
  integrated GPUs (8 GB shared RAM).

## Fix 2 (proposed to the user, OK not given yet): our own per-zone pipeline-library cache, any PC
The driver shader cache is not something we control:
- NVIDIA's had hit its 1 GB default limit (the user set it to "Unlimited" in the NVIDIA control panel and should run
  "Precompilar shaders" again).
- AMD / Intel caches have their own limits and behaviour.
- iGPUs (3200G) may not have GPL at all (check g_vk.gpl on Vega / RADV vs the AMD Windows driver).

Idea:
- Store the built pre/fs libraries per zone (per set of programs a loading screen registers, e.g. keyed by the
  registration batch) in our own files on disk.
- Load only the current zone's file into memory on the loading screen, which keeps RAM bounded for 8 GB machines.
- Fall back to the current path when the GPU has no GPL.
- For non-GPL GPUs (where the only path is whole pipelines), the same per-zone idea applies to whole pipelines: on
  the loading screen, build the zone's recorded variants (variants.bin / seed) before the game starts drawing.
  Bound it by time and RAM.

## Known facts / traps
- cache/vk_pipelines.bin is one file per checkout. Test runs (LARECOMP_HIDDEN) no longer save it (2c4cb62), so a
  test build's cache can't spoil the player's.
- precompile_done.txt holds "exe <size> <mtime>". The launcher precompiles again when build/xcde.exe changes.
- Diagnostics:
  - [hitch]: frames > 25 ms and > 2x the average, with the build counters.
  - [build-wait]: a draw waited > 8 ms.
  - [variant-miss]: a SPIR-V compile at draw time.
  - XCDE_PREBUILD_LIBS=0/1.
  - XCDE_DUP_CHECK.
- Python heredocs turn `\n` inside C strings into real newlines. Use script files, or chr(92).

## Other open graphics bugs (staying with the graphics session, listed so you don't chase them)
- The area-name banner ("Schwebendes Riff 4") bleeds faintly into the party menu. Likely the HUD composite
  (tmp_hud.frag adds final - pre-HUD snapshot) when the menu background is a captured scene image.
- Save-slot thumbnails are blank in the load menu.
- DLSS sharpness: confirmed fixed by the user (no longer blurry).

## Status (party mod session, 2026-10-21 ~23:40)
- Fix 1 done (T212, exec.c): libraries prebuilt for programs with recorded variants too (gpl_prebuild_variant, once
  per program / fill mode / samples / a2c), the recorded variants' pipelines no longer built whole ahead, and
  build_pipeline always links on GPL GPUs (link_first; XCDE_PREWARM_WHOLE=1: the old way). "cached" pipelines after
  loading: 0. Tried and dropped: linking only when the libraries are known-being-built (no gain).
- Test bench (reusable): <work dir>/coldroot/build/ab.sh <exe> <tag> (fresh precompile + run) and ab2.sh (a second
  run on a warm driver cache); route build/turnrun60.txt (fallen_arm load, camera turn, run; 60 fps, the user's ini).
  Each exe needs its own name / path: the NVIDIA driver cache is per exe path. Runs vary +-30 %: compare 3 warm runs.
  Warm averages: before T212 2.16 s of stalls after loading (worst frame 1.35 s); now ~1.4-1.5 s (worst ~0.8 s).
- What is left is the area's first frame (0.5-0.8 s, in the black transition): files read at ~frame 3712, ~1,000
  programs registered at ~3745, first frame at ~3780 (LARECOMP_LOG_FILES=1). Ideas: a per-zone head start from the
  files read (zone -> programs recorded on the first visit, or from precompile's containers): ~0.5 s at most on a fast
  load; libraries kept across areas already (never freed - memory not measured on a long run yet).
- Fix 2 (own per-zone cache, non-GPL GPUs) not started.
- T214 (~00:10): libraries without RETAIN_LINK_TIME_OPTIMIZATION_INFO (unused: ~630 -> ~320 MB per area) and a
  prebuild budget by RAM (XCDE_LIB_BUDGET). Libraries are still never freed (a draw's own are built past the budget).
- Not reproduced / not fixed here: the area banner bleeding into the party menu (Fallen Arm banner + menu, DLSS and
  bilinear: no ghost - needs the user's case, "Schwebendes Riff 4"); save-list thumbnails (T181: filling both slot
  buffers and writing the slot target back changed nothing - the list displays another texture).
