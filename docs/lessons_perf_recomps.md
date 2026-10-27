# How the other Switch recomps get performance, compared with XCDE (2026-10-20)

User question: are we doing something wrong; how do the other recomps make the game run well and use the PC?
Sources: the notes already in docs/ (lessons_astral_ssbu.md, lessons_other_recomps.md, lessons_windowsmash.md) and the
copies in <work dir>\otherrecomps (OpenSmash-Ultimate nvn_vk_m4.c / hitch.c / prewarm.h, Mario Wonder and WindowSmash
commit logs, Astral Chain docs, LASRecomp diffs). Ideas only, no code copied.

## What they all do, and where XCDE stands
| Technique | Who | XCDE |
|---|---|---|
| Static recompilation of the game code (no interpreter / JIT) | all | yes |
| Renderer on its own thread ("replay thread", "render thread with fence tickets") so the game builds the next frame while the previous one is translated | Mario Wonder (pipelined submits, default on iGPUs), Let's Go #59 | **built 2026-10-20 (exec.c async render worker), +20-25 % uncapped at 4K; not committed until the battle / cutscene / save checks pass** |
| Submit GPU work as it is recorded, not once per frame | OpenSmash, Wonder | yes (split every 400 draws, 2026-10-20: 49 -> 60 fps in the heavy view) |
| Pipelines made ahead on worker threads, pipeline libraries + fast link, shader containers scanned and prepared | OpenSmash, TotK, Wonder | yes (T163, T187, T188) |
| Preparation paused / capped while the game is busy (4 low-priority workers cost OpenSmash 35 fps in fights) | OpenSmash | partly (workers below normal priority, T160); no pause in battle yet |
| Extended dynamic state 3: blend enable / equation / write mask / polygon mode / alpha to coverage as dynamic state -> few pipeline keys | OpenSmash | **no** (they are in our pipeline key) |
| Push descriptors for sets of <= 32 bindings | OpenSmash | **no** (every draw allocates + writes 2-3 sets: ~40 % of our render thread is the driver) |
| Upload checks once per submission, reuse unchanged uploads | WindowSmash | yes (texture checks memoised per frame, copy dedupe per submission) |
| Canonical pipeline keys (state Vulkan ignores normalised away: 18 % fewer pipelines) | Wonder | no (T195) |
| Timer: invariant TSC when QPC is slow (HPET PCs) | WindowSmash | yes (T190) |
| 1 ms timer resolution, no EcoQoS throttling | most | yes (platform/windows.c) |
| Game / render / vsync threads on performance cores (Intel hybrid CPUs) | LASRecomp f7731d3 | **no** (matters on Intel 12th gen+, not on the user's Ryzen) |
| High-performance GPU on laptops (NvOptimusEnablement / AmdPowerXpress) | WindowSmash | no (T194) |
| Frame rate above the game's own: patch the game's limiter, speed from measured time | Astral Chain (60), Wonder (study), EoW | yes (FPS 30..165 / unlimited, checked at 120) |
| iGPU defaults: skip per-frame clears of scene targets, lean image usage | LASRecomp 8a66a61 / 03ee802 | no (T193, needs an iGPU) |
| Vertex data for GPU-written buffers kept in VRAM | - | no: grass instance data read over PCIe (~2 ms a frame at 4K on the RTX GPU, T175 to redo) |

## What this means for the user's question
Nothing XCDE does is "wrong" in the sense of a design the others avoid; the remaining gap to 120 fps at 4K is:
1. **CPU, render path**: commit the async worker; then push descriptors + extended dynamic state 3 to cut the driver
   share of the render thread (the biggest single cost there).
2. **GPU**: per-pass GPU profile of the heavy 4K view (12.8 ms a frame): our overheads in it (grass over PCIe, pass
   breaks, 3x-scaled half-resolution buffers, full-screen copies) - fix the largest.
3. **Game main thread**: ~0.9 cores when uncapped, ~60 % of it spent in the game's own wait loop (lock + sleep polling
   for the render thread) - it shrinks by itself as 1 and 2 make the render side faster.
4. Pause background shader preparation during battles (OpenSmash's lesson), P-core placement for Intel hybrid CPUs.
