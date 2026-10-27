# What keeps XCDE from using the whole PC (measured 2026-10-20, RTX GPU + an 8-core desktop CPU, 4K, fps unlocked)

Scene: the user's meadow save, camera spinning (tests/routes/load_spin.txt), build 7ce4c3c (async worker + VRAM grass
mirrors). Result: 96-162 fps, ~134 average. Real per-thread CPU (Windows thread times over 50 s):
worker (our Vulkan translation) 0.57 cores, game render thread t83 0.29, game job threads t118 / t119 0.26 each, game
main thread t80 0.25; everything else < 0.02. About 1.7 cores busy of 16: **no thread is saturated** - the time goes to
the threads waiting for each other.

## Bottlenecks, largest first
1. **The game waits for the GPU at the end of every frame** (its frame limiter f_70005bcfe0 -> f_7000603900 ->
   nvnSyncWait on the fence it placed right before, sync 72675154c8; XCDE_LOG_SYNCWAIT: always 1 submission behind the
   newest, ~2.5-2.8 ms a wait). CPU and GPU take turns as on the Switch: the GPU idles while the game builds the next
   frame, the game idles while the GPU finishes. Tried "wait for the previous frame instead" (XCDE_FRAME_LAG): slower
   (84 fps avg, other waits appeared, the 30 fps fallback triggered) - the game synchronises elsewhere too; needs a
   study of what it reads back after that wait before trying again.
2. **One thread translates everything to Vulkan** (the worker): ~7.5 ms a frame in the heaviest view = the limit there
   (GPU ~6 ms). Inside: NVIDIA driver ~35 % of its busy time, per-draw preparation 1.8 ms, pipeline keys 1.2 ms,
   descriptor sets 1.5 ms, textures 0.7, vertex streams 0.5 (~3,900 draws, ~350 passes a frame). Two small fixes
   measured without gain (set reuse, key memo). Real fixes: split it into two threads (prepare / record), or bindless
   descriptors + dynamic uniform buffers (far fewer driver calls per draw).
3. **GPU time that is ours, not the game's**: after the grass mirrors 5.7 ms average / 8.5 worst at 4K. Left:
   ~350 render passes a frame (the game's own plus our breaks for barriers, writers and the 400-draw submission splits:
   each break stores / loads every attachment); skinning palettes and other GPU-written ranges still read from host
   memory over PCIe (XCDE_TRACE_DIRECT lists them); the 3x-scaled 640x360 probe / lighting buffers.
4. **The game's own CPU threads** (main t80, render t83, jobs t118 / t119): ~0.25-0.3 cores each, mostly game code;
   the main thread spends ~30 % in the game's mutex lock / unlock and ~20 % sleeping in its wait loop. Generated-code
   speed was already worked on (restrict, T165); the rest is the game's design (it doesn't spread more).
5. **External caps** on this PC (not XCDE): RivaTuner's global frame limit (was 60), NVIDIA control panel forced
   V-Sync (was on), a 60 Hz monitor mode. Any of them caps everything at 60.
6. **First-visit stutter**: shader compiles in new areas (precompilation T187 exists; its effect not re-measured).

## Other open items (not performance)
- T181: save/load menu shows the placeholder (the saved .tmb is right now).
- T177 / T179: Colony 9 town edges / splotches - probably fixed by T176, not seen in a test route.
- DLSS / FSR 3: the game has no motion vectors; SDK downloads need the user's OK.
- Battle party-member switching mod: not started.
- Long-play check of the 69-minute freeze fix (T185): the 100-minute soak did not finish.
- Min-spec items: integrated-GPU path (T193), AMD checklist (T196), laptop GPU selection (T194), Intel hybrid
  P-cores, GPU hang guard (T189). LINE_WIDTH command unimplemented (no visible effect).

## Status after the fixes (2026-10-20, evening; same scene, 4K uncapped)
133 -> **166 fps average, worst 96 -> 129**: one frame in flight (bottleneck 1), splits at pass boundaries, VRAM
mirrors of the transform-feedback and store-written vertex ranges (no vertex data read over PCIe in the meadow).
Now: GPU ~5.8 ms a frame (LARECOMP_GPUPROF_AT, 27 frames over the spin), worker ~4.4 ms; the average frame is
GPU-bound. The GPU time is the game's own passes at 3x internal resolution (largest: a 5-draw two-target lighting
pass, ~0.64 ms); pass breaks cost little on an immediate-mode GPU. Record-only second thread: measured with rdtsc
around every call - vkCmd* ~1.0 ms, descriptor sets ~0.2 ms a frame: it could only help the heaviest views (worker
~7.5 vs GPU ~6.8 ms there, ~10 %), not built. More fps from here = less GPU work per frame: a lower internal
resolution with an upscaler (FSR / DLSS, the game has no motion vectors) or resolution "dynamic".
