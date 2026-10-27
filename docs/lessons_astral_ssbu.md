# Lessons from AstralChain-PC and OpenSmash-Ultimate (ssbu-recomp), reviewed 2026-10-19

User asked to look at two new Switch static recompilations for ideas on graphics bugs and performance. Read: their
READMEs, AstralChain-PC `docs/` (development, how-it-works), ssbu-recomp `runtime/nvn_vk_m4.c` comments,
`runtime/nvn_vk_prewarm.h`, `runtime/hitch.c`. Ideas only - no code copied (ssbu-recomp is GPL-3.0; AstralChain-PC MIT,
built on the same LASRecomp base as this project).

## AstralChain-PC (Puddz)
- Built at `-O2` for **x86-64-v3** (AVX2 / FMA) - the same choice tested here for T165 (generated code on v3).
- **GPU hang stop**: the renderer ends the game when one submission runs over 1.2 s (`AC_GPU_HANG_MS`), before the
  Windows TDR resets the driver; the launcher script also kills the game on the first `nvlddmkm` / `amdkmdag` / TDR event
  in the System log. Worth having for players on weak GPUs (a hang otherwise resets the desktop).
- **Save-slot thumbnails missing** for them too: `nvnTextureReadTexels` not implemented. Same symptom as our T181
  (Colony 9 save slots blank): check whether XCDE builds its slot image with ReadTexels / a CPU copy of a render target.
- Cutscene catch-up patch: cutscenes take larger steps after a stall so the picture stays in sync with the voices
  (relevant for us after first-time compiles: T160 / T163).
- Same LASRecomp NVN layer: `LARECOMP_SKIP_UNBUILT`, `LARECOMP_TEX_FULLHASH`, GPU profile of slow frames automatically
  (we only profile on request: `LARECOMP_GPUPROF_AT`).

## OpenSmash-Ultimate (Denkishi/ssbu-recomp)
Reports 59-60 fps for whole matches on an **Intel Raptor Lake iGPU**, and 0 pipeline holds in fight frames on a first run.
- **Shader container scan**: the game's shader containers are found in memory (searching below each program's control
  section for its container header) and *every variation of every container* is prepared on a background queue, the
  containers of the coming fight first (at its loading screen); a loading barrier waits only for those. Our T163 records
  only variants already seen (`cache/variants.bin`): this is the way to cover areas the player hasn't visited.
- **Graphics pipeline library** (VK_EXT_graphics_pipeline_library): vertex-input, pre-rasterization, fragment and
  fragment-output libraries built ahead; a new state combination is a fast link (milliseconds) instead of a full
  pipeline compile, and a link-time-optimized pipeline is compiled on the background queue and swapped in later.
  That removes the "draw waits for its pipeline" class (our T174 waits) without precompiling every render state.
- **Lesson on preparation priority**: 4 workers at the lowest priority compiling during a fight cost them 35 fps (the
  driver contends with the render thread), so the preparation pauses near fights and its workers are capped
  (8 normally, 0 in a fight) - the rest stay free for what the game hands over. For us (T160 worker priority, 4-thread
  min spec): lower priority alone is not enough; cap or pause background preparation while the field is busy.
- History of pipelines (`pipes.bin`) prewarmed at start by several workers with no shared lock on the hot path (their
  PR #33: per-worker counters, stage loads deduplicated) - compare with our `prewarm_drain`.
- `hitch.c`: a hitch report per slow frame (what the frame did), plus a freeze watchdog with every thread's stack.
- Deterministic mode with a per-frame state hash log (we have XCDE_FRAME_HASH).

## Follow-ups (tasks.md)
- T187: container scan + prepare all variants (T163 part 2), with a cap / pause while in the field or in battle.
- T188: graphics pipeline libraries + fast link, LTO pipeline swapped in later.
- T189: GPU hang stop before TDR.
- T181 note: thumbnails likely need `nvnTextureReadTexels` (or the capture path the game uses).

## AC-Recomp (swaymun, Astral Chain on macOS / MoltenVK, built on SuperMarioWonderRecomp)
- **All shaders translated offline** at build time with a pinned translator (no translation while playing; the build
  checks the translated shaders are byte-identical to the developer's). For us: T187 could translate every shader
  found in the RomFS / containers at install time, leaving only pipeline creation for run time.
- **Internal resolution is in the game's code, not the runtime's**: Astral Chain renders docked at a fixed 1600x900 with
  its own dynamic resolution between 1440x810 and 1600x900; the sizes are `mov` / `cmp` immediates, and the system's
  display-resolution answer is never read. Their fix patches those immediates before lifting (render targets, crop,
  DRS slots, display-size getter, graphics memory budget). **For XCDE (T182 / T183):** check whether the game's own
  dynamic resolution lowers the 3D target (it reads the GPU timing counters we report) - that would explain soft
  characters - and whether our output scale really reaches every scene target at 4K.
- **60 fps as a second lifted binary**: five instructions patched in a private copy of main (after build id and word
  checks), main lifted twice; the launcher starts the 30 or the 60 fps exe (only the generated files that differ
  recompile: 2 of 207). Game speed handled by the game's own speed controller; cutscenes fixed-step. A model for our
  "60 fps patch" step (the limiter is f_70005bcfe0, T157).
- Metal performance HUD toggle in the launcher (ours: F-key overlay idea in the feature list).

## Updates of the earlier repos (checked 2026-10-19, commits since 2026-10-15)
- **LASRecomp (our base, MIT) work branches** (`test-perf-6`, `beta_5`, `dynres-steady`, `frame-interp-rt`; main only gets
  README credits):
  - 2332e74 *Fix LDC.64 address/destination overlap and the Windows lazy-commit race* (both from letsgo-recomp). LDC.64:
    we already had it (T127). **Lazy commit race: ported** (two threads faulting on the same uncommitted 64 KB chunk -
    the second found it committed and crashed; execute faults are no longer retried).
  - 8a66a61 / 03ee802 *integrated GPUs*: skip the per-frame clears of scene targets (3.7 ms a frame on an Intel UHD 770
    at 2x, identical images), images listing their view formats instead of MUTABLE_FORMAT ("lean usage"), SMAA weights
    pass only where edges were found (stencil) - all on by default on iGPUs only. -> T193.
  - f7731d3 game, render and vsync threads kept on performance cores (hybrid Intel CPUs); 6dc7f92 dynamic resolution
    holds a steady size (floor 540 lines); 1783437 `LARECOMP_LOG_HITCH_MS`; cc1ada3 Intel placeholder attachment /
    depth-copy scratch; frame interpolation branch (render-thread interpolation between game frames: a 60 fps look
    for 30 fps games - see the branch if we want that instead of a game-logic 60 fps patch).
- **WindowSmash (SNO2207)**:
  - 5004359 **slow system timer**: on PCs where Windows times with the HPET (a common "tweak") a
    QueryPerformanceCounter read costs ~1 us instead of 10-20 ns; 40 % of their main thread went there. They switch to
    the invariant TSC (RDTSCP, rescaled at 20 ms / 2 s / 30 s / 10 min) when a read is over 250 ns. Our rt_ticks /
    plat_now_ns / SDL_GetTicksNS go through QPC: -> T190.
  - 4d6ee5c one shared write-watch record (each user keeps its own clock; a reset by one check lost other users' news;
    separate query + reset lost writes in between). Ours (exec.c vk_pages_changed / vc_flush) already stamps
    generations in one table - check that query and reset are one call (GetWriteWatch WRITE_WATCH_FLAG_RESET).
  - 5cf1752 **NVIDIA driver threads with 64 KB stacks** overflow in nvgpucomp64.dll on deep shaders: silent crashes. They
    hook CreateThread of DriverStore DLLs to give those threads 16 MB; the crash report runs on its own thread. -> T191.
  - c370274 Intel iGPU: alpha-test variant with a switch on a constant failed on Intel (menus black): use comparisons
    and selects, no switch. Also pick the high-performance GPU on laptops (NvOptimusEnablement /
    AmdPowerXpressRequestHighPerformance exports). -> T194 (cheap, matters for laptops of min-spec players).
  - 2eb1e5e uploads compared once per submission (88 MB of memcmp a frame on a results screen before).
- **SuperMarioWonderRecomp**: a0c214f **canonical pipeline keys** (18 % of new pipelines differed only in state Vulkan
  ignores; NX_PIPE_VERIFY checks merged keys) -> T195; f116b69 heavy texture uploads through staging, not the ring.
- **letsgo-recomp**: FSR 3.1 upscaler (F12 menu) - temporal upscaling would suit a weak iGPU at 720p (needs depth and
  motion vectors: does XCDE render a velocity buffer for its TAA?) -> idea T192; SSAO/GI fixes are game specific.
- **MacNativeGames**: a shared shader-variant list in the repo, grown from players' contributions (8,097 variants from
  one player) - the community route to T187; long-play crash from a stale optional reference (#57).
- **B2recomp (K0NL, Bayonetta 2, Windows)** - several **AMD** fixes, relevant for the min-spec Vega 8:
  60f5552 a new texture's clear ordered before its upload (AMD showed textures blank); a5d0b45 shaders must not read a
  constant buffer the pipeline layout lacks (AMD refuses the pipeline); 1642dd6 runs without
  VK_EXT_vertex_input_dynamic_state (RX 400/500); 781e756 FIFO when there is no mailbox present mode; a5577d7 a pipeline
  or library the driver refuses no longer stops the game; 66ea6c0 DPI aware (scaled screens get real pixels); 68c2d08
  cinematics in sync above 60 fps. -> T196 (AMD checklist).
- **SkyRecomp (Apolinario-coder, Skyward Sword, LAS base)**: NVIDIA Image Scaling (NIS) upscaler option, mod manager
  (LayeredFS), Linux/macOS CI - nothing new for graphics bugs or speed.
- **EoWRecomp (Nycolazs, Echoes of Wisdom, LAS base, early: Linux + Vulkan on an Iris Xe at 9-12 fps)**: Maxwell
  translator fixes we share the code of - FLO.SH / .INV (a wrong FLO ran its light loop too long), BFE.BREV,
  HSETP2/HSET2 immediates, VOTE, RED, LEA.HI, structured loops. **Ported here: FLO .SH/.INV and BFE.BREV**
  (translate.c; not used by XCDE in the title / load / field runs so far - a log line says when they appear).
  Also a "dark vertical band from the top of the screen down to Link" artefact - compare with our T178 vertical lines.
