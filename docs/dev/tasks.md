# Tasks: Monado

**Inputs:** the original spec, plan and research documents (Spanish, not included in the public copy; their key facts
are in the README) and `CONTRIBUTING.md` (the project rules, "constitution").

**Format:** `- [ ] Txxx [P] [Milestone] Description → files · Req: … · Done when: …`
- `[P]`: can run in parallel with other `[P]` tasks of the same milestone (different files, no dependency).
- Every task cites its requirements (Art. IV). Tests come **before** the implementation they validate (Art. V).
- A closed task is marked `[x]` and links its evidence when the milestone asks for it.
- Statuses below M5 are historical: much of what is open here was done later under the session tasks further down.

---

## M0 — Foundations

- [x] T001 [M0] Initialise git; pin `upstream/lasrecomp` (`136f679`) and `upstream/ssbu-recomp` (`938e66b`) as
  submodules → `.gitmodules` · Req: Art. X · Done when: `git submodule status` shows both commits.
- [x] T002 [P] [M0] MIT `LICENSE` with Peiikai's notice + our own; `NOTICE.md` with every dependency and licence →
  `LICENSE`, `NOTICE.md` · Req: Art. III, NFR-001.
- [x] T003 [P] [M0] Write ADRs 0001–0010 → `docs/adr/` · Req: Art. IV.
- [x] T004 [P] [M0] Design contracts → `docs/contracts/*.md` · Req: Art. IV.
- [x] T005 [M0] **Test first:** `tests/unit/test_check_dump.py` with synthetic folders (correct, encrypted container,
  wrong version, incomplete romfs, non-ASCII path) · Req: FR-001–004, FR-006.
- [x] T006 [M0] **Test first:** `tests/unit/test_package_guard.py`: the packager fails on generated `.c`, NSO, romfs
  files or keys · Req: Art. I, SC-012.
- [x] T007 [M0] `tools/extract/check_dump.py`: validation by build-id and the expected list of paths / sizes (no content
  hashes) → makes T005 pass · Req: FR-001–004, FR-006.
- [x] T008 [M0] CI (GitHub Actions or local): lint + Python / C unit tests, no game data → `.github/workflows/`
  · Req: SC-012 · Done when: CI green and T006 green.

**M0 gate:** T001–T008 done; constitution check reviewed.

## M1 — Game profile and generator

- [x] T010 [M1] `games/xcde/profile.json` (bases `main` 0x7000000000, `sdk` 0x7004000000), build-ids, modules to
  lift, heap · Req: Art. IX, FR-003.
- [x] T011 [M1] Adapt `tools/lifter/gen.py`: LAS patches and randomizer loaded per profile (empty for XCDE), `[XCDE]`
  marks, `docs/UPSTREAM.md` · Req: FR-013, Art. X.
- [x] T012 [P] [M1] `games/xcde/patches.py` + a format with expected bytes; a test that a patch with a different byte
  aborts → `tests/unit/test_patches.py` · Req: FR-013.
- [x] T013 [M1] Reproducible generation: two runs → the same hash of `generated/` · Req: NFR-006.
- [x] T014 [P] [M1] Generator coverage report (functions, tables, `Unsupported`, padding vs real `udf`) →
  `tools/lifter/report.py` · Req: FR-010.
- [x] T015 [P] [M1] Guest function map (address, size, name when known) to debug `main` without symbols →
  `build/maps/` · Req: FR-064.

**M1 gate:** reproducible main+sdk generation, 0 `Unsupported`, report in `docs/evidence/M1/`.

## M2 — A correct, compact lifter

- [x] T020 [M2] **Research Q1:** classify main's 1,083 unresolved `br` by pattern (R4).
- [x] T021 [M2] **Test first:** synthetic corpus of jump-table patterns (`ldrb/ldrh/ldrsw` + `add lsl`, with and
  without an immediate `cmp`, copied indices) → `tools/tests/test_jumptables.py` · Req: FR-011.
- [~] T022 [M2] Extend the table resolver to ≥ 95 % resolved in main and sdk · Req: R4, NFR-005. (Status: main 93.4 %,
  sdk 89.9 % after fixing the `adr` partition; the remaining patterns are listed in R4.)
- [x] T023 [P] [M2] Wider differential test against Unicorn (on real XCDE instructions: 6,000 + 15,000 encodings,
  62,934 cases, 0 failures; 30,000 per class not reached) · Req: FR-011.
- [x] T024 [P] [M2] Atomics as `__atomic` with the guest's ordering, `DMB/DSB` as fences; multithreaded stress test at
  `-O2` · Req: FR-011.
- [x] T025 [M2] First full build (main+sdk) with clang; measure time and size; tune chunking and `-O0/-O1`
  · Req: NFR-005 · Evidence: `docs/evidence/M2/build_time.md`.
- [x] T026 [P] [M2] `FRSQRTE`/`FRECPE` without long loops (ssbu lesson #44); exhaustive test of 1–4095 · Req: SC-009.

**M2 gate:** ≥ 95 % tables resolved, differential 100 %, `xcde_game` compiles, time measured.

## M3 — Boot (strict mode + diagnostics)

- [x] T027 [P] [M3] Watchdog (5 s without a frame → threads, locks, queues) → `runtime/diag/watchdog.c` · Req: FR-061.
  **Done 2026-10-17:** 5 s without a frame by default (`XCDE_STALL=<s>`, 0 turns it off); report on stderr and in
  `crash/stall_N.txt` with each thread's guest function, mutex owner and self / mutual deadlock detection; never blocks
  on `g_klock`. Test: `XCDE_TEST_HANG_AT=<frame>`.
- [x] T028 [P] [M3] Out-of-process minidump + crash report → `runtime/diag/crashdump.c` · Req: FR-062. **Done
  2026-10-17:** the exception filter writes `crash/crash_<date>.txt` and starts `xcde --minidump ...`, which dumps the
  process with `MiniDumpWriteDump` (≈ 1.2 MB). Test: `XCDE_TEST_CRASH_AT=<frame>`; `XCDE_NO_MINIDUMP=1` turns it off.
- [x] T029 [P] [M3] Deterministic mode + per-frame hash + input record / replay → `runtime/diag/` · Req: FR-060,
  FR-063. **Done 2026-10-17 (reproducible):** `XCDE_DETERMINISTIC=1` = cooperative scheduler (one guest thread runs at
  a time, switching only when it blocks / yields / every 4,000 SVCs, FIFO order), virtual time (advances only when all
  threads are blocked, or on a yield), vsync and audio buffers as virtual timers, synchronous shader builds, GPU
  counters and frame pacer without the real clock; `XCDE_FRAME_HASH`, `XCDE_INPUT_RECORD/REPLAY`, `tools/hash_diff.py`,
  `tests/routes/`. **Measured:** 3 runs (35–60 s, 2,299 frames, 2,007 distinct images) with 100 % identical frame
  hashes; with an input route (A at frame 600) 2,595/2,595 identical, diverging from the input-less run from frame 603.
  Limits: it is not the game "at real speed" (no pacing, the game sees a virtual 60 fps), a thread busy-waiting
  without SVCs would hold the baton, and only the title was measured.
- [ ] T030 [M3] Loader with the XCDE profile (main+sdk; `multimedia.nss` resolved through HLE) · Req: FR-010.
- [x] T031 [M3] **Test first:** a condvar with a timeout returns without the mutex → `tests/unit/test_condvar.c`
  · Req: FR-021.
- [ ] T032 [M3] **Test first:** a fiber resumed on another thread; 12,288 exception contexts freed →
  `tests/unit/test_fibers.c` · Req: FR-022.
- [x] T032b [M3] **Fiber HLE** on host fibers (Windows `CreateFiber`/`SwitchToFiber`):
  `nn::os::InitializeFiber/FinalizeFiber/SwitchToFiber/GetCurrentFiber`, a `Cpu` context per fiber, the fiber function
  returns the next one, symbols in `games/xcde/hle_symbols.txt` so the SDK's internal calls are replaced too
  · Req: FR-022 · Done when: boot gets past `SwitchToFiber` and `test_fibers.c` is green. (Found on the first boot: a
  crash in `nn::os::SwitchToFiber`.)
- [x] T033 [M3] Strict mode + a generated HLE audit · Req: FR-065, Art. VI. **Done 2026-10-17:** `XCDE_STRICT=1`
  stops the game with a report (unknown SVC, unimplemented IPC command, trap service, unimplemented HLE import);
  `XCDE_HLE_COVERAGE=<file>`; `tools/hle_audit.py` generates the audit (SVCs, services and HLE functions classed
  real / simplified / stub / unreviewed; manifest `games/xcde/hle_classes.tsv`); its `--check` runs in the tests.
- [x] T034 [M3] Boot in strict mode; record the SVCs, services, IPC commands, memory requests and NVN functions asked
  for → answers Q2, Q3 (partly), Q4, Q5, Q7. **Done 2026-10-17:** `XCDE_USAGE=<file>` records SVCs, IPC commands,
  HLE functions, NVN and memory requests; results in `docs/evidence/M3/usage.tsv`.
- [x] T035 [M3] Implement the missing SVCs (of the 50 declared, only the ones used) · Req: FR-020. **Done
  2026-10-17:** the 23 SVCs the title uses are implemented (0 unknown); the rest are unused.
- [x] T036 [M3] Missing services used (per T034); network / shop / friends as "offline" · Req: FR-020, FR-024. **Done
  2026-10-17 (title):** no network / shop / friends services are requested; the 9 unimplemented IPC commands (`am`,
  `pctl`) are audited and strict mode catches them.
- [ ] T037 [P] [M3] **Test first:** atomic saves and handle closing → `tests/unit/test_fs_commit.c` · Req: FR-023.
  (Later: save commits with a journal, b78be40.)
- [x] T038 [M3] `fsp-srv` over `targets/romfs` with 18.5 K files: listings and opens without copies · Req: FR-020.
- [ ] T039 [P] [M3] `movie::SetCoreMask` and `movie::MediaData::operator=` (the 2 missing in LAS) · Req: FR-042.
  (Done later, see T118.)
- [x] T040 [M3] Heap and memory map per Q5 (adjust `HEAP_MAX` if needed) · Req: FR-020. **Done 2026-10-17:** the game
  asks for a single `SetHeapSize 0xC9400000` (≈ 3.15 GB); `HEAP_MAX` 3.25 GB fits (≈ 0.1 GB margin).
- [x] T041 [M3] Reach the first `Present` · Evidence: log in `docs/evidence/M3/`.
- [ ] T042 [P] [M3] Minimal recorded route "boot → first frame" → `games/xcde/routes/boot.txt`.
- [ ] T043 [P] [M3] Per-function / per-thread profiler → `runtime/diag/profiler.c` · Req: FR-064. (Done later as the
  sampling profiler, `runtime/diag/sampler.c`.)

**M3 gate:** first `Present` without unaudited stubs; Q2, Q4, Q5, Q7 answered.

## M4 — Picture and sound up to the title

- [ ] T050 [M4] NVN functions used (T034's list) implemented or justified · Req: FR-030.
- [ ] T051 [P] [M4] Dump the shader universe with an emulator (from the user's own dump) to `targets/shaders/` and test
  the translator on all of it → answers Q3 · Req: FR-031.
- [~] T052 [M4] Maxwell opcodes missing in the translator · Req: FR-031.
- [ ] T053 [P] [M4] Persistent pipeline cache + prewarming off the game thread · Req: FR-032. (Done later: T187, T211.)
- [ ] T054 [P] [M4] Copies with the command buffer's own strides, no overruns; Vulkan validation · Req: FR-033.
- [ ] T055 [P] [M4] Check freed memory before writing compute results · Req: FR-034.
- [ ] T056 [P] [M4] CPU→GPU write tracking on Windows and Linux (userfaultfd + `PAGEMAP_SCAN`) · Req: FR-035.
- [ ] T057 [P] [M4] `VK_EXT_device_fault` + optional checkpoints · Req: FR-036.
- [ ] T058 [P] [M4] ASTC / BCn tests against a reference · Req: FR-037.
- [x] T059 [M4] Wwise audio output through `audren`/`audout`; a 60 s WAV compared with a reference · Req: FR-040.
  **Partly done 2026-10-17:** the real output is `audout:u` (not `audren`); 65 s PCM16 WAV in real time, tonal, no
  clipping (`tools/wav_report.py`). Against a reference recording (`tools/wav_compare.py`): chroma 0.92, same notes and
  band split.
- [~] T060 [M4] `hwopus` with libopus if Q4 confirms it · Req: FR-041.
- [~] T061 [M4] WebM cutscenes through `movie::` + FFmpeg, NV12→RGBA on the GPU · Req: FR-042. 2026-10-18: the New
  Game intro (`vs01000000.webm`) now plays (T118).
- [~] T062 [M4] Title screen identical to the reference (pixel threshold) · Evidence: `docs/evidence/M4/`.
- [ ] T063 [P] [M4] Freeing unused shader modules and pipeline libraries; a list of live textures · Req: SC-005.
  (Pipelines and libraries: b82a198, c262fe4.)

**M4 gate:** title right, a cutscene with audio, clean Vulkan validation.

## M5 — Gameplay (Story 2, playable MVP)

- [ ] T070 [M5] Test route intro → Colony 9 → battle → save → load → `games/xcde/routes/m5.txt` · Req: Story 2.
- [ ] T071 [M5] Fix whatever breaks the route (each bug with its route or test before the fix) · Req: Art. V.
- [ ] T072 [P] [M5] SDL3 controllers, keyboard / mouse, remapping, non-blocking rumble · Req: FR-043.
- [ ] T073 [P] [M5] Frame pacing with hysteresis · Req: FR-044.
- [ ] T074 [P] [M5] Window, F11, minimise / restore · Req: FR-045.
- [ ] T075 [P] [M5] Fonts and languages (`pl:u` + free substitutes) · Req: FR-046.
- [ ] T076 [M5] M5 route without a crash on machine A, deterministic over 10,000 frames · Req: SC-002 (partly), SC-010.

**M5 gate:** T076 with evidence.

## M6 — Whole game

- [ ] T077 [M6] Test playthrough plan per chapter; recorded routes per area · Req: SC-003.
- [ ] T078 [M6] *Future Connected* complete · Req: Story 2. (2026-10-25: a tour of all 11 maps passes, tests/tours/fc_all.txt.)
- [ ] T079 [P] [M6] Captures of every language · Req: FR-046.
- [ ] T080 [M6] Two people finish the game on different machines · Req: SC-003.

## M7 — Hardening (Story 3)

- [ ] T081 [M7] Automated 4 h soak with metrics (private memory, VRAM, handles, live textures) → `tests/soak/`
  · Req: SC-004–006. (Done later as `tools/soak.py`.)
- [ ] T082 [P] [M7] Go through every lesson of research R10 with its test · Req: R10.
- [ ] T083 [P] [M7] GPU matrix (NVIDIA, AMD, Intel iGPU) on Windows and Linux · Req: NFR-004.
- [ ] T084 [M7] Guest heap as driver memory on Linux / AMD · Req: NFR-004.

## M8 — Performance (Story 4)

- [ ] T085 [M8] Profile of the route on machines A and C; hot-spot list · Req: SC-009.
- [ ] T086 [P] [M8] NZCV flags in local variables in the generated C · Req: SC-008.
- [ ] T087 [P] [M8] Split submits and copies on helper threads · Req: SC-007.
- [ ] T088 [M8] Meet SC-007/SC-008/SC-009 with evidence.

## M9 — Release

- [ ] T089 [M9] A builder with every tool included (no game data) · Req: FR-007.
- [ ] T090 [P] [M9] Clean-machine test: dump → playing in ≤ 45 min · Req: SC-001.
- [ ] T091 [P] [M9] Linux AppImage · Req: NFR-002.
- [ ] T092 [P] [M9] README, build guide, FAQ of common errors · Req: SC-001.
- [ ] T093 [M9] Release CI: packaging + derived-file guard · Req: SC-012.
- [ ] T094 [M9] Review the constitution and spec when the release closes.
- [ ] T095 [M9] Offer LASRecomp the generic fixes upstream · Req: Art. X.

## M10 — PC improvements (Story 5)

- [ ] T100 [M10] Resolution scale 0.5–4.0 · Req: FR-050.
- [ ] T101 [P] [M10] Free aspect ratio with a widened 3D scene and an intact UI · Req: FR-051.
- [ ] T102 [P] [M10] Bilinear, FSR 1, SMAA · Req: FR-052.
- [ ] T103 [P] [M10] ImGui menu usable with a controller · Req: FR-053.
- [ ] T104 [M10] Unlocked frame rate only if Q6 allows it · Req: Story 5.

---

## Dependencies between milestones

```
M0 → M1 → M2 → M3 → M4 → M5 → M6 ─┐
                  └─ (diag T027–T029 in parallel)  ├→ M7 → M8 → M9 → M10
                                         M5 ───────┘
```

- T020–T022 (tables) can start in parallel with the rest of M1 (they only read the dump).
- T051 (shader dump) can start any time after M0.
- M7 and M8 can overlap once M6 is closed.

## MVP strategy
1. M0–M5 = playable MVP (Story 1 + the start of Story 2).
2. Validate with the M5 route before opening M6.
3. Each later milestone adds demonstrable value without breaking earlier routes.

## Tasks added in session 1 (M4)

- [x] T064 [M4] **Programs without a fragment shader** (depth-only passes: shadows, z-prepass): `get_program` returned
  NULL when the VS or FS stage was missing and the draw was dropped (≈ 671 a frame). Support pipelines without an FS
  · Req: FR-030 · Done when: 0 draws dropped by `exec.c` "program NULL" on the title run.
- [~] T065 [M4] Storage images for `SULD`/`SUST` (translator + `STORAGE` + `uint` view + descriptor type 6). Done in
  code; **still to verify** (barriers between draws reading / writing the same image; the real surface format of the
  classification pass) · Req: FR-031.
- [x] T066 [M4] Rendering to slices of 3D textures (`2D_ARRAY_COMPATIBLE`, a 2D view per slice). Done in code;
  verified: the colour LUT is no longer zero · Req: FR-030.
- [x] T067 [M7] **Intermittent hang** (stops after 4–8 s without a crash; does not reproduce with the watchdog on).
  **Closed 2026-10-17:** cause = a race between `pthread_cond_timedwait` (ETIMEDOUT) and a condvar signal that had
  already handed over the mutex; `block_current` turned it into `R_TIMEOUT` and the thread blocked on its own mutex.
  Fix in `runtime/kernel.c`; `XCDE_STALL=<s>` watches for future hangs. 47/47 clean boots (before ≈ 1/30 hung).
- [x] T068 [M4] **Black final image** (SOLVED 2026-10-17: the cause was the 3D deswizzle, blocks 1 GOB tall and depth
  by d+d/2; see `runtime/nvn/tegra.c`; the title is right in the window).
- [ ] T069 [M4] Take the LAS-specific hooks out of the renderer (widening, mirror, flower pots, `texpatch`, `menu_*`)
  and delete `runtime/host/stubs_gfx.c` · Req: Art. IX.
- [ ] T070 [M4] Exact `PTP` for `TLD4` (per-texel offsets) and `SUST` in D/P modes with 8/16-bit sizes, when a shader
  uses them · Req: FR-031.
- [x] T105 [M4] (SOLVED: point sprites from an unsupported geometry shader; GS implemented) A regular dot pattern over
  the whole title image.
- [x] T106 [M4] (NOT A BUG: the reference shows no logo at that point either) The title logo missing (only "Press Any
  Button"), and an opening fade with a grey rectangle at the bottom right.
- [x] T107 [M4] (SOLVED 2026-10-17: two NVN texture objects over the same memory - the stencil-mode view of the
  G-buffer depth - had different Vulkan images; they share the image now) **Unlit title foreground** (Monado / rocks /
  grass as dark silhouettes). G-buffer right; the light accumulation pass came out black for everything but the sky.
  Fixed on the way: SULD/SUST size D and image binding (`st.img`). Tools: `XCDE_DUMP_TEX=<pass>`, `XCDE_TRACE_ATTR`,
  `XCDE_TRACE_CB`.
- [x] T108 [M7] Intermittent close while loading resources (~2/30 boots, frame ~200-700): the game's allocator returned
  an address outside the mapped heap in f_700067b830. **Closed 2026-10-17:** cause = the virtual RomFS descriptor cache
  in `runtime/services/romfs_virtual.c` had no lock (one thread closed another's fd in the middle of a `pread` ->
  silent zeros -> a zeroed resource header -> an absurd size in the allocator). Fixed with a mutex + a per-slot user
  count; read errors are logged now. 47/47 clean (before ≈ 3/30).
- [ ] T109 [M4] Geometry shaders: tested only with the title's two (point -> quad). Missing: lines / triangles with
  adjacency inputs, several streams, `gl_in[].gl_PointSize` and the MSL path.
- [ ] T110 [M4] The backend shares an image between NVN textures with the same address / size / compatible format:
  extend to views with another format of the same texel size, and to partial overlaps if a game uses them.

## Candidate tasks from the WindowSmash review (2026-10-17, see `docs/lessons_windowsmash.md`)
- [ ] T111 [M7] Whole-function differential tests (Unicorn vs native, registers + memory) for leaf functions of `main`/`sdk` -> `tests/diff/` · Req: SC-002.
- [ ] T112 [M3] Sampling profiler: sample guest thread instruction pointers, map to `f_<addr>`, report per function/thread (finishes T043) · Req: FR-064.
- [ ] T113 [M2] Cross-check function discovery against exception-frame tables (`.eh_frame` extents) · Req: FR-010.
- [ ] T114 [M8] Tail-call helper so guest tail transfers do not grow the host stack · Req: SC-008.
- [ ] T115 [M5] Static IPC/service reachability census (lower bound) for what the game needs after the title.
- [ ] T116 [M5] User-facing frame capture hotkey (F3) and draw diagnostics, to make playtest reports easier.
- [x] T117 [M3] Static import census (`XCDE_LIST_IMPORTS=1`): 0 unimplemented imports; 64 MB stacks for shader build threads; `-ffp-contract=off` (2026-10-17).

## Session 4 (2026-10-18)
- [x] T118 [M4] **Intro video showed grey static with vertical stripes.** Cause: `Decoder::GetOutputBuffer` ignored the game-owned memory in the `movie::Buffer` it was given (Buffer(void*, size) + SetRange) and pointed it at the HLE slot; the game reads its own memory, which its uploader (f_70005a8590) fills with LCG noise at init. Fix: `mbuf_fill_output` copies into game memory (not into our own slots). Test: `tests/native/test_movie_buf.c`. Measured: capture noise score 21 -> 0.03-1.2 at frames 1800/2400/3200 of `tests/routes/new_game_a.txt`; audio WAV report identical to the pre-fix baseline · Req: FR-042.
- [x] T119 [M3] Deterministic runs diverged in ~7-11 % of frames from frame ~1780 (intro video, mostly a one-frame shift). Measured per stage: the guest side was identical (movie handoff trace, hashes of the frame buffers at every frame and every submit); hashing every pass with a GPU sync made it identical; ruled out FFmpeg threads, GPU batching per submit, texture upload shortcuts. Cause: the vertex cache (`vcache_lookup`/`vc_flush`, refreshed from OS write tracking and copied on the GPU). Fix: off in deterministic mode (vertices read in place, as `LARECOMP_VK_VCACHE=0`). Measured 2026-10-18: 3 concurrent runs of `tests/routes/new_game_a.txt`, 5245/5245 frames identical (before: identical prefix 1779) · Req: T029.
- [ ] T121 [M7] Why the vertex cache gives run-to-run differences (T119): its refresh decision (write tracking shared with texture checks, GPU-side copies from guest memory) may leave stale vertices for a frame in normal play too. Reproduce with `LARECOMP_VK_VCACHE=1 XCDE_DETERMINISTIC=1` (forces it on) and two runs + `tools/hash_diff.py`.
- [x] T122 [M5] Route stopped presenting at frame 5245 in deterministic mode. Cause (host stacks of the stuck threads, new in the thread dump): the movie HLE holds `d->lock` across a guest call (`dec_signal` -> `nn::os::SignalEvent`, an SVC that can pass the baton); the baton went to a thread that then blocked on `d->lock` -> deadlock (real-time mode unaffected). Fix: `kernel_det_mutex_lock` (deterministic mode: yield the baton while the HLE mutex is busy) for all movie locks. Measured 2026-10-18: runs reach frame 8000+ ("Eons have passed.", then the first 3D scene), 0 stall reports, scheduler SVC digest identical in 2 runs on 8242/8242 frames.
- [ ] T124 [M3] Image hashes still split between deterministic runs: from frame ~6027 (first 3D scene) in every pair, and in some pairs already during the movie (2057, 2326, 2510). The guest is identical (`XCDE_DET_DIGEST`), so the cause is renderer-side. Per-pass hashes (`XCDE_PASS_HASH`, with a GPU sync per pass) differ in G-buffer passes 86-97 drawing large mip-mapped compressed textures. Ruled out: exact texture uploads (`XCDE_TEX_EXACT=1`), zero-cleared new colour targets, zero-padded cbufs, flush per submit. Next: hash the VkImage contents of those textures per frame, and the gmem ranges their draws read. Rechecked 2026-10-18 after T133/T134/T138 (two runs to frame 9000, three game processes at once): SVC digests identical on 8999/8999 frames; image hashes differ on 1900 frames: 914-916 (menu transition) and from 6171 on (first 3D scene) - not fixed by the barrier / transform feedback work. Candidate to check first: the renderer's texture change detection (CPU write tracking) runs on the render thread while guest loader threads write texture memory - its timing, not the guest, decides when a streamed texture is re-uploaded.
- [ ] T123 [M4] Passes 111/120/121 of the intro frames differ between runs although the final image does not (`XCDE_PASS_HASH`): probably uncovered regions of fresh render targets (uninitialised memory). Clear new targets in deterministic mode if it ever reaches the screen.
- [ ] T120 [M4] Candidate: a fragment shader with no output for a bound render target (omap nibble 0) should leave it untouched (Maxwell); Vulkan writes undefined values. Set `colorWriteMask = 0` for those targets. Seen on the intro's off-screen marker draw (no visible effect there) · Req: FR-030.

## Candidate tasks from three other recomp projects (2026-10-18, see `docs/lessons_other_recomps.md`)
- [~] T125 [M4] Program cache keyed by shader content as well as address (streamed shaders reuse addresses; Let's Go #66). Done 2026-10-18 (hash per stage in `set_shaders`); route to frame 8000 unchanged (digest equal). Not yet exercised: a zone change that reloads shaders.
- [x] T126 [M4] Constant buffer reads past the bound range return 0 (Maxwell): zero-padded copy in `cbuf_info` (Wonder #21). 2026-10-18: route clean, captures unchanged.
- [x] T127 [M4] `LDC.64` when the address register is also a destination (Let's Go #21): our translator had the bug; address snapshot in a temp. Test `tests/native/test_translate_ldc.c` (failed before, passes now).
- [~] T128 [M4] Upstream LAS fixes (credited PRs on its development branch): #108 fence sequence of a stale ring slot and #127 timed-out GPU wait now fatal + checked counter query - applied 2026-10-18. Still to compare: null colour slots, duplicate pipeline keys, IPA multiply, I2I/SHF/HSETP2 (Let's Go #62).
- [ ] T129 [M4] Textures / pool slots re-initialised between recording and execution (Wonder #55-57, Let's Go #60); candidate cause of T124.
- [ ] T130 [M4] Movie decoder: rotate output slots; end-of-stream code 0x2000 (Let's Go #13, #16).
- [ ] T131 [M4] Shader semantics audit: integer vertex inputs, sRGB view formats, FMZ, NaN in .SAT/FMNMX, TMML, RGB5A1/RGBA4.
- [x] T132 [M4] Transient upload ring must not overwrite data a pending submission still copies (Wonder #72). Checked 2026-10-18: not affected - `vk_transient` reuses a chunk only when every submission that allocated from it has completed; big uploads get their own chunk.
- [x] T133 [M4] **Exploded hair/cloth in in-engine cutscenes** (real-time too). Cause: `nvnCommandBufferBarrier` was dropped (CMD_BARRIER unimplemented). XCDE writes skinning palettes from point-draw vertex shaders into a scratch range reused per mesh; without the barrier the writer and mesh draws overlapped on the GPU. Fix: barrier with bits ends the render pass (next pass starts with a full barrier). Measured 2026-10-18: frames 9600/11400/12000/13800 of `tests/routes/new_game_a.txt` show the characters intact; ~22 fps deterministic (unchanged) · Req: FR-030.
- [x] T134 [M4] **Black grass** (thin black streaks over the ground, frame 11400 of `tests/routes/new_game_a.txt`; seen by the user in play). Cause: **transform feedback was not implemented** (the 7 `nvnCommandBuffer*TransformFeedback*` entry points and `SetRasterizerDiscard` were no-ops; ~117k / 757k calls on the route). XCDE animates grass with a point draw whose vertex shader output is captured (stride 24: v0.xyz, v1.xyz) into a scratch buffer that the grass draws then read as vertices; with no capture they read leftover data (skinning matrices from the same range), so the depth prepass drew long streaks and the G-buffer grass failed its EQUAL depth test (G-buffer pixels never written = black). Layout found in the NVN control section (9 capture shaders, all buffer 0: `[0x6e8]` count, `[0x6dc]` stride, `[0xdc+i]` slot 0x20+k = v_k, `[0x4dc+i]` components). Fix: capture emulated as heap stores in a vertex shader variant (`ShaderKey.xfb_*`, uniform `XfbP` binding 22), appended per draw; rasterizer discard = empty scissor; a draw that stores to memory ends the render pass (graphics STG now sets `uses_gmem_store`). Test: `tests/native/test_translate_xfb.c`. Measured 2026-10-18: frame 11400 G-buffer albedo has 0 % unwritten pixels (before 3.35 %); grass renders as grass · Req: FR-030. Debug switches: `XCDE_DUMP_CONTROL=1` (control sections to `build/ctrl/`), `[barrier]` / `[xfb]` lines in the debug frame log.
- [x] T138 [M7] **Deterministic run hung at frame 7** (watchdog: the baton holder was a new guest thread that never made an SVC; seen with three game processes running). Cause: on Windows (winpthreads) an explicit pthread stack size is *committed*: 256 MB per guest thread (~38 threads ≈ 10 GB per process) + 64 MB per shader worker; at the commit limit `pthread_create` failed and its result was ignored, so the thread was runnable with no host thread. Measured with a test program: 8 threads with a 256 MB stack size = 2052 MB private; with the 256 MB as the exe's default reservation (`-Wl,--stack,268435456`) and no explicit size = 4-8 MB, and 200 MB-deep recursion still works. Fix: no explicit stack size on Windows (kernel.c, exec.c), link flag in `link_gfx.sh` / `link_boot.sh`, `pthread_create` failure is now fatal with a log line. Measured 2026-10-18: game private memory 4.6 GB at frame 3200 with 92 threads.
- [ ] T136 [M4] Near-camera grass still black after lighting at frame 11400 (bottom-left tuft): correct in the G-buffer albedo, black in the final image. Check its normals (NaN from a zero-length v1?) and the depth-of-field passes. 2026-10-18: the tuft is NOT black in the tonemapped 853x480 scene (last debug pass image); it turns black in the last full-res pass (vs `72c28b6d00` / fs `72c28b6f00`, 1280x720 to `7252b74000`, before the composite `72c28d0400` to the window): probably near-field depth-of-field compositing; the half-res passes 276-303 of that frame are all zero (DOF near buffers?).
- [x] T137 [M5] **Party and enemies invisible on the battle field** after "Battle Introduction 1" (closed with A at frame 16600, `tests/routes/new_game_b.txt`). Measured: the game issued no character draws at all in gameplay (frame 17000: none of the skinned character programs drawn in cutscenes). Cause: `nvnCommandBufferReportCounter` wrote 0 for every counter type; type 1 is samples passed (occlusion), which XCDE uses to cull field characters and enemies (~0.8 M reports per run), so everything was "hidden"; `ResetCounter` was a no-op too. Fix: T139. Verified 2026-10-18 (`tests/routes/new_game_c.txt`, deterministic): frames 17000/17300 show Dunban, Dickson, Mumkhar and the Mechon; walking, camera, L targeting ("Battle Introduction 2") work.
- [x] T139 [M4] Samples-passed counters as Vulkan occlusion queries: `ResetCounter`/`ReportCounter` type 1 recorded; one query per render pass while counting (a query can't outlive its pass), a report sums the segments since its reset; resolved when the submission completes (like the timing counters), "visible" until then and when it can't be told. Deterministic mode: always "visible" (GPU results must not steer the game); `XCDE_OCCLUSION=0` forces that too. Stats line: `occlusion N (M hidden)`. Verified 2026-10-18 in real time (`tests/routes/realtime_tap_a_long.txt`, 35k frames, 30 fps): ~7.8k reports per 2 s in battle, ~1k hidden; party and Mechon drawn as in the game's own tutorial picture; no stalls.
- [x] T140 (NOT A BUG 2026-10-19: the Switch video shows the same orange bars on the bottom edge) [M5] Battle HUD: the party HP panel seems cut off at the bottom edge ("Warning!" and orange bars at the very bottom corners). Compare with a reference capture of the Switch version before touching it.
- [ ] T135 [M7] Intermittent startup failure `guest address range 7000000000-7320000000 is not free` (another allocation got there first; a retry works). Reserve the range earlier or retry.
- [x] T141 [M2] **Crash on the first attack in battle** (`FATAL: no function at 70005264e8`, `tests/routes/new_game_d.txt` frame ~18750). Cause: a byte jump table whose bounds check tests one copy of the index (`ldr w8,[sp,#0x14]; cmp w8,#3`) while the lookup reloads another from a stack slot (`ldr x8,[sp,#8]; and x8,#0xff`); the resolver set only the compared register, so every index gave the same garbage target and the table was taken as resolved with one wrong case. Fix (`tools/lifter/gen.py`): the index value also fills the emulator's scratch stack window, and a multi-entry table resolving to a single target is rejected (any-instruction fallback). Tests: two new cases in `tests/unit/test_jumptables.py` (failed before). Effect: main 732 -> 728 resolved tables (4 now safe fallback, 2 corrected), sdk 492 -> 490. Measured 2026-10-18: the route plays the battle to frame 20000 with no crash.
- [ ] T142 [M4] Systematic audit of NVN entry points that are no-ops or partial and that the game calls (`XCDE_USAGE` census): every graphics bug of session 5 was one (barrier, transform feedback, rasterizer discard, occlusion counters). Implement or justify each.
- [ ] T143 [M4] Automatic per-frame detectors on routes: unwritten render-target pixels, NaN/Inf, draws with zero samples where the depth/stencil test should pass, HUD clipped at the edges; report frame + draw.
- [ ] T144 [M4] Reference comparison: capture the same route points in a reference emulator (a reference emulator, permission pending) and diff images region by region.
- [x] T145 [M4] (fixed by T147) Battle Palette: the orange/red piece above the centre circle (left of the blue tab) looks like a wrong mask/clip (user report, frame ~18750 of `new_game_d`). Dump its draw: texture, mask, blend/stencil.
- [x] T146 [M4] **Everything rendered at 853x480 in a 720p window** (scene and HUD; soft HUD text). Cause: `runtime/nvn/output_scale.c` (from LASRecomp, whose game drew for the Switch's 1920x1080) scales the game's 16:9 render targets by window height / 1080; XCDE's frame is 1280x720, so the factor was 0.667. Fix: the base is the game's own window-texture size (`output_scale_set_base` from `nvnWindowInitialize`). The earlier note "853x480 is the game's dynamic resolution" was wrong. Also measured: reporting handheld 1280x720 (`XCDE_HANDHELD=1`, test switch in `am.c`) gives a pixel-identical loading screen, and the game never asks for the operation mode or display size: the HUD/loading-icon clipping at the bottom-right is not caused by that (the loading Monado enters diagonally from the corner: probably by design; needs a Switch reference). Verified 2026-10-18: log `[scale] the game renders for 1280x720`, captures at 1280x720 native (sharper HUD text and scene); deterministic 3D ~15-16 fps (more pixels).
- [x] T147 [M4] **Small textures decoded scrambled** (user report: loading-screen kanji off-centre and cut; Battle Palette orange piece). Diagnosed draw by draw (`XCDE_SPLIT_DRAWS`, per-draw constants, `XCDE_DUMP_TEX_ADDR`): geometry and constants were right, the 80x80 BC7 texture decoded wrong. Cause: wrong default block height. Three rules were tried against textures checked on screen: the original pow2_round_up(ceil(rows/8)) scrambled the kanji (20 rows) and ring glow (36); pow2_round_up(floor(rows/8)) fixed those but broke the Battle Palette slots (14 rows) and striped the enemy bar; largest pow2 <= ceil(rows/8) fixed the slots but broke portraits and button icons. Final: thresholds on 1.5x the rows (>= 128 -> 16 GOBs, 64 -> 8, 32 -> 4, 16 -> 2, else 1; tegra_swizzle's block_height_mip0, same family as our 3D rule) - every element correct. Fix in `runtime/nvn/tegra.c`; test `tests/native/test_tegra_block_height.c` (2 failures on the old rule). Verified 2026-10-19: the loading-screen ring matches the user's YouTube reference (kanji centred, ring glow, stray pieces gone). Debug switch kept: `XCDE_BH_TEST=<w>x<h>:<log2>`.
- [~] T144 [M4] Reference comparison against the user's Switch playthrough video (not versioned): frames at 1 fps in `<work dir>\full` (1080p) and `idx` (320x180); `tools/ref_compare.py <captures> --window from-to` pairs each capture with the most similar second and writes ours | reference | flagged cells to `<work dir>\cmp`. The automatic pass is a first filter; every pair is also reviewed by eye (user request). Prologue: captures 6900-14700 of `new_game_d` match video seconds 110-276 (corr 0.85-0.97).
- [x] T150 [M4] (NOT A BUG - the video's processing) **Colour: our shadows looked bluer and darker than the Switch video** - consistent over 10 matched prologue scenes (video range-corrected 16-235 -> full): darkest 20 % of pixels ours - reference = R -14, G -13, B -5 on average; whole frame R -12, G -8, B +2; red often clipped to 0 in ours. Not explained by the video encode (that would shift R, G, B alike). Suspects: colour-grading LUT (3D 16x16x16), a missing haze / ambient lift pass, tonemapping / sRGB handling. Resolved 2026-10-19 (user doubted it, rightly): on the loading screen, which skips the colour grading, the console's pure black is 29 raw / 15 range-corrected in the video and the blade blue shows the same R/G-more-than-B lift (ours 14,25,58; video corrected 27,40,65): the offset is the video's (lifted blacks + colour-space conversion). `ref_compare.py` now fits each pair's levels per channel before comparing.
- [~] T151 [M4] Vulkan validation findings: (a) point-list draws with no point size written (VUID-...-topology-08773 / 10748) -> vertex shaders always write gl_PointSize = 1; (b) *_UINT textures sampled through float samplers (VUID-vkCmdDrawIndexed-format-07753, R8_UINT seen) -> marked usampler (raw bits, as Maxwell). Built; a 100 s validated run after the fix showed no errors (partial). The validation layer leaks Windows handles (~3.5 M / 15 s, process dies with error 1450 in the intro); normal runs stay at ~1,900 handles - not our bug, limits validated runs.
- [x] T152 (run 2026-10-19 on new_game_d, N=300, frames to 20500: zero NaN/Inf texels in any float target) [M4] NaN/Inf detector `XCDE_CHECK_NAN=<N>` (float colour attachments read back at pass end every N-th frame, `[check-nan]`): written, not yet run.

## Session 7 (2026-10-19)
- [x] T153 [M5] Battle tutorial played to its end (`tests/routes/new_game_h.txt`): close "Battle Introduction 3" and "Using Arts 1" with A, walk to the target (stick), Enchant = D-pad left + A, Buster = D-pad right + A, Monado = A on the centre slot; damage numbers, buff icons, Mechon M82 bar, break/topple text, cutscenes and the Monado flash all show; audio alive (97 % of seconds above -60 dBFS). Earlier routes (`new_game_e/f/g`) only explored the input: popups swallow A, arts need range.
- [~] T136 grass: diagnosed to the colour pass. Per-draw images (`XCDE_SPLIT_DRAWS=<pass>` + new `XCDE_SPLIT_DRAWS_TO`): the near tuft's black blades are albedo pixels where the EQUAL-depth grass draws (`vs 72c2938600`, ds EQUAL, no depth write) fail against the prepass (`vs 72c292cc00` / `72c292c700`). `LARECOMP_VK_EQUAL_TOL=1` (LEQUAL + bias) does NOT fix it: it shows huge garbage shards, so the colour-pass instance data differs from the prepass data (not a few ulps). Prepass draws take records 0..373 of the XFB scratch in the order 16 draws (vs cc00) + 6 draws (vs c700); the colour pass interleaves the small draws (2,2,1,1,2,1 instances) among the large ones with the same scratch.
- New tools: `XCDE_SKIP_GPU_UNTIL=<frame>` (no GPU work before that frame; the scene stays black afterwards - baked GPU content - so it is only for logic tests), `XCDE_SPLIT_DRAWS_TO`, `XCDE_EXE=build/other.exe scripts/build_rt_gfx.sh` (separate exe, doesn't kill running games), `tools/contact_sheet.py` (reference video), `tools/shot_sheet.py` (our captures), `scripts/drive_env.sh` (drive.sh with retry for T135 and env passthrough).
- [x] T154 [M4] (root cause found 2026-10-20: T176 entry) **Cliffs in shade navy blue in the field** (user report too; Switch video: olive). Traced: G-buffer albedo correct; the probe-lighting pass (fs `72c2d52000`, cube-array `samplerCubeArray`) and its input, a 64x64 RGBA16F cube array built each frame from seven 64x64 BC6H time-of-day cube maps (fs `72c2900b00`), were wrong. Guest memory of those cubes (`XCDE_DUMP_MEM`, field frame 42000): each face = 15 GOBs of data + 1 empty GOB = 8192 bytes; `tegra_layer_size` aligned faces to the level-0 block (2 GOBs: 7680 bytes), so faces 1-5 were read shifted. Fix: layers aligned to at least 16 GOBs.
  - 2026-10-19: after that change the cliff is STILL navy (run to frame 42010 with XCDE_SKIP_GPU_UNTIL=40500): the stride was wrong but is not the cause. Next: the probe pass inputs (cb6 probe list, weights texture 640x360 f0x29, the R11G11B10 cube array).

## Session 8 (2026-10-19) - performance (user goal: hyper-optimized port)
- [x] T155 [M8] **Scene-change hitches from 3D LUT uploads.** Cause (measured with `XCDE_PROF_UPLOAD=1`): a debug block in `textures.c` scanned every uploaded 3D texture byte by byte to log its non-zero count - reading `lin`, which is the transient ring (write-combined BAR memory, ~3 MB/s to read). Before: 5.3-6.0 ms per 16x16x16 LUT, 70-80 ms per 64x64x15 one (11 ms with the ring in system memory). After: no 3D upload over 2 ms on `new_game_h` to frame 12000 (the copy itself is ~50 us). The scan now needs `XCDE_TRACE_3D=1`. Remaining upload cost: 2-3 ms per 2048x2048 BC texture (12 levels, 2.7-5.3 MB) on the render thread, 58 such over 12000 frames.
- [x] T156 [M8] **Test runs capped at 60 fps wall-clock** (deterministic + hidden). Cause: Windows composes even a hidden window's presents at the monitor refresh (mailbox and immediate both 60.0 fps; with the present skipped 145-150 fps in light scenes). Also every deterministic run hashed the window image each frame by default (readback + GPU wait). Now: hidden deterministic runs draw into the window only on frames captured or hashed (`XCDE_PRESENT_ALWAYS=1` restores it); frame hashes only with `XCDE_FRAME_HASH=<file>` (as the routes README already said). `new_game_h` to frame 12000: 333 s -> 227 s; the capture at 12000 is pixel-identical to the old path.
- [x] T112 [M8] **Sampling profiler** `XCDE_SAMPLE=<from>:<to>` (presented frames; `XCDE_SAMPLE_HZ`, default 1000; `XCDE_SAMPLE_OUT`, default `build/samples.txt`): every thread of the process, each thread's CPU cycles since the last tick (QueryThreadCycleTime) charged to its current instruction; report per thread (guest threads now named `guest t<id> p<prio> f_<entry>`, shader workers named), per module, per function, per busy thread, and the hottest instructions. Exe symbols from the PDB by enumeration (dbghelp's SymFromAddr fails on lld PDBs with error 126; in-process dbghelp also didn't find `xcde.pdb` because the exe names it without a directory - `plat_symbol` now searches the exe's directory). Offline: `tools/exe_sym.py <exe> <rva>... [--dis N]`, guest addresses: `tools/lifter/sym.py`.
  First profile (real time, prologue cutscenes, frames 6500-8000, 51 s): 1.38 cores busy - main game thread 0.77, GPU submit thread 0.37. Findings fixed below (T158, T159); the main thread's spin is T157.
- [x] T158 [M8] **128-bit software division on every clock read**: `rt_ticks` (ns * 192 / 10000) and `plat_now_ns` (QPC * 1e9 / f) used `__int128` multiply-divide (compiler-rt `udivmod`, 8 % of all samples - the game polls the tick in its frame limiter). Now exact 64-bit quotient/remainder forms; `tests/native/test_time_math.c` checks 4 M values against the 128-bit result.
- [x] T159 [M8] **getenv on hot paths**: ~10 debug-switch `getenv` calls per draw (each scans the environment: ucrtbase `strchr` 4.9 % of all samples, 20 % of the submit thread). `runtime/env_cache.h` redefines getenv as a per-call-site cached read in exec.c, textures.c, device.c, objects.c, cmdbuf.c (the environment only changes before the game starts). Measured with T158: total 1.38 -> 1.30 cores, submit thread 0.37 -> 0.29 cores (-22 %); ucrtbase 4.9 % -> 0.1 %.
- Note: `zig cc` passes `-O2` to clang for -O1, -O2, -O3 and -Ofast alike (identical objects): the build is already -O2 with vectorization, nothing to gain from flags there.
- [x] T157 [M8] **The game's frame limiter busy-waits** (nnMain+0x12150, `f_70005bcfe0`: loops reading the system tick through a vtable until 33.3 ms passed, no sleep - a dedicated core on the Switch). Patch (games/xcde/patches.py, two hooks: loop head and exit) + `runtime/hle/framepace.c`: learns the frame interval (shortest of the last 8, used only when they agree within 3 ms) and sleeps on a high-resolution timer until 1.5 ms before the predicted end; if the game leaves the wait right after a sleep (target earlier than predicted), it relearns. Deterministic runs untouched. `XCDE_LIMITER_SLEEP=0`: off. A/B in real time (prologue cutscenes, frames 6500-8000): main thread 0.77 -> 0.31 cores, whole process 1.31 -> 0.85 cores (-35 %); frame periods unchanged (median 33.25 / 33.25 ms, p99 47.1 / 46.5 ms). Both runs show ~4.5 % of frames over 40 ms: a separate hitch problem (T160).

### Performance backlog (review 2026-10-19, measured on the prologue: real time, RTX GPU + an 8-core desktop CPU)
Numbers per 2 s at 30 fps unless said. Order = expected gain / risk.
- [ ] T160 **Frame-time hitches**: ~4.5 % of frames over 40 ms, p99 47 ms, max ~70 ms, in cutscenes where the work fits easily. Find what the long frames have in common (pace log + XCDE_SAMPLE window around them + GPU timestamps): uploads, feedback copies, pipeline compiles, GPU waits.
- [x] T161 (2026-10-19) **Feedback snapshots (`fbcopy`)**: classified with `XCDE_FB_STATS=1` (prologue route, 8.2 M copies): 99.8 % were colour targets 1280x720 sampled by the game's UI uber-shaders (13 texture slots, branches picked by uniforms), not depth and not mip chains (a level/layer overlap check was added anyway: `feedback_overlaps`). Now colour feedback samples the attachment itself (GENERAL layout, as Maxwell reads render-target memory): 5.57 M copies -> 0, captures identical at 5 points (max 2/255 on 0.2 % of one frame), battle 23.8 -> 27.7 fps deterministic (+16 %), validation layers quiet. `LARECOMP_FEEDBACK_DIRECT=0` restores snapshots. Was: : 3,500-106,000 per 2 s (up to ~1,700 per frame in battle, where fps fell to 25 and the CPU waited ~1 s per 2 s on the GPU). Each one ends the render pass, issues a full pipeline barrier and copies the whole attachment. Most draws only *read* the bound depth (soft particles, depth-tested reads): those need no copy (read-only depth layout / VK_EXT_attachment_feedback_loop_layout, or depth-write-off detection); true feedback can copy only the region / once per content change.
- [ ] T162 **Render passes**: 20,000-47,000 per 2 s (330-780 per frame). Causes to count: CMD_BARRIER ends the pass for any non-zero bits (refine by bits: ORDER_FRAGMENTS / texture invalidation only need a barrier, not always a pass break; scratch-writer draws could use a buffer barrier), feedback copies, XFB/storage draws, clears. Each break = load/store of all attachments.
- [ ] T163 **Pipeline compiles in play** (up to 98 per 2 s on first sight): precompile from the SPIR-V/pipeline caches at boot or in the launcher, async compile with a fallback, VK_EXT_graphics_pipeline_library.
- [~] T164 (2026-10-19: deswizzle moved to the GPU, see below) **Texture uploads on the render thread**: 2-3 ms per 2048x2048 BC texture (12 levels); 25-75 MB/s of uploads. Move deswizzle + copy to worker threads / a transfer queue; skip re-hashing unchanged textures.
- [ ] T165 **Generated code: registers in memory**. Every guest register lives in `c->x[]` and is reloaded after any guest store (aliasing); flags are stored to `c`. Promote registers to locals within a function (spill at calls / indirect jumps / returns), compute flags lazily. Biggest CPU item; validate with the ~107,000-case differential tests. Also `rt_dispatch` (4 % of samples): direct calls for known targets, inline cache for vtable calls.
- [ ] T166 **Guest synchronisation**: InternalCriticalSection Enter/Leave + LockMutex were ~10 % of the main thread; check the HLE fast path (uncontended lock = one atomic, no kernel call).
- [ ] T167 **GPU time**: GPU ~33 % busy in cutscenes but the CPU waits on it up to 50 % in battle: per-pass GPU timings (`LARECOMP_GPUPROF_AT`) on a battle frame; occlusion queries per pass; full barriers at every pass begin (`vk_full_barrier`) -> precise barriers.
- [ ] T168 **Startup / loading time**: measure boot-to-title and scene loads; RomFS reads, shader cache load, pipeline cache load.
- [ ] T169 **Memory**: 4.0-4.6 GB private; check descriptor pools, snapshot images (16), transient ring sizing, texture copies kept twice.
- [x] T170 [M5] **Crash after accepting the bonus with audio on** (user report, 2 crashes, same pc): the intro movie's own IAudioOut appends AudioOutBuffer structs with `next` and `offset` uninitialised (sample bytes); samples + offset pointed nowhere and the audio thread crashed in SDL's copy. Offset now used only when it fits inside the buffer (as the emulators, which ignore it). Reproduced in real time with the user's xcde.ini (German, audio on at gain 0): crash at 47 s before, past frame 4400 after. Test runs never saw it (no audio device in them).
- [ ] T171 [M4] Intro movie audio is silent: its IAudioOut gets all-zero buffers (game output 80 % active, movie output 0 %). Check how the movie HLE hands decoded Vorbis PCM to the game (the T118 class: a pointer replaced instead of data copied?).
- [x] T172 [M5] **Tests from the user's save** (Colony 9, saved 2026-10-19 12:33; backup `<work dir>\saves\colony9_20261019_1235`, never versioned): `DRIVE_SAVE=<dir> scripts/drive_env.sh tests/routes/load_a.txt ...` (Load Game -> newest save -> Yes) reaches the Colony 9 field at frame ~2400 in ~1.5 min (was ~35 min to frame 42000 with XCDE_SKIP_GPU_UNTIL). Drives now always use a scratch save folder (`build/save_<name>`, LARECOMP_SAVE_DIR), never the user's `save/`. `XCDE_SHOT_FROM=<frame>` starts XCDE_SHOT_EVERY's 400 captures there. Seen: the load list's save thumbnails are blank (minor, to do).
- [x] T171 not a bug: the intro movie's own audio track is silent in the file itself (ffmpeg volumedetect -91 dB over 86 s); narration and music play through the game's audio.
- [x] T173 [M4] (NOT A BUG - the game's own effect) **Characters / grass drawn black near the camera**. Resolved 2026-10-19: the user's Switch video shows the same thing (reference frame 6730, Military District: a character the camera passes through is a black silhouette with lit rims, then a dithered fade). Mechanism, measured: per mesh, the game switches the material to silhouette constants (cb7 = 0.1,0.1,0.1 | 2,1,1: albedo x0 plus a faint rim) and swaps the depth prepass to a dithered program (fs 72c2958d00: 256x8 RGBA8 atlas of 64 4x8 patterns, layer = opacity x 64 from a per-object 4-byte vertex stream, discard if <= 0.882); the first frame uses the silhouette material with the opaque prepass (solid black), later frames the dithered one (opacity 0.6, 0.2...). Ruled out on the way: textures / mips (shader override), constants race (LARECOMP_SYNC_SUBMIT), vertex cache. Kept: vertex streams are now bound with their own size and VK_EXT_robustness2 robustBufferAccess2 (fetches past a stream read 0, as on Maxwell; captures unchanged). Note: debug-frame pass dumps (LARECOMP_DEBUG_FRAME=N) show the frame captured as XCDE_SHOTS N+1. Old text: (user report + 4-min video `<local file>`, ~19 one-frame events): when the camera gets very close, the game fades the character out with a per-pixel checkerboard (half the pixels show the background; the console's temporal resolve makes it see-through). Ours: the character's kept pixels have near-black albedo. Reproduced deterministically from the Colony 9 save: `tests/routes/load_walk.txt` (walk in circles, camera turning), frame 4317 (Shulk). Facts: G-buffer pass 134 (5 targets, fs 72c4c46000, no discard in it) - albedo of Shulk dark at 4317, coloured at 4300 (far); fs constants identical in both frames; textures fine; XCDE_TEX_EXACT changes nothing; the vertex cache is not the cause (same with it off and in deterministic mode). Next: where the checkerboard comes from (stencil? another program?) and what darkens the kept pixels (vertex shader 72c4c45900 varyings near the camera; compare v0..v6 at 4300 vs 4317).
  New tools: `XCDE_FLICKER_CHECK=<dir>` (in-game detector of one-frame dark flicker: logs `[flicker]`, saves the 3 frames, runs at game speed), `[draw]` log shows each colour target's view (levels / layers) and texture target/depth/layers, `XCDE_TRACE_CB=2` now dumps zero-padded fs constant buffers too.
- T154 check: the cube-array probe build renders levels 0-5 into layers 42-47 of a 192-layer cube array (views right, image has 192 layers): the layer hypothesis is ruled out.
- Note: the vertex cache matters for speed - off: CPU waits on the GPU 1161 vs 485 ms per 2 s in the field, fps under 30.
- [x] T136 (2026-10-19) **Black grass tufts flashing for a frame** (user report: title screen, Colony 9 field). Root cause: a GPU write-after-read race. The game animates grass in batches: a transform feedback capture refills one scratch buffer from offset 0, then ~20 draws read it as instance data, then the next batch's capture refills the same buffer with no barrier in between. Maxwell runs draws in order; Vulkan overlaps them inside a render pass, so the next capture overwrote data the previous batch was still reading - those tufts got another batch's positions, missed their depth prepass (EQUAL) and showed the cleared black. Timing dependent (moved between runs, even deterministic ones). Fix: a draw that writes memory (capture or shader stores) now starts a new pass, i.e. a full barrier before it as well as after (exec.c). Measured, 6 min real-time walk in the field (`tests/routes/load_walk.txt`, in-game detector `XCDE_FLICKER_CHECK`): small dark flashes 64 -> 11, all 11 reviewed by eye - no grass left (game silhouettes of the sword / shield near the camera, a tree trunk's shading, 3 detector false positives); passes +2 %; prologue captures pixel-identical. Also: transform feedback Pause/Resume keep their position per control buffer (NVN semantics; the game doesn't use them so far); DrawTransformFeedback logs once if ever called.
- [x] T174 (2026-10-19) **Draws dropped while their shader / pipeline compiled** (real time only): ~18,000 draws in 6 min of field play were skipped while their program or pipeline was being built on the workers - an object whose colour pass was skipped but whose depth prepass had drawn showed black for the frame (first time something appears: title grass at startup, new enemies and effects). Now the draw waits: a job still queued is taken out and run on the render thread, one already running is waited for (`wait_ready`). Skipped draws 7,191 -> 0; frame times median 33.2 ms both, p99 40.7 -> 45.7 ms (first-time builds; the disk pipeline cache makes repeats free; shader precompilation, T163, removes the rest). `LARECOMP_ASYNC_SKIP=1`: the old behaviour. The fps log line shows `build waits N (ms)`.
- Note (user question, 2026-10-19): the user's Switch reference video (the 2 h YouTube walkthrough in the user folder, 30 fps) checked with `tools/video_flicker.py`: 0.19 one-frame dark flashes per 1000 frames; the Switch shows the same character silhouette flash (normal -> solid black -> dither) when a character crosses between camera and target (e.g. at 4572 s, 5446 s, 6457 s).
- [ ] T175 (tried 2026-10-19, REVERTED) GPU-resident copies of GPU-only heap ranges (transform feedback / skinning-palette scratch in VRAM instead of imported host memory). Captures showed most field grass missing: the "saving" was grass not drawn. Measured on the way (real time, field frame, `LARECOMP_GPUPROF_AT` + new `XCDE_GPUPROF_VS=<vs,...>` per-draw timestamps): GPU 10.2 ms per frame, of which the grass prepass (vs 72c293c900, 16 draws of ~200 instances x 24 vertices, alpha-test discard) ~3 ms and the grass colour pass ~2.2 ms; each prepass draw 0.1-0.5 ms; independent of internal resolution in a first test (to recheck). Deterministic runs are not representative for GPU time: the vertex cache is off there (vertices read from host memory: 30 ms). `XCDE_TRACE_VC=1` lists the ranges the vertex cache refuses (GPU-written pages).
- [x] T163 (2026-10-19, first part) **Shader variant precompilation**: every pipeline built is recorded in `cache/variants.bin` (shader content hashes + translation keys + render state, no game data); when the game registers a program (nvnProgramSetShaders, usually on a loading screen) all its known variants are translated, compiled and built into pipelines on the workers ahead of the draws (`prewarm_drain` on the render thread; pipelines whose program isn't ready yet wait in a pending list pumped by draws and by `wait_ready`). Same field walk A/B in real time (warm SPIR-V / pipeline caches both): build waits up to frame 3000 (title + load) 7,916 -> 230 ms; in the field 519 -> 141 ms; worst 2 s window 303 -> 55 ms. Frames over 40 ms unchanged (13 / 14): other causes (T160). `XCDE_PREWARM=0`: off. Off in deterministic runs (synchronous shaders). The fps log shows `prewarm N progs M pipes`. To do: ship / build the variant list for areas the player hasn't visited (launcher precompile), cold-cache first run.

## Session 9 (2026-10-19) - user report from a real play session (launcher, 3840x2160 window, resolution "match", docked)
Screenshots: `<work dir>\user_reports\20261019_s9\` (1-15, numbered as the user sent them). The user played `build/xcde.exe` = 69b98ce
(the launcher starts that exe). The save is still the Colony 9 one (outskirts meadow). User: fix all of these after the
optimizations ("they have to be solved, no matter what").
- [x] T176 [M4] (fixed 2026-10-20, see the T176 root-cause entry below) **Blue cliffs / walls in shade** (= T154, more cases): rock walls and Mechon wreck surfaces navy blue in the
  outskirts (shots 6, 8, 9, 10, 14, 15), the tree / building in Colony 9 (shot 6). Switch: olive / grey.
- [ ] T177 [M4] **Ground blue/black with a hard vertical edge** in Colony 9 (shot 4: the road right of x~790 is navy, left
  of it normal, the edge is a straight screen-space vertical line). Likely the same lighting / probe input as T176, split by
  a tile or a screen-space buffer half written. Also shot 7: a hard-edged dark rectangle behind Shulk on the cliff.
- [ ] T178 [M4] **Thin vertical lines across the image** (shots 9 x~1075 and ~1440, 10 x~1330, 14 x~880): one-pixel columns
  over the whole height. Candidates: tile / column seams in a full-screen pass (upscale, SSAO, shadow resolve), a texel offset
  at 4K internal resolution, a target scaled by a non-integer factor.
- [ ] T179 [M4] **Dark splotches on the ground in Colony 9** (shot 5: black/blue "puddle" pattern along the road; shot 4 also).
  Possibly decals / wet-ground or shadow-map artefacts; compare with the Switch video in the Commercial District.
- [ ] T180 [M4] **"Transparent"/ghost thing** the user saw in some shots (1-3, 11 repeated: meadow under the tree; check by
  eye what is see-through - dithered fade, shadow seam at y~630, sword shadow). Ask with a crop if unclear.
- [ ] T181 [M5] **Save/load slot thumbnails empty** (shot 12, "Kolonie 9" boxes blank; also seen in T172). On Switch the
  slot shows an image of the location. Find which texture / capture the menu uses.
- [x] T181 (2026-10-20) **Save thumbnails: the saved image is fixed; the save / load list still shows the placeholder.**
  Cause (proved): when saving, the game draws a 320x180 RGBA8 target once (one quad, fs content hash b515bb7fd9974090,
  frame 2968 of `tests/routes/save_a.txt`) and then reads that texture's *guest storage* on the CPU (block-linear) to
  build the .tmb (320x180 RGB, no header). Our draws only reach the VkImage, so every .tmb was zeros (prefilling small
  textures' storage with a per-texture byte made the whole .tmb that byte). No CopyTextureToBuffer / ReadTexels /
  Invalidate* call is involved. Fix (exec.c `thumbnail_target` + `writeback_texture`): after that draw, wait for the
  GPU, read the image back at guest size (scaled targets are blitted down) and swizzle it into the guest storage; one
  stall per save, nothing else changes (load_walk captures vs the old exe: frame 1200 identical, 2600/3500 differ only
  in the top cliff band that differs run to run, T176 note). Verified: the saved .tmb is the field scene
  (<work dir>/visual/tmb_fixed.png). XCDE_THUMB_FS=<hash> overrides the program, XCDE_THUMB_LOG=<frame> lists the
  320x180 RGBA8 draws and their hashes.
  Still open: the list draws each slot (fs 93ee0aecfbae2ac9, reads the RGB from a storage buffer through gmem into
  the slot's 320x180 target) from two buffers alternating every frame; the game memcpys the loaded .tmb into only one
  of them (f_700057da00, once per slot), the other keeps a 243-grey placeholder, and the UI shows the placeholder in
  the captures (the slot target holds the image on alternate frames: <work dir>/visual/svd2). Next: find why the
  buffer index flips every frame here (frames-in-flight / sync emulation?) or why the second buffer is never filled.
  Ruled out (2026-10-21, party mod session): filling both buffers (each slot's pair: e.g. 7265ec8700 / 7265e9e300,
  172800 bytes in the fragment stage's storage buffer 0; the image was copied into the twin) AND writing the slot's
  320x180 target back to its guest storage after the draw - the list still shows the placeholder in every frame. So
  what the list displays is not that target / those buffers: find the texture the list's final draw samples.
  Done (2026-10-22, T181 fix, exec.c slot_thumb_fix): the earlier "ruled out" was wrong - it was tested in hidden
  deterministic runs, which present only the captured frames. The real cause has two parts (real time,
  XCDE_PRESENT_ALWAYS=1):
  - The vertex stage offsets the quad by two floats from its storage buffer 2. The game leaves that offset at
    (100000, 100000), which pushes the quad off screen.
  - The empty twin buffer holds a marker (16 bytes of 0xf3, then zeros).
  Fix:
  - Per slot (the n-th such draw of a frame), the two buffers are paired and the loaded picture is copied into the
    empty twin.
  - A slot whose picture is loaded gets the offset (0, 0).
  Verified: fallen_arm save copy, load list, all 4 slots show their image in consecutive frames (2200 / 2201).
  XCDE_SLOT_THUMB=0 turns it off.
- [x] T183 (2026-10-20) **Depth of field option.** The blur is the game's own: the user's Switch video shows the same
  soft distance (<work dir>/full f_00960.jpg). The game's DOF is a bokeh chain after the lighting (debug frame 3500 of
  load_walk, passes 253-259): CoC + half-res colour (fs hash 69b277b005fbc48a, 3 targets 640x360), 64x36 CoC tiles,
  one point sprite per tile (2304) splatted into a 640x360 buffer (f818597443f5fa73), then 2304 sprites composited
  over the lit scene (8cb02bca8ec7e152). Skipping the splat + composite removes it (frame 6000: the out-of-focus
  foreground grass becomes sharp; 11,000 pixels change, <work dir>/visual/dof/ini_6000.png). Launcher (Graphics tab,
  "Profundidad de campo", on by default) writes `depth_of_field = 0/1` to xcde.ini; settings_ini.c -> g_settings.dof_off;
  exec.c skips only those two programs. With the option on nothing changes (default run vs the old exe: differences
  only at noise level, the T176 run-to-run band). Not checked: other scenes may use other DOF programs (cutscenes).
- T178 note (2026-10-20): **not reproduced** in 5 configurations, deterministic and real time: 3840x2160 (scale 3),
  3712x2088 (2.9), 3840x2089 (fitted 16:9 box), the user's own xcde.ini (FSR, match), 3x into 3712x2088 through FSR,
  and a real-time 4K run (frames 3500 / 4300 / 4302 of load_walk). Detector: per band of rows, the column whose
  horizontal high-pass mean is most negative (only the HUD text and the pillarbox edges show). In the user's shot 9 the
  line crosses the lit grass and the shaded cliff but not the Mechon panel or the characters (a scene / lighting pass,
  not the upscale); shot 14 likewise on the cliff, not over Shulk. Next: a real-time run in the user's spot (shots 9-10:
  Mechon wreck by the outskirts cliff), several captures over time (it may be intermittent - a race in a half-res
  pass, e.g. the 640x360 f0x17 ping-pong blur 821ae0a7 / 851f7516 upsampled bilaterally by 9dff9c25).
- T180 note (2026-10-20): shots 1, 2, 3 and 11 are the same image (pixel-identical). Candidates, cropped in
  <work dir>/visual/t180_candidatos.png: (1) Shulk's sword looks flat / see-through, (2) a dark scalloped band along a
  ground step behind the grass right of the tree (y ~630 in shot 1; looks like the T179 dark splotches - shading /
  shadow, the lighting session's area), (3) grass blades over the tree trunk. Needs the user to say which one; not
  reproduced at that spot.
- [ ] T182 [M4] **Jagged, low-resolution party portraits** (shot 13: hair edges stair-stepped, faces soft) and blurry
  characters: check that the portrait render target is scaled with the internal resolution (or is a fixed-size target
  upscaled with nearest), and that "match" at 3840x2160 really renders the 3D at 4K (T175 found GPU time independent of
  internal resolution - recheck: log every render target size in the field at 4K).
- [x] T182 (2026-10-20) **Portraits: fixed. Soft field characters: not a scale bug.** The main menu's party portraits are 3D
  renders into 192x544 targets (colour 0x25, depth 0x35, G-buffer 0x3d / 0x3f, post chain at 96x272 and 48x136), drawn
  ~1:1 on the 1280x720 HUD. Our scalable-target rule (from LASRecomp) only covered 16:9 targets, so at 4K the portraits
  stayed 192x544 and were magnified 3x (the stair-stepped hair of shot 13; reproduced with `tests/routes/menu_x.txt`,
  X from the field). textures.c: targets of that shape (aspect 0.345-0.360, render-target flag) now scale with the
  output, uniformly (min of sx, sy) and without the 16:9 targets' per-frame clears (`scalable` 2). Verified at 4K: the
  portrait is rendered at 576x1632 (<work dir>/visual/mx/face2.png: before / after); 360k pixels change inside the two
  cards, 0 outside; at 720p the menu and the field are unchanged (menu: 67 pixels differ by 1 level in the blurred
  background; field 1200 / 2600 / 3500 as run-to-run). The game's own dynamic resolution: none seen - a real-time 4K run
  (debug frame 4300) draws every scene pass with a full 1280x720 viewport, so "match" at 3840x2160 renders the 3D at 4K.
  Distant characters look soft because of the game's depth of field (T183, now optional).
- [ ] T183 [M10] **Distant characters / scenery blurry** (shots 14, 15): likely the game's depth of field. Confirm with the
  Switch video; if it is the game's DOF, add a launcher option "Depth of field: on / off" (and maybe strength).
- [ ] T184 [M8] **Stutter in the field** (fps counter in the shots: 30 fps, 33-34 ms, frametime graph with spikes). First play
  of a new area compiles shaders (T163 part 2); also T160. Battle drops expected until the battle work is done.
- **Min-spec target (user, 2026-10-19):** the port must run on a Ryzen 3 3200G (4 cores / 4 threads) + Vega 8 iGPU (shared memory)
  + 8 GB RAM at 720p (FSR; DLSS is NVIDIA-only). Optimize only our overhead (generated code, emulation-style copies, compile
  stutter, memory); never lower the game's own features. Every perf change is judged on that machine's budget: 4 threads
  (shader workers currently = cores - 4, floor 4 -> 4 workers on 4 threads), ~4 GB process RAM today, VC_BUDGET 768 MB
  device-local (= system RAM on an iGPU). To do: a low-spec test mode on the dev PC (affinity to 4 logical CPUs, RAM cap,
  `LARECOMP_SCALE` 720p) to measure against that budget.
- [~] T187 (2026-10-20) **Shader precompilation from the RomFS** (T163 part 2): `xcde.exe --precompile targets` (runtime/nvn/vulkan/precompile.c; launcher button "Precompilar shaders" with a progress bar, and JUGAR runs it the first time, "Omitir" skips) scans the game's SPCH shader containers (.wishp/.wimdo/.wismt/.wismda/.wiefb, xbc1 zlib blocks unpacked): 8,124 files, 11,649 distinct shaders, 9,823 VS+FS programs; 593 of 595 shaders and 421 of 422 programs the game drew in a cold title+field run are among them. Each program is built as its first draw would (exec.c `vk_precompile_program`: translate, SPIR-V into cache/spirv, GPL vertex + fragment libraries into the driver's own cache; NOT into cache/vk_pipelines.bin - that file grew to 698 MB, read whole into RAM at start). 188 s with 6 threads on the dev PC (scan 42 s); disk: spirv 952 MB + driver cache 668 MB. Truly cold A/B (empty cache/ and empty driver cache via `__GL_SHADER_DISK_CACHE_PATH`, load_walk real time, scripts/rt_run.sh + rt_summary.py, busy PC): title+load build waits 23.9 / 23.5 s -> 11.3 s, field 2.0 / 1.3 s -> 0.7 s; a later precompiled run on a quieter PC: title+load 4.4 s, field 0.26 s, frames over 40 ms 15 + 21. Translation keys are guesses (depth_minus_one, float inputs + location 1 uint variant, float targets): a wrong guess only misses. Game output unchanged by construction (same GLSL -> same SPIR-V; only cache contents differ) - deterministic captures with/without the caches NOT yet compared. Still to do: that capture check; profile the remaining title waits (sampler output in <work dir>\precompile
unB3s\samples.txt - suspected single translator thread: a translation cache would remove it); 36 shaders fail to translate (unknown instructions ea000486c0070202 FS, 50d8e38000070003 VS); 2 shaders not in containers (maybe exefs); measure on a 4-thread PC; cap concurrent background (T188 optimize) jobs - written and dropped untested.
- [ ] T185 [M8] **No leaks over long sessions** (user requirement): soak run (1-2 h real time, field walk + scene changes) logging
  process private bytes, VRAM (VMA budget / heap usage), handle count and descriptor pools every minute; must stay flat.
  Seen 2026-10-19: each run grows 4.3 -> 4.5 GB in ~6 min of field walk.
  - **Soak 1 (2026-10-20, build of 7b275cc, scripts/soak.sh + tools/gen_soak_route.py: load the save, circles / run out / fight / run back, real time, LARECOMP_VK_PROF=1; data <work dir>\precompile\soak1, tools/soak_report.py):** the game FROZE at ~69 min (frame 89,121): the render thread spun forever in exec.c get_program - prog_tab (4096) and pipe_tab (8192) were fixed open-addressing tables whose probe loop never ends once full. They filled because entries are never removed and the program key mixed in the guest code address: the same shaders streamed in at new addresses became new programs (~10,100 program builds by 69 min, the rate rising). Before the freeze: private memory 6.2 GB at 10 min -> 7.3 GB at 69 min (+0.8 GB/h), GPU heap flat after 20 min (2,029 MB, ours ~1,670), handles 2,060 -> 2,099, threads flat (~94). Fix: growable tables (htab_slot, log line on growth) and the program key by content only (T125 hashes; translation reads only code + key). Deterministic captures before/after: identical at 1200 / 2600, 3500 within the known rock-edge noise (896 faint pixels).
- [x] T186 (2026-10-19, removed) [M8] **Per-draw logic left over from the Link's Awakening recomp** (LASRecomp) in `exec.c draw_`: mirror mode,
  pot tint / glow, escape bottle, hearts, pets item cursor, bushsanity instance runs, widescreen backdrop hash and scene
  UBO scan, LARECOMP_SKIP_FSHASH - run on every one of ~4,000 draws a frame in XCDE. Remove or gate behind a once-per-
  program flag.
- [x] T164 part 1 (2026-10-19) **GPU deswizzle**: block-linear -> linear for 4/8/16-byte-per-block formats (BC, RGBA8, ...)
  now runs as a compute shader in the upload command buffer (textures.c `dz_level`): the CPU only memcpys the level's
  swizzled bytes into the ring. Measured before (real time, field walk, `XCDE_PROF_UPLOAD=1`): 26 levels over 2 ms in
  6 min, 5-11 ms each on the render thread (1024x1024 RGBA8 4 MB: 6.4 ms, BC 2048x2048: 5-7 ms). Verified:
  `XCDE_DZ_CHECK=1` (GPU result compared byte for byte with the CPU deswizzle once the GPU ran): 3001 levels, 0 bytes
  differ; deterministic captures from the save (frames 1200, 2600 identical; 3500/4300/6000 differ only at the blue
  cliff edges, by as much as the OLD exe differs from itself run to run - see T176 note). `LARECOMP_GPU_DESWIZZLE=0`: CPU.
  Still on the CPU: linear textures, RGB8 expansion, ASTC (decode), texpatch textures, levels under 16 KB.
- T176 note (2026-10-19): the blue cliff region is NOT deterministic: two runs of the same exe (deterministic mode, load_walk
  from the save) differ in 1,200-19,000 pixels along the cliff silhouettes in the top of the frame (frames 3500/4300/6000).
- [~] T160 (2026-10-19) shader workers at THREAD_PRIORITY_BELOW_NORMAL (`plat_thread_background`; `LARECOMP_WORKER_PRIO=0`:
  normal): in the field, bursts of prewarm builds (hundreds of variants when the game registers programs while walking)
  ran on 12 normal-priority workers and the render thread's exec went from ~11 to ~29 ms per frame (4K run, hitch log:
  "compiles 228-837 pending"). A/B at 720p was not clean (one run overlapped other runs): >50 ms frames 22 -> 11,
  p99.9 56.7 -> 47.1 ms, p99 37.0 -> 38.0 ms. Re-measure with the low-spec mode (4 logical CPUs).
- Measured 2026-10-19 (real time, field walk, 720p): 81 % of draws use the previous draw's program, 78 % its pipeline
  (`same prog / pipe` in the VK_PROF line). Render thread in the field: ~8-13 ms of CPU per frame for ~4,000 draws
  (key 2.1, sets 2.7, pre 2.4, tex 1.8 ms) - the main CPU cost for a 4-thread PC together with the guest game thread
  (~11 ms per frame, T165; its hottest functions are the SDK mutex lock / unlock, f_70040d58c0 / f_70040d59b0).
- Profiler caveat (T112): ~41 % of samples land on kernel wait return addresses (ZwWaitForMultipleObjects): a thread
  that ran during a tick and then blocked has the tick's cycles charged to the wait. Read per-thread totals, not those rows.
- Tried 2026-10-19, NOT kept (measured):
  - Descriptor set reuse within a submission (same layout + contents -> same set): 26 % of sets reused in the field, render
    thread time unchanged (sets 121 vs 113 ms per 2 s, noise): hashing costs what the driver calls cost.
  - T165 registers as C locals (each guest register a local, stored / reloaded around calls that take the Cpu): x86-64 has
    ~14 usable GPRs against AArch64's 31, so functions with 20+ live guest registers spill them to the host stack anyway,
    and the copies at every call made it worse (main_151: +5.6 % instructions, +9 % memory operands). Dropped.
- T165 variant in test: `Cpu *restrict c` on generated functions (memops -3 %) and generated code built for x86-64-v3
  (AVX2 + FMA: the Ryzen 3 3200G has them): -9 % instructions in main_151, and the 1,545 software `fmaf` calls there
  (4 per vector FMA, from -march=x86_64_v2) become 425 vfmadd. FMA in hardware rounds exactly like fmaf. Differential
  tests: `XCDE_TEST_MARCH=x86_64_v3 XCDE_TEST_RESTRICT=1 tools/lifter/test_lift.py ...` (new switches).
  - T182 lead (AC-Recomp): Astral Chain's internal resolution and its dynamic resolution are immediates in the game code;
    check XCDE's own DRS (it may drop the 3D target when our reported GPU times look slow) and every scene target's size
    at 4K. 60 fps model: a second lifted binary from a patched copy of main, chosen by the launcher.
- From the other repos' updates (2026-10-19, `docs/lessons_astral_ssbu.md` last section):
  - [x] Lazy-commit race (upstream LASRecomp 2332e74): ported to runtime/platform/windows.c.
  - [ ] T190 [M8] **Slow-QPC PCs** (HPET timing): ~1 us per QueryPerformanceCounter; fall back to the invariant TSC when a
    read is over 250 ns (WindowSmash 5004359). Measure our reads per frame (rt_ticks in the limiter, plat_now_ns, SDL ticks).
  - [ ] T191 [M7] **Driver threads' stacks**: NVIDIA's compiler threads start with 64 KB and can overflow on deep shaders
    (silent crash). Give DriverStore DLLs' threads big stacks; crash report from its own thread.
  - [ ] T192 [M10] FSR 3.1 (temporal) upscaler option, if XCDE has depth + motion vectors (TAA) to feed it.
  - [~] T193 [M8] Port LASRecomp's integrated-GPU path (8a66a61, 03ee802): no per-frame target clears, lean image usage,
    SMAA stencil - on by default on iGPUs. Needs an iGPU to measure (the dev PC's Ryzen iGPU is disabled in the BIOS).
    2026-10-23 (docs/spec_lowend_gpu.md R6):
    - lean image formats: done, fde082c, on for non-NVIDIA;
    - per-frame clears off: rejected, the frames differ;
    - SMAA stencil: open.
  - [x] T194 [M7] (2026-10-22: exports in host/main_boot.c; device.c already prefers the discrete GPU) Laptops: export NvOptimusEnablement / AmdPowerXpressRequestHighPerformance and pick the
    high-performance adapter; launcher option for the GPU.
  - [x] T195 [M8] Canonical pipeline keys (normalize state Vulkan ignores before hashing; verify mode comparing merged keys).
    Done 2026-10-22 (exec.c pipe_key_canon, XCDE_CANON=0: off).
    - Normalized: blend on unwritten targets, the advanced-mode byte, and the alpha / RGB factors of unwritten channels.
    - load_walk (colony9 save): 1130 -> 1122 pipelines. Captures 1200 / 2600 identical; 3500 differs only in the top
      band, which also differs between two runs with it off.
    - Key-space measured on the same run:
      - with blend / write mask / a2c / logic op / fill mode dynamic (extended dynamic state 3): 1111;
      - with the vertex input dynamic as well: 1013.
      XCDE's pipelines are ~1 per program + targets, so EDS3 / vertex-input dynamic state are not worth it here.
    - Push descriptors also set aside: descriptor sets are ~150 of 700 ms of render-thread time per 2 s (720p, 4 cores,
      unlimited fps). Only one push set per pipeline layout (we use 2-3), and the change invalidates every pipeline
      cache / library.
  - [ ] T196 [M7] **AMD checklist** (B2recomp fixes; the min-spec GPU is an AMD Vega 8): clear-before-upload ordering on new
    textures, no shader reading a constant buffer missing from its layout, present-mode fallback to FIFO, a refused
    pipeline never fatal, DPI awareness. Test with the AMD validation path when an AMD GPU is available.
- Idea (user, 2026-10-19, not planned): **switch the controlled party member in battle** (as in Xenoblade 3), an optional
  launcher mod, off by default. Needs reverse engineering of the battle's player / AI controller assignment, camera
  target, Battle Palette / HUD, aggro; hooks as in T157. Estimate: prototype days, polished weeks. After optimization + bugs.
- [x] T165 part 1 (2026-10-19) **`Cpu *restrict c` on every lifted function** (tools/lifter/gen.py): the compiler keeps
  guest registers / flags in host registers across guest loads and stores (it reloaded them after every store through
  the may_alias pointers). Measured in the low-spec mode (XCDE_LOWSPEC_CPUS=4, real time, field walk frames 3000-10000,
  two series in opposite orders): process 0.96 -> 0.835 cores (-13 %), the game's worker threads t118/t119
  0.095 -> 0.06 cores each (-37 %), main game thread 0.29 -> 0.28, render thread 0.35 -> 0.305. x86-64-v3 (AVX2 + FMA)
  on top was WORSE than restrict alone in both series (0.91 cores) - not used (and the target's Zen+ splits 256-bit ops).
  Verified: differential test 30,000 encodings (89,961 cases) with restrict (+ v3: 0 failing; v2 run below), captures
  from the save identical at 1200 / 2600 and within the cliff-edge run-to-run noise at 3500 / 4300 / 6000.
- [~] T188 (2026-10-19) **graphics pipeline libraries** (exec.c gpl_*): whole pipeline from the disk cache when it is there
  (FAIL_ON_PIPELINE_COMPILE_REQUIRED), else a fast link of four cached pieces and the optimized pipeline built on a
  low-priority queue and swapped in. Cold caches (empty cache/ folder), field: build waits 1,642 -> 1,453 ms, frames over
  40 ms 68 -> 51; title screen unchanged (5.2 s of waits: shader translation + SPIR-V compile dominate there, T187).
  NVIDIA's own driver cache answers most whole pipelines even with our cache empty ("gpl cached"). Deterministic
  captures with linked pipelines (XCDE_GPL_DET=1): identical at 1200 / 2600, noise elsewhere. LARECOMP_VK_GPL=0: off.
- [x] T190 (2026-10-19) TSC clock fallback when a QPC read is over 250 ns (platform/windows.c clock_pick; XCDE_CLOCK=qpc|tsc).
  This PC: QPC 16 ns (QPC kept). Forced TSC: 200 s field run at 30.1 fps, frame period median 33.24 ms, p99 36.1 ms.
- [x] T169 part 1 (2026-10-19) **memory report** (`[mem]` every ~10 s with LARECOMP_VK_PROF=1: private bytes, working set,
  guest committed, GPU heaps, vertex cache, ring). Field walk 7 min, 720p: guest heap 3,220 MB (all committed), working
  set 3.7 -> 4.4 GB, private 4.3 -> 6.2 GB and still growing slowly; GPU heap 1.56 GB of which the vertex cache 768 MB
  (at its budget). Without the vertex cache: private flat at 5.6 GB, GPU heap 1.0 GB - but GPU busy 9.8 ms a frame
  instead of 4.0 on the RTX GPU (vertex fetches over PCIe). So: **vertex cache off by default on integrated GPUs**
  (same RAM, no PCIe: it only cost memory), kept on discrete GPUs. Still to explain: the slow private growth with the
  cache on (T185 soak), and the ~1 GB of private bytes beyond guest + GPU.
- [x] Maxwell translator: FLO .SH / .INV and BFE.BREV implemented (from EoWRecomp's notes); scripts/native_tests.sh links
  the sampler (test_condvar had failed to link since T112). All native tests pass.
- GPU profile 2026-10-19 (field frame 4000, RTX GPU): GPU busy 3.4 ms a frame at 720p, 4.6 ms at 4K. The grass passes
  (32 draws each) take ~2.1-2.3 ms at both resolutions: not fill-bound but instance data read over PCIe (GPU-written
  transform-feedback scratch the vertex cache can't hold). Discrete GPUs only; T175 to redo correctly later.
- T169 part 2 (2026-10-19) `XCDE_MEM_MAP=1` (with VK_PROF): committed private memory outside the guest window by allocation.
  Field, RTX GPU: 2.7 GB in ~400 allocations - one 778 MB block (the vertex cache's device memory, mirrored in system
  commit by the NVIDIA driver), the two 64 MB ring chunks, many 32 MB blocks (GPU memory for textures / targets), only
  ~50 MB in small heap regions. Flat after warm-up (6,135 MB private over the last 3 reports): no leak in 5.5 min.
  Estimate for the 8 GB iGPU target (vertex cache off): ~4.3 GB the game touches + ~0.5 GB textures/targets at 720p.
- [x] Battle measured (2026-10-19, handoff step 2): `tests/routes/battle_b.txt` (load the save, L = target nearest every
  15 s, A every 3 s) fights a Little Bunnit and a Little Skeeter in the outskirts, frames ~3000-5400 (no enemies near
  after that). Real time, low-spec mode (4 cores), 720p, final exe of this session: 29.9 fps average over the battle,
  render thread ~10 ms a frame (twice the field's), whole run 0.82 cores busy, frames over 40 ms: 18 in 6 min. The
  ~165 ms hitches every 600 frames were the run's own window captures (XCDE_SHOT_EVERY, "present 132 ms"); the others
  (51-89 ms) all had shader builds pending (first-time battle effects: T187). Bigger battles (Mechon, 3 party members)
  still to measure - needs a later save.
- Tried 2026-10-19, NOT kept: descriptor update templates in stage_set (one vkUpdateDescriptorSetWithTemplate per set).
  Battle, low-spec mode, A B B A: driver share of the render thread 15.4 -> 13.9 %, render thread 0.40 -> 0.41 cores
  (no gain: the packing costs what the driver saves).
- [~] T162 part 1 (2026-10-19) **tracked barriers between render passes** (exec.c pass_barrier): measured first that
  skipping every pass-start full barrier (test build only) cut GPU busy 7.4 -> 4.8 ms a frame (-35 %). Now a pass
  directly following another gets a full barrier only when needed (anything untracked since the last one, a draw
  sampling an image written since the last full barrier, an attachment sampled since then), an attachment-only
  barrier when it reuses an attachment written since the last barrier, else none. Field (2 s windows): full ~12,000
  (ended by something else ~10,000, sampling hazard ~1,300, dirty ~650, write-after-read ~120), attachment-only
  ~5,700, none ~3,100. GPU busy 7.38 -> 6.82 ms a frame (parallel A/B, -8 %). Verified: deterministic captures
  identical at 1200 / 2600, cliff noise elsewhere; flicker detector 39 (full barriers) vs 37 events, all the game's own
  near-camera silhouette (T173); sync validation over the title screen: 0 messages (layer too slow for the field).
  LARECOMP_VK_PASS_BARRIER=full: as before. **Next:** the "ended" passes (~80 % of the remaining full barriers): passes
  ended by memory-writing draws (grass / skinning writers), the game's own barrier commands, copies, clears - narrow
  those to the stages and resources they need.
- [~] T162 part 2 (2026-10-20) **guest-memory barriers instead of full ones** (exec.c mem_barrier, pass_untracked, mem_rd /
  mem_wr / pre_wr). Counted first (the pass-end counter skipped lines over 4096: fixed): per field frame ~54 passes ended
  by memory-writing draws (grass transform feedback, skinning-palette writers) and ~77 by the game's own barrier
  (CMD_BARRIER), each followed by a full barrier, plus a full barrier before every memory-writing draw (T136). Now those
  passes count as tracked: the barrier covers the stages that wrote guest memory since the last barrier -> every reading
  stage, the stages that read it -> a memory-writing draw starting next (write after read), plus attachments as before;
  sampling hazards still get a full barrier, and anything else that ends a pass (copies, clears, dispatches, submissions,
  draws using storage images) too. Field, 2 s windows: full barriers ~170 -> ~64 a frame (left: sampling hazard ~53,
  dirty ~7, write after read ~3), memory barriers ~85, attachment ~93, none ~49. Verified: deterministic captures from
  the save identical at 1200 / 2600, cliff noise only at 3500 / 4300 / 6000 (same as part 1 vs itself); new_game_h
  cutscenes (skinning, T133) identical at 6000 / 9600 / 11400 / 12000 vs HEAD. A first build missed draws with storage
  images (2600 differed in blocks): those now force full barriers around their pass. `XCDE_MEM_BARRIER=<bits>` (1 writer
  ends, 2 game barriers, 4 narrow pre-writer; 0 = part 1) to bisect. **GPU time not measured yet**: the PC ran 4 other
  game processes (parallel sessions) and GPU busy per frame swung 4-125 ms; redo the A/B on a quiet PC.
- [x] Render thread per draw (2026-10-20, exec.c / textures.c): `stage_set` zero-filled and filled the 1 KB resolution-
  scale table for every set (2-3 a draw) even when the shader has no binding 18 -> only for that binding; `get_program`
  hashed both shader keys byte by byte on every draw -> a last-call memo (81 % of draws repeat the previous program
  with the same keys; cleared on reset); `fmt_of` memoized. Tried and dropped: comparing the pipeline key with the
  previous draw's before hashing (key time went up). A/B in parallel (real time, field walk, VK_PROF, last 60 s): draw
  14,041 -> 10,753 ms-sum (-23 %), sets 4,333 -> 2,646, pre 3,100 -> 2,496, exec 8.23 -> 7.27 ms a frame (-12 %).
  Verified: new_game_h 6000 / 9600 / 11400 / 12000 identical; load_walk 1200 identical, others within the
  top-of-frame noise (2600: 721 px of sky seen through the tree's leaves, the same region where an earlier T162 build
  also differed by run; the command stream is unchanged by these edits).
- [x] **60 fps option (experimental)** (2026-10-20): the limiter f_70005bcfe0 waits interval x (frame period constant
  at 0x70009d3dcc, 0.997) where interval is the int behind the pointer at 0x7000b92ea0 (2 = 30 fps). Storing 1 there
  every frame (runtime/hle/framepace.c fps_interval_force) runs the game at 59.9 fps steady (field, real time, max
  frame 18 ms on the RTX GPU). World speed is dt-based: deterministic runs from the save, 30 fps vs 60 fps with the
  route's frame numbers doubled after the switch - same in-game clock at equal times (9:44 / 10:11 in both), party at
  the same places; idle animations normal. Seen: the camera sits a little farther back at 60 (its follow smoothing is
  probably per frame). Not tested yet: battle, cutscenes, menus at 60. Launcher: "60 FPS (experimental)" (Graphics,
  Velocidad) -> xcde.ini `fps = 60`. Test switches: XCDE_FPS_INTERVAL=<n>, XCDE_FPS_AFTER_S / XCDE_FPS_AFTER_FRAMES.
- T192 / DLSS feasibility (2026-10-20, user asked for DLSS 4 and FSR 3): both need per-pixel motion vectors, depth
  and jittered rendering. Field frame 3000 inventory (LARECOMP_DEBUG_FRAME, all render targets of the frame): G-buffer
  1280x720 RGBA8, RGBA8, RGB10A2, RGB10A2, RGBA8 (+ RGBA8, R11G11B10 x2 in the 8-target pass), D24S8 depth; post chain =
  bloom downsamples (320x180 .. 20x12), a 256x144 / 640x360 step, then one full-res composite (fs 72c28b6f00, DOF) and
  the UI. **No velocity target and no temporal AA pass with a history buffer**: the game has no motion vectors to hand
  over. Options: (a) camera-only motion vectors computed from depth + this / last frame's view-projection matrices
  (find them in the G-buffer pass cbufs); characters and grass that move on their own would ghost; (b) FSR 1 (already
  in) / a spatial upscaler. Both SDKs (NVIDIA DLSS / Streamline, AMD FidelityFX) are downloads that need the user's OK
  (standing rule). Not started.
- [x] T162 part 3 (2026-10-20) **graphics-only barriers for sampling hazards / write after read** (exec.c gfx_barrier):
  when nothing untracked happened since the last full barrier, an image written as an attachment and sampled now (or
  sampled and now written) gets attachment output + shader stages (+ guest memory) instead of all commands. Field,
  2 s windows: full barriers ~72 -> ~19 a frame (left: storage-image draws ~18, `dirty`), graphics ~53. Verified:
  load_walk captures 1200 identical, the rest within the top-of-frame noise; new_game_h identical at 6000 / 9600 /
  11400 / 12000. `XCDE_GFX_BARRIER=0`: full ones there. **GPU, parallel A/B on a quieter PC (one other game running),
  real time, field walk, 300 s:** part 2 alone vs part 2 + 3: 7.51 -> 7.34 ms a frame (median 7.33 -> 7.08);
  part 1 (`XCDE_MEM_BARRIER=0 XCDE_GFX_BARRIER=0`) vs parts 2 + 3: **7.00 -> 6.54 ms a frame (-6.6 %, median 6.53 ->
  6.00, -8 %)**. That is also the missing GPU measurement of part 2.
  - 60 fps checks (2026-10-20): in-engine cutscenes (new_game_h with every frame number doubled, deterministic):
    the 60 fps frames match the 30 fps timeline with a constant offset (B 12000 ~ A 6200, B 24000 ~ A 12200, image
    distance 6-7 vs 12-20 for neighbours) - same playback speed, the offset comes from the title / loading phase. Battle
    in real time at 60 (battle_b): fights normally, HUD fine; 41-48 fps there with two other game processes running.
- [x] T162 part 4 (2026-10-20) storage images (SULD / SUST in draws) tracked like attachments (read + written at
  their draw) instead of forcing full barriers around their pass: field full barriers ~19 -> 1 a frame (the
  submission start), passes +0.5 %. Captures: load_walk 1200 / 2600 identical (rest: top-of-frame noise),
  new_game_h identical. GPU A/B not measured yet. `XCDE_SIMG_FULL=1`: as before.
- [~] T176/T177/T179 (2026-10-20, lighting session, part 1) **Probe lighting: NVN logic ops were never applied.** The probe-lighting index map (640x360 RG32UI, `725c620000`) is built by per-probe box draws (fs 72c2d2e100 / 72c2d2d600 / 72c2d3e700) plus a full-screen fallback (fs 72c2d14e00, probe 0 = global sky probe): each picks a free byte slot from a per-pixel bitmask image (imageLoad/Store, popcount) and writes `index << slot*8`, `weight << slot*8` with **ColorState logic op OR (7)**. `nvnColorStateSetLogicOp` was stored but no pipeline used it, so each draw replaced the map: measured at frame 4300 (shader override showing slots), every pixel held only probe 0 (the blue sky probe) in one slot. Fix: logic op in the pipeline key (tail padding: `cache/variants.bin` records keep their size) and in both pipeline paths (monolithic + GPL fragment-output library), device feature `logicOp`; `[draw]` log prints `logicop N`. After: pixels hold probe 2 + probe 0 (2 slots), box edges visible in the map. Captures (load_walk from the save): frame 1200 identical, field frames 2600-6000 change slightly (lighting only) - **the navy cliff is still there**, so this is necessary but not the whole fix.
  Proven on the way (shader overrides in <work dir>\lighting\ov*): (1) zeroing the probe pass output (fs 72c2d52000, c0/c1) removes all navy -> the blue comes from this pass; (2) replacing all 9 cube-array samples with constant grey keeps the navy -> it is NOT the cube array contents (also: a per-face vertical flip of the lookups changed nothing); (3) the diffuse term is per-probe 4x4 irradiance matrices in cb6 (192 B per probe, R/G/B; n^T M n): probe 0 DC 0.25/0.24/0.30 (bluish sky), probe 2 0.29/0.29/0.23 (warm). The fallback writes weight 255 for probe 0 in the next free slot. Next: dump the weight bytes per pixel (c1 = pw.y bytes) and compare probe 0 vs probe 2 weights in the blue region; check how fs 72c2d52000 normalises the 4 weights (and whether the 8-bit weights from the box draws, `saturate(..)*255` truncated, are right), and whether the irradiance evaluation uses the normal with the same y sign as the cube lookup (`r2 * -r9`). Also ruled out: the LAS per-frame clear of 16:9 targets (`LARECOMP_NO_FRAME_CLEAR=1`: field frames identical). Not yet run: scripts/native_tests.sh.
- [x] T176 (2026-10-20) **ROOT CAUSE of the navy cliffs: LDC immediate offsets are signed.** The probe-lighting shader (fs 72c2d52000) evaluates each probe's irradiance as three 4x4 matrices (R, G, B; 192 bytes per probe in cb6) and reads R and G at `c[6][Ra - 128]` / `c[6][Ra - 64]` relative to the B matrix. The translator decoded the 16-bit LDC immediate as unsigned (+65408 / +65472): R and G came from past the end of the buffer (clamped), only B was right, so shaded surfaces lit by probes turned navy. Found by elimination with shader overrides at frame 4300 (load_walk from the save): zeroing the pass output removes the blue; constant-grey cube samples keep it; probe 2 has weight 255 there and its matrices give warm light, so the inputs were right and the read was wrong. Fix (`translate.c`): sign-extend the immediate when a register is added (static RZ offsets unchanged), emit `(Ra) - N`. Test: `tests/native/test_translate_ldc.c` (c[6][R59 - 0x80]). Measured: deterministic captures from the save, frame 1200 pixel-identical; field frames 2600-6000: the cliff tops / Mechon wreck surfaces go from navy to olive / grey-brown in shade, as in the Switch video (outskirts, ~650 s); the rest of the frame changes only by lighting (the old ambient had no red / green). Together with the logic-op fix above (probe slots now merge). `scripts/native_tests.sh` passes.
  T177 / T179 (Colony 9 town: navy road with a hard screen-space edge, dark rectangle behind Shulk, dark blue splotches on the road) are most likely the same two bugs - the hard straight edges are probe box volumes (seen in the index map) and the navy is this probe ambient - but they are NOT verified in game yet: the test save starts in the outskirts and no route reaches the Commercial District. To verify: a route from the save into Colony 9 (or the user's next play session).
- [x] T180 = T177 dark rectangles (2026-10-20, session 12) **ROOT CAUSE: image stores ran with late depth / stencil
  tests.** The probe-lighting box draws (two-pass stencil: marking fs 72c2cd1d00, then the probe's fs 72c2d2d600 /
  72c2d2e100 / ...) each set their bit in a per-pixel "slots used" R32UI image (`725c800000`, cleared every frame - checked:
  the clear and the storage view are the same VkImage) and OR their index into the map only if the bit was not set.
  A fragment shader with side effects runs before the tests in Vulkan, so every pixel a box covered got the bit even
  where the stencil then dropped the colour; later probes sharing the bit (the global probe, fs 72c2d14e00) skipped
  those pixels -> index map 0 -> black boxes (pass 267). Fix (translate.c): `layout(early_fragment_tests) in;` for
  fragment shaders with SUST and no discard / depth output (only the probe family uses SUST in fragment shaders);
  `XCDE_EARLY_FS=0` = old behaviour. Verified: user save, load_a frame 3000 (cave at night) boxes gone; load_walk from
  the Colony 9 save 3000 identical, 6000 / 9000 / 12000 <= 15 px differ by > 8 (noise level). Colony 9 town
  (T177 road edge / T179) still to check in a user session.
- [~] T178 (2026-10-20, session 12) **thin vertical line: most likely the T180 probe bug (fixed in cebd044).** User's 4K
  shot (<work dir>\user_reports\20261020_s12\t178_line.png): a soft ~3-5 px dark column over cliff and grass, hidden by
  Shulk - a scene-lighting buffer, not the upscale; the 640x360 probe index map is 6x upscaled at 4K, so one zeroed texel
  column = that width, and characters do not use the probe map. 4K deterministic load_walk from the user's save
  (display lines of xcde.ini only): the old exe (XCDE_EARLY_FS=0) shows probe boxes with hard vertical edges at frame
  6000 (Cliff Lake), the new exe none; the exact one-column line was not reproduced. To confirm: user plays at the spot.
  Pitfall: routes do not work with `fps = 60` in the ini (menu timing: the load dialog ends on "Nein").
- [x] T192 (2026-10-20) **SULD / SUST on non-32-bit-per-channel textures read 0 / dropped stores** (Colony 9 gate ramp
  black, day and night; user shot 20261020_s12/shot5). fs 72d95acc00 reads the RGB10A2 normal buffer it blends into
  with a raw SULD; `storage_uint_format` only knew 32-bit-channel formats and the image had no STORAGE usage, so the
  dummy storage view was bound. Now: raw views by texel size (8 .. 128 bits) and a texture first used through
  SULD / SUST gets storage usage (`vk_tex_add_storage`: re-created, contents copied, remembered for re-creations;
  EXTENDED_USAGE when the format itself can't be a storage image). Storage stays off for other render targets up front
  (it can cost colour compression, e.g. DCC on Vega = the min-spec GPU). Verified: change_time route at the gate,
  frame 3700: ramp lit (was black); load_walk 3000 identical, 6000 / 9000 differ by 55 / 1,768 edge pixels (the meadow
  also re-creates the normal buffer with storage); ghost repro (T180) clean; native tests pass. Also committed: T191
  NVN alpha test (shader variant; the game never sets it so far, `XCDE_ALPHA_TEST=0` = ignored), route
  tests/routes/change_time.txt.
- [x] T178 (2026-10-20) **thin dark vertical line at 4K: fixed.** Reproduced from the user's meadow save with Reyn
  (<work dir>\saves\user_reyn_meadow: only bfsgame00 of 10:43) at 3840x2160 "match": a dark column at x = 2047-2050.
  Traced pass by pass: it starts in the probe lighting at 1920x1080 (the 640x360 probe buffers at 3x) at x = 1023-1025
  = guest column 341, where the probe index map was empty. The probe shaders address the 3x-allocated "slots used"
  storage image (T180) with guest coordinates (gl_FragCoord / scale, truncated): the 3 x 3 pixels of a guest pixel
  shared one texel, raced on it, and the losing pixels dropped their probe; the lighting reads the block's centre pixel,
  and at x = 1024 (a raster tile edge) the centre always lost. Fix (translate.c img_coord / isc, exec.c storage scale in
  the rscale table): in fragment shaders, a SULD / SUST at the fragment's own guest pixel goes to its own scaled pixel;
  other coordinates map to the scaled texel's centre (as texelFetch). Verified: 4K column darkness 30 -> none (by eye
  too); 720p load_walk 3000 identical, 6000 / 9000 edge noise only; ghost repro clean; native tests pass.
- [x] Graphics bug-class audit (2026-10-20, user request: find the remaining bugs before the player does). Classes
  behind the session 4-12 graphics bugs: NVN state stored but not applied (barrier, transform feedback, rasterizer
  discard, occlusion counters, logic op), translator precision / sign (LDC offsets), storage-image paths (late stencil
  T180, dummy raw views T192, unscaled coordinates T178), texture layout (block height). Checks done:
  1. NVN call census (XCDE_USAGE) over new_game_h to 19000 (title, intro, cutscenes, battle tutorial), battle_b from
     the Colony 9 save and change_time at the Colony 9 gate: of our ~80 no-op entry points the game calls only
     AddControlMemory, SetShaderScratchMemory, SetTiledCacheAction / TileSize (no effect on output); of the stubs
     returning constants only GetControlMemoryUsed / RegisterFastClear* / QueueInitialize (fine).
  2. New `[audit]` log (exec.c audit(): once per distinct message): dummy texture / storage views with a real texture
     bound, SULD/SUST formatted mode on non-integer images, advanced blend, raster samples, coverage to color /
     modulation, point polygon mode, point/line polygon offset. Same three routes: no [audit] line; the only
     unimplemented command is LINE_WIDTH. Translation failures were already logged: none.
  3. Translator sign class: LDG/STG/LDL/STL immediates already sign-extended (sbits); LDC fixed in T176.
  4. Scaling class: 4K vs 720p (downscaled) captures of the gate, the meadow walk and a battle: same images (mean
     diff 3-6, max 32x32 block 16-31 = finer detail / moving enemy). Per-pixel texelFetch at >1x (XCDE_RSC_PIXEL=1,
     rscf) measured: no sharpness change at 4K - off by default.
  Not covered yet: areas the routes don't reach (Tephra Cave onwards, Bionis' Leg...): the [audit] log runs in every
  build, so a player's log will show new classes.
- [x] perf (2026-10-20) **submissions split every 400 draws** (exec.c split_submit, `XCDE_SUBMIT_DRAWS`, 0 = off). User:
  60 fps mode dips to 55-57 looking at the open meadow at 4K with the PC mostly idle. Reproduced (real time, 4K,
  user's meadow save, camera spinning, build/spin.txt): 49-51 fps in that direction; GPU 12.8 ms + render thread
  8 ms a frame and SyncWait ~9 ms a frame - the game's whole frame was one Vulkan submission, so the GPU started only
  after recording ended (frame = recording + GPU). With the split (~10 submissions a frame) the GPU overlaps the
  recording: 60.0 fps through the whole spin (was 49 at worst). Occlusion counts split across submissions report
  "visible" (safe); culling still works (thousands hidden per 2 s). Captures: load_walk 3000 identical, 6000 noise;
  new_game_h 6000 / 11400 / 12000 identical.
- [x] **FPS option 30 / 60 / 120 / 144 / 165 / unlimited** (2026-10-20, launcher "FPS", xcde.ini `fps = 120` or
  `unlimited`): above 60 the limiter's period constant (0x70009d3dcc) is scaled by 60 / target (limiter registers read
  at its exit: target = interval x 1/60 x constant). Deterministic 120 fps run with the route time-scaled x4: same clock
  (9:44 / 10:11) and positions as at 30. Real time: 120 fps steady at 720p; 4K uncapped in the heavy meadow view 53-97.
  Caps found on the user's PC on the way: RivaTuner's global frame limit (Limit=60) and NVIDIA's forced vsync (the
  user changed both). XCDE_VSYNC_HZ=<hz> also added (the game does not wait on that event: 0 vsyncs per present).
- [x] perf (2026-10-20) **async render worker** (exec.c rq_*, objects.c): QueueSubmitCommands / FenceSync /
  PresentTexture / TextureFinalize queue jobs that a worker thread runs in order; a sync wait first waits for the job
  that sets the fence (tickets; fences inside lists found when the list is queued, under the queue lock); at most 2
  presents queued; the worker's idle time counts as blocked for the 30 fps pacing check. Off in deterministic runs and
  with XCDE_ASYNC_RENDER=0. Measured (4K, user's meadow save, camera spin, fps unlocked after loading,
  tests/routes/load_spin.txt): 50-100 fps -> 62-116 fps (worst +24 %). Checked in real time: battle_b (no flicker,
  HUD fine), the Colony 9 gate, the intro cutscenes and the battle tutorial (realtime_tap_a_long, empty save), no crash
  in ~30 min of runs. Other recomps do the same ("replay thread" / "render thread with fence tickets":
  docs/lessons_perf_recomps.md).
- [x] T175 redo (2026-10-20) **device-local mirrors of the transform-feedback buffers** (exec.c xsh_*): after each
  writer draw the captured bytes are copied once into a VRAM mirror of that buffer; vertex / index fetches starting
  in its range read the mirror (bound size clamped to its end: the game binds streams with the buffer's whole size
  from an offset). The heap keeps the data (shader loads / CPU unchanged). GPU profile, 4K heavy meadow view
  (LARECOMP_GPUPROF_AT every 250 frames over the spin): frame GPU time avg 9.47 -> 5.69 ms, worst 13.42 -> 8.49 ms
  (-37 %); the two grass passes 3.5 + 3.3 ms -> gone from the top (the G-buffer chunks lead now, ~1 ms each).
  First try with a 1 MB margin after the buffer: wrong - the margin covered the skinning palettes the GPU rewrites
  every frame (stale copy: pixel differences); replaced by the clamp. Verified: load_walk 3000 identical, 6000 45 px;
  new_game_h (skinning, cutscenes) 6000 / 9600 / 11400 / 12000 identical; ghost repro at noise level.
  `XCDE_XFB_SHADOW=0`: off; off by default on integrated GPUs. `XCDE_TRACE_DIRECT=1`: ranges still read from host
  memory (remaining: STG-written ones, e.g. skinning palettes - candidates for the same treatment).
- Tried 2026-10-20, NOT kept (measured, 4K uncapped meadow spin, worst view ~100 fps, worker ~7.5 ms a frame):
  reuse of the previous draw's descriptor set when its contents are identical (+ skipping the bind): 133.5 -> 133.6
  fps avg, worst 96 -> 95; key / program memo by state generations (exec_list bumps): 133.5 -> 134.8, the key time in
  the heavy windows unchanged (the game issues a key-relevant command between almost all draws). Measured after the
  VRAM mirrors: GPU ~6 ms vs worker ~7.5 ms a frame in the heaviest direction - the worker (driver ~35 % of its busy
  time, per-draw prep 1.8, keys 1.2, sets 1.5 ms) is the limit there. Next lever: record with two threads (one builds
  keys / descriptor sets / copies, the other only records vkCmd*), or bindless descriptors.
- [x] perf (2026-10-20) **one frame in flight** (objects.c nvnSyncWait, "frame lag"): the game's frame limiter
  (f_70005bcfe0 -> f_7000603900, caller lr 70005bd038) waits at the end of every frame for the GPU to finish that frame
  (XCDE_LOG_SYNCWAIT: always 1 submission behind the newest, ~2.5 ms a frame): CPU and GPU took turns. Now that wait,
  after the async worker has run the frame's jobs (constant buffers / textures copied, vertex cache snapshotted at
  submit), waits for the GPU of the PREVIOUS frame. On where the vertex cache is on (discrete GPUs), off on integrated
  GPUs (vertices read in place); XCDE_FRAME_LAG=0/1 to force. First try looked slower (84 fps): our 30 fps fallback
  ("frames don't fit 60") had fired - it now runs only with the game's own 30 fps (FPS option 30). Measured 4K
  uncapped meadow spin: **133 -> 162 fps average, worst 96 -> 124**. Checked in real time: battle_b at 120 fps (flicker
  detector: 3 one-frame black silhouettes, the game's own T173 effect - the same run without frame lag shows it too),
  intro cutscenes + battle tutorial, Colony 9 gate day / night: correct.
- [x] T197 (2026-10-20) **VRAM mirrors of the store-written vertex ranges** (exec.c xsh_stored): the last two ranges
  draws still read from host memory (XCDE_TRACE_DIRECT: 7265efca00 +72160, 7265f0e500 +61472) are written by a
  vertex-stage storing writer (vs 72c2922800, sbuf stores - not transform feedback, not compute) and read as vertex
  data by ~10 programs. An in-place vertex read of a GPU-written page is noted; from the next storing draw / dispatch
  binding that range on, each one refreshes a VRAM mirror of the whole storage buffer (<= 1 MB) after the draw.
  Transform-feedback mirrors are untouched. Measured 4K uncapped meadow spin: 163.7 -> 166.3 fps avg, worst 120 ->
  129, GPU 5.79 -> 5.73 ms a frame. Verified: new_game_h 6000..12000 identical, load_walk / ghost repro at the
  run-to-run noise (same exe twice: 898 px; XCDE_STORE_SHADOW=0 vs on: 132 vs 140 px), battle_b real time: no flicker.
  `XCDE_STORE_SHADOW=0`: off. Measured for the two-thread plan (rdtsc around every call, same view): vkCmd* recording
  ~1.0 ms a frame, descriptor allocate / update ~0.2 ms, of ~4.4 ms worker time: a record-only thread can take at
  most ~1 ms off the worker, and the average frame is GPU-bound now (GPU 5.7 > worker 4.4 ms).
- [x] T198 (2026-10-21) **Game AA / motion blur option** (user: the game looks blurry at 4K even with depth of field
  off; pointed at the community "AA/Blur Removal" mod, gamebanana 452909). The game's graphics configuration
  romfs/monolib/shader/lib_nx.ini turns on its temporal AA (tmaa, with tmaaNewUpScale), AntiAliasing, motion blur
  (blur2: object + camera) and fur blur - tuned for the Switch's 720p. The virtual romfs (romfs_virtual.c maybe_edit)
  now serves an edited copy from memory: xcde.ini `game_blur = 0` (launcher "Antialiasing y desenfoque de movimiento
  del juego", on by default = the game's own look) sets those four to off; `XCDE_LIBNX="key=value,..."`: test edits of
  any key. 4K deterministic captures (load_walk 3000 / 6000): edge energy +22 % / +44 %, the moving camera's smear on
  the rocks gone. Default path verified unchanged (verify.sh at noise level); battle_b real time with them off: no
  flicker. Also checked on the way: the presented image is 4K at "match" (only the first frame is 1280x720, before
  the scale is set; the "[post] ... fsr1" log line is printed only when an upscaler runs).
- [x] T199 (2026-10-21) **V-Sync option + frame lag only above 60 fps** (user: at a steady 60 fps on a 60 Hz monitor
  it "feels laggy", Afterburner frametime flat). The game's limiter aims at 0.997 x 1/60 s (~60.2 fps); the Switch's
  display holds frames to its vblanks, our mailbox present did not: frames drifted across the 59.998 Hz vblanks (some
  shown twice, some never). device.c present_mode: FIFO at FPS 30 / 60 when xcde.ini `vsync = 1` (default; launcher
  "V-Sync (con 30 / 60 FPS)"), mailbox above 60 / unlimited / test runs. objects.c: the frame lag (one frame in flight)
  only when FPS > 60 or unlimited - at 60 a frame fits the period and it only added a frame of input latency. 4K
  meadow spin with FIFO: 60.0 fps, max 17 ms. Tried and dropped: locking the emulated vsync / the limiter to DWM vblank
  times (the game doesn't use vi's vsync thread; the DWM-based phase metric proved unreliable). Notes:
  docs/worklog_session14.md.
- [x] T200 (2026-10-21) **Frame drops to ~50 fps entering new parts of Colony 9** (user: short drops 60 -> 50, not at
  once on entering, shaders already precompiled). User log: each drop = a frame of 160-190 ms with `build waits` 2-9
  (162-273 ms), at prewarm bursts (~500 programs registered by the game when an area streams in). Not stale caches:
  only 10 SPIR-V compiled in that whole session. New `[build-wait]` log (exec.c build_wait_log: any draw waiting > 8 ms
  for its program / pipeline, with queue / lock / translate / compile times, new SPIR-V, key, libraries built) showed
  the draw waiting **98 ms for the translator lock** with 0.1 ms of translation of its own: the translator thread
  translated the prewarm variants back to back and re-took the (unfair) lock each time. Now urgent callers (a waiting
  draw, compute) go first (xlat_lock: the translator yields while one waits). Same route (tests/routes/walk_far.txt,
  user's save, real time): waits over 8 ms on the lock 4 -> 0; load-burst build waits 309 -> 140 ms. Left: whole
  pipelines from the driver cache take 9-17 ms (loading screens only). Variant classes precompilation doesn't guess
  (from the user's cache/variants.bin, 4,333 variants: 83 % match the guess; integer textures 420, integer targets 158,
  depth-only 113, integer vertex inputs 76, geometry 42, transform feedback 40) cost a first-time compile once.
- [x] T201 (2026-10-21) **AMD FSR 3.1 and NVIDIA DLSS (temporal upscaling / AA)** - launcher "Escalado / antialiasing":
  FSR 1 / FSR 3.1 / DLSS + quality (Native AA 1x, Quality 1.5x, Balanced 1.7x, Performance 2x, Ultra 3x of Match
  display); xcde.ini `upscaler = fsr3 | dlss`, `upscale_quality = native|quality|balanced|performance|ultra`.
  exec.c finds the game's camera each frame in the vertex constant buffers (512-byte buffer: view 3x4, projection with
  row 6 = 0 0 -1 0, view-projection = P x V, checked) and jitters (Halton 2/3 viewport offset) every draw into a depth
  of the scene depth's size with the depth test on - jittering only the scene depth's own image removed the ground
  and walls (the depth prepass and the EQUAL colour pass use different depth images). temporal.c: one pass at render
  size copies the game image, the scene depth (R32F) and writes camera motion vectors (previous VP x inverse(current)),
  then FSR 3.1.4 (FidelityFX API, amd_fidelityfx_vk.dll loaded at run time; needs shaderFloat16 / subgroup size
  control, now enabled when the GPU has them, and a KHR -> core function-name shim) or DLSS (dlss.cpp: Streamline
  2.14.16 in manual-hooking mode - instance / device extensions and features added at creation, slSetVulkanInfo,
  swapchain calls through its proxies, frame-based tags) upscales to the window. The game's own AntiAliasing / TMAA
  are turned off with them (lib_nx.ini). Fallbacks: DLSS unavailable -> FSR 3; no camera this frame -> FSR 1.
  Verified: deterministic captures with the options off identical to the previous build (frame 3600; frame 3800 has a
  run-to-run difference in a 9x13 px far object, also between two runs of the same exe); FSR 3 Quality 853x480 ->
  1280x720 and Native, DLSS Quality: complete images, detail close to native. 4K GPU time a frame (meadow spin): native
  5.71 ms, FSR 3 Quality 4.74, DLSS Quality 5.25. Limits: camera motion only (no per-object vectors yet), HUD is part
  of the input. Not done: frame generation (launcher checkbox disabled), FSR 4 (no Vulkan SDK as of 2026-10-21).
  Note: <work dir>\sdk\sl\include had two all-zero headers (sl_appidentity.h, sl_device_wrappers.h): fetched again
  from the v2.14.16 tag (RenderAPI = eD3D11, eD3D12, eVulkan). DLLs: scripts/copy_upscaler_dlls.sh (run by the build).
- [x] T202 (2026-10-21) **In-game options (F1)**: runtime/ui/menu_vk.cpp - Dear ImGui overlay drawn by its Vulkan
  backend after the game image; F1 opens / closes, Esc / B close; keyboard, mouse and pad go to the menu while open.
  Live: fullscreen, internal resolution, upscaler + quality, SMAA, depth of field, FPS in the title, V-Sync (swapchain
  recreated), volume; at the next start: FPS, the game's AA / blur, movie audio. "Guardar" writes xcde.ini.
  LARECOMP_MENU_AT=<frame> opens it in a test run (checked with a capture).
- [x] T203 (2026-10-21) **Mods**: mods/<name>/romfs/... (Ryujinx / yuzu layout) replaces or adds game files
  (romfs_virtual.c apply_mods, alphabetical, later wins, case-insensitive names; a modded lib_nx.ini still gets the
  AA edit); xcde.ini `mod_<name> = 0` turns one off; launcher tab "Mods" lists them with on/off and opens the folder.
  Code mods (exefs / pchtxt / IPS) don't apply to recompiled code. Checked with three test mods (XCDE_MODS_DIR):
  replaced, added and turned-off files in the log ([mods] lines); no mods folder = no change.
- [x] T204 (2026-10-21) **FSR 3 frame generation** (temporal_fg.inc; launcher / F1 "Frame generation", xcde.ini
  `frame_gen = 1`, with FSR 3.1): device.c reserves AMD's three extra queues (present: graphics+compute+present;
  image acquire; async compute - picked as the FidelityFX sample does; with the option off the device is as before),
  the first swapchain is handed to AMD's frame-generation swapchain and its replacement functions take over create /
  destroy / images / acquire / present; every frame the frame-generation context is configured (off without a camera:
  menus, loading) and the interpolation is prepared from the upscaler's depth and motion vectors. Measured (real time,
  game at 30 fps): 239-240 presents per 120 frames. Found on the way: create_swapchain asked for 8 images in one call -
  AMD's swapchain has 3 and the driver crashed creating views of the 5 empty slots: count first, then fetch. Not done:
  DLSS frame generation; a HUD-less image (the HUD is interpolated too).
- [x] T205 (2026-10-21) **Characters' faces drawn as vertical strips** (user shots: Shulk / Dickson / Fiora in Colony 9,
  cutscenes and field, after playing a while). T197's store mirrors: the vertex-stage writers rebind the same scratch
  memory with other sizes as scenes change (user log: 7265f2ef00 +40224, later 7265f2ef00 +81632). The older mirror
  was no longer refreshed but matched lookups first: stale vertices, and the binding clamped to its end left the
  rest out of bounds. exec.c xsh_retire_overlaps: a new store mirror retires every store mirror it overlaps (buffer
  freed when its submissions are done). A fresh load doesn't reproduce it (5 mirrors, none overlapping: the
  cutscene_1520 save's Vangarre scene is fine with both builds); verify.sh at noise level; user to confirm in a long
  session. Routes: tests/routes/load_a2.txt (load with two extra A presses), cutscene_walk.txt (walk forward into the
  cutscene, A every 120 frames). Tests with FPS 60 in the ini stall at the load dialog: use an ini without `fps`.
- T207 note (2026-10-21) **"cutscenes feel 30 fps at FPS 60"** (user) - measured, not reproduced: new diagnostic
  XCDE_DUP_CHECK=1 (device.c dup_check: a 64x36 GPU thumbnail of the top 55 % of every presented image, read back 3
  frames later, compared with the previous one; "[dup]" every 120 frames, XCDE_DUP_VALUES=<frame> logs 90 raw
  differences). cutscene_1520 save + tests/routes/cutscene_walk.txt with XCDE_FPS_INTERVAL=1 XCDE_FPS_AFTER_FRAMES=3500
  (Vangarre scene at 60 fps): 0 repeated frames, differences vary smoothly (no small / large alternation = a new image
  every frame; a 30 fps animation would alternate). The user's session log shows 60.0 fps throughout. Open: which
  scene, whether character animation keys step at 30 under a moving camera (needs a static-camera shot).
- [x] T206 (2026-10-21) **Party mod: Xenoblade 3-style switching of the controlled character** (runtime/hle/party.c,
  docs/party_switch_research.md). F2 / L3+R3 (launcher Controls option, xcde.ini party_switch, off by default) rotates
  the leader among the 3 deployed members as the game's Party menu does it (field group rebuilt, entity focus, set
  leader); in battle the HUD arts palette follows, downed members are skipped; refused in menus / cutscenes / loading;
  the new leader's pending follow move is dropped (no lock while running). Objects found by a scanner thread (no hitch).
  Verified: field and battle, 2 / 3 / 7-member parties, arts / damage of the new leader, Chain Attack and Visions
  (user), no-switch runs identical.
- [x] T209 (2026-10-21) **~100 ms freeze every 2 minutes** (user: "it still stutters"; their two logs: 80-89 ms frames
  at t=124.8 / 244.9 and t=124.2 with no pipeline work). New "[hitch]" log (device.c backend_present + exec.c
  vk_hitch_counters; frames over 25 ms and twice the recent average: pipeline waits, cached / linked / whole builds
  with build-thread time, upload MB; 300 lines max, XCDE_LOG_HITCH=0 off) on walk_far.txt (faces_1515, 60 fps, 8 min):
  4 hitches of 97-100 ms exactly 7,196 frames apart = the periodic pipeline-cache save (100+ MB serialized and written
  on the render thread). Now saved on a thread of its own (vk_pipeline_cache_save_async) and only when pipelines were
  made since; per-process temp file (test runs and the game save the same cache). Same route after: 3 hitches, all in
  the first minute (title, load, one first-time pipeline). Also seen: first-run "linked" pipelines whose libraries
  compile 10-58 ms each (T211: precompile the libraries), load bursts of whole pipelines from the driver cache 9-17 ms
  each. verify.sh at noise level.
- [x] T211 part 1 (2026-10-21) **stale precompile**: the user's precompile was from 10-20 10:41; translator fixes since
  (T180, T192, T178, ...) changed the SPIR-V, so most pieces no longer matched and the game compiled them while
  playing (first-run "linked" pipelines whose libraries took 10-58 ms each in the [hitch] log). A refresh run: 12,958
  SPIR-V compiled, 25,452 from the cache, 120 s. precompile.c writes "exe <size> <mtime>" of build/xcde.exe into
  cache/precompile_done.txt; the launcher's pc_done() compares it, so JUGAR precompiles again after every new build.
  Note: the libraries live in the driver's own disk cache only (vk_pipelines.bin stays small, T187).
- [x] T211 part 2 (2026-10-21) **pipeline pieces ready at loading time + link first** (user: no hitches even in the
  ~30 areas not visited yet; OpenSmash's recipe, docs/lessons_astral_ssbu.md). exec.c: a program the game registers
  with no recorded variant (new area / new player) gets the precompilation's guessed variant translated and its
  pre-rasterization / fragment-shader libraries built on the workers (gpl_prebuild, pl_pending; discrete GPUs only,
  XCDE_PREBUILD_LIBS=0/1); build_pipeline links first when both libraries are in memory (gpl_ready; ~0.3 ms vs 2-17 ms
  for a whole pipeline from the driver cache), the optimized one still swaps in later. "Never visited" test
  (<work dir>/coldroot: fresh precompile, no variants.bin, no vk_pipelines.bin; walk_far.txt at 60 fps, 8 min):
  load-end spike 458 -> 192 ms, hitches while walking 4 (41-196 ms) -> 2 (41-44 ms), 395 pipelines linked at ~0 ms.
  Left: 610 whole pipelines (variants the guess misses), hitches at the loading fade. Next: wider variant guessing,
  a shipped variant seed, background preparation while playing (paused in battle), a loading barrier, a fallback
  variant instead of waiting. verify.sh at noise level.
- [x] T211 part 3 (2026-10-21) **variant seed**: data/variants_seed.bin (5,007 variants recorded in real play: the user's
  cache/variants.bin + every test cache on E:, tools/merge_variants.py) - exec.c var_load reads it besides the player's
  own file (prewarm at loading screens knows them from the first session); precompile.c builds each distinct
  (shaders, keys) of it exactly after the guessed pass (1,391 in 3 s). [variant-miss] log (exec.c compile_program): a
  variant the precompilation didn't make, how its keys differ. Never-visited test (coldroot, walk_far.txt, 8 min):
  variant misses 25 -> 3, hitches while walking 2 -> 1 (34 ms), load-end spike 192 -> 68 ms (optimistic: the seed
  holds this route's variants). The misses follow the data a draw binds (integer vertex inputs, stencil textures,
  integer targets), not the shader - next: derive the vertex-input ones from the model files at precompile. Grow the
  seed with the user's cache/variants.bin at each update. verify.sh at noise level.
- [x] T211 part 4 (2026-10-21) **precompile reads the containers' input / texture names** (precompile.c spch_inputs;
  SPCH program data layout from the public description in ScanMountGoat/xc3_lib, read only; survey tool
  tools/spch_attrs.py): per program, its vertex / fragment control sections (follow the programs' NvsdShaders sizes:
  1,479 / 1,479 found in monolib, 18,424 / 18,424 in chr) and its vertex inputs (name, location) and samplers (name,
  unit). Monolith names inputs by type: v* / f* float, n* integer (nWgtIdx: location 1 in 17,729 character programs,
  location 0 in 356); stencil textures gTStencil / gTCurStencil / gTPrevStencil (unit = the key's tex_uint bit).
  Names say what CAN be an integer (a draw without that data binds a float format: names INSTEAD of the guess missed
  170 variants), so they add versions to the guess: integer inputs other than location 1, stencil textures as
  integers. Never-visited test without the seed: variant misses 25 -> 16 (integer input 0: 6 -> 1); precompile
  120 -> 144 s (4,149 more versions). Left: integer render targets, transform-feedback keys, a few stencil textures
  under other names - the seed's (global shaders).
- [x] T213 (2026-10-21) **HUD ghosting with DLSS / FSR 3** (user): the upscalers accumulated the image with the HUD
  in it. Now exec.c vk_end_pass copies the presented image when the frame's first pass into it ends (the scene
  composite: the HUD passes follow; temporal.c tmp_hud_snapshot), the inputs pass (shaders.c tmp_prep.frag, output
  3) marks the pixels the HUD changed, and that mask goes to FSR as its reactive mask and to DLSS as
  kBufferTypeBiasCurrentColorHint (dlss.cpp): no history on HUD pixels, any HUD / menu / scene, measured per frame.
  XCDE_TMP_NO_HUD_MASK=1: off. Cost: one image copy + one extra output, < 0.1 ms. Not yet confirmed visually (still
  frames don't show it; the user tests it). Next step: the HUD drawn at the window size after the upscale (sharp HUD).
- T213 follow-up (2026-10-21): the user still saw the HUD "vibrate" with the mask: the upscalers undo the jitter on
  everything they get, and the HUD was never jittered - no mask can fix it while the HUD is in their input. Now they get
  the image before the HUD (the snapshot) and exec.c post_process adds back what the HUD passes added (shaders.c
  tmp_hud.frag: upscaled scene + (final - snapshot), render size bilinear, where they differ). The HUD is drawn at the
  render size (soft in Quality) but stable, no trails. HUD draws are also never jittered now (tmp_hud_started). Next
  step: the HUD rendered at the window size.
- [x] T208 (2026-10-21, party mod session) **Saving over a save from another game version crashed** (user, a downloaded
  100% save): runtime/services/fs.c kept every file the game opened open (no on_close), so DeleteFile failed on Windows
  and the game aborted. on_close now closes IFile / IDirectory. Verified: the downloaded save loads and autosaves with
  the fix (build/xcde.exe crashes on it).
- [x] T210 (2026-10-21, party mod session) **Field followers fall behind at 60 fps** (user): a frame-count threshold
  (follower move restart after > 9 frames, f_7000443760 / f_70004439f0) scaled to the frame rate by two patches
  (games/xcde/patches.py) + xcde_frames_gt (runtime/hle/party.c). 60 fps: ~6.8 m behind while running, as at 30 (was
  2 -> 17.5 m and growing); 30 fps: identical positions.
- [x] T215 (2026-10-21) **DLSS / FSR 3 get the game's own per-object velocity** (user: characters look worse with DLSS
  Quality than with bilinear - camera-only motion vectors: moving characters lost their history). The game keeps a
  velocity buffer for its temporal AA / AO / shadows (gTVelocity, a G-buffer target: 1280x720 guest, RGB10A2, written also
  with the game's AA off). Found at runtime through its readers (17 fragment programs found by their container names
  and code hashes; exec.c calls tmp_set_velocity). Encoding measured against our camera motion on static scenery
  (temporal.c XCDE_TMP_VEL_FIT=<frame>): R = sqrt|v.x|, G = sqrt|v.y|, alpha bit 0 = x negative, bit 1 = y positive,
  UV units, previous minus current (e.g. R 0.0762 vs sqrt(0.005798) = 0.0761). The inputs pass (tmp_prep.frag) uses it
  where the scene has geometry, our camera motion on the sky. XCDE_TMP_GAME_VEL=0: camera only. XCDE_TMP_LOG=1 says
  whether it was used each second. Also: test runs never overwrite the player's pipeline cache (2c4cb62).
- T213 / T215 follow-up (2026-10-21): with DLSS characters still looked jagged (user). XCDE_TMP_LOG counted 0 jittered
  draws a frame: the game writes the window image early in the frame too, so the pre-HUD snapshot fired before the
  scene and "no jitter after the HUD began" turned the jitter off for everything - DLSS / FSR had no sub-pixel
  samples. The snapshot now waits for the frame's first scene draw (exec.c tmp_scene_frame): 248 draws jittered a frame.
  The game's velocity on characters measured plausible (idle motion ~1e-4 of the screen, sign bits mixed).
  Also found: the NVIDIA driver's shader cache (AppData/Local/NVIDIA/GLCache) at its 1 GB default limit - the
  precompiled libraries were evicted, pieces compiled 30-55 ms while turning the camera; the user set it to unlimited.
  Next: keep the libraries in our own cache file (RAM-aware) so no driver limit matters.
- [x] T212 (2026-10-21, party mod session; docs/handoff_shader_pipeline.md "Fix 1") **Shader libraries prebuilt for
  programs with recorded variants too** (exec.c prewarm_drain / gpl_prebuild_variant): before, only programs without a
  recorded variant got their pre / fs libraries prebuilt, so new state combinations of the others loaded whole
  pipelines from the driver cache (2-5 ms each). Now once per (program, fill mode, samples, a2c) of their variants.
  Measured on <work dir>/coldroot (fresh exe path + precompile, the user's variants.bin, fallen_arm save, load + camera
  turn + run, 60 fps, second runs = warm driver cache, 3 runs each): stalls after loading 2.16 -> 1.74 s, worst frame
  (the area's first frame) 1.35 -> 0.91 s. Tried and dropped: linking while the libraries are still being built
  (waiting for them) - no better (1.94 s).
  Part 2 (same day): with the libraries prebuilt, the recorded variants' pipelines aren't built whole ahead any more
  (they saturated the workers: ~2,600 whole pipelines queued 0.6 s before the area's first frame), and pipelines are
  always linked from libraries (built if missing) - no "cached whole" route left on GPL GPUs (exec.c link_first;
  XCDE_PREWARM_WHOLE=1 restores the old way). Same test: stalls after loading 1.49 s (2.16 before T212), "cached" 0.
  What is left: the area's first frame (~0.5-0.8 s): the game reads the area's files at ~frame 3712, registers ~1,000
  programs at ~3745 and draws at ~3780 (LARECOMP_LOG_FILES) - the libraries can't all be ready in that time; it falls
  in the black transition into the area. Not done: libraries memory on a long run (GPL_TAB 16384, never freed); a
  per-zone head start from the files read (~0.5 s at most on a fast load).
- [x] T214 (2026-10-21, party mod session) **Shader-library memory + T205 redo.** (1) The libraries were made with
  RETAIN_LINK_TIME_OPTIMIZATION_INFO although nothing links them with LTO (gpl_optimize compiles the optimized pipeline
  whole): dropped (XCDE_GPL_RETAIN=1 keeps it). Peak process memory on the coldroot route: no libraries 6.83 / 6.85 GB,
  libraries with the flag 7.46 GB (~630 MB for one area's ~3,460 libraries), without it 7.19 / 7.16 GB (~320 MB);
  stalls unchanged (warm 1.13 / 1.00 / 1.92 s, "cached" 0). (2) Libraries are prebuilt only below a budget in memory
  (12,000 with >= 24 GB RAM, 6,000 from 12 GB, else 3,000; XCDE_LIB_BUDGET); a draw's own libraries are still built on
  demand. (3) T205 seen again (user: Shulk's face as strips, Fallen Arm): any new vertex mirror - store or transform
  feedback - now retires every mirror of either kind it overlaps (the user's log: 7265f79c00 +61248 over 7265f7c000
  +288 / 7265f7c300 +61472; only store mirrors were checked, against store mirrors). "[vk] mirror ... retired" log (40
  lines). Colony 9 walk: 0 retirements (no per-frame churn). Not reproduced here (it needs a long session).
- [x] T216 (2026-10-22, party mod session) **HUD ghost over the main menu with DLSS / FSR 3** (user shot: the field hints
  "Ziel erfassen / Kamera bewegen / Automatisches Laufen" as a text outline over the character cards; earlier reported
  as the area banner bleeding into the party menu). The T213 composite (tmp_hud.frag: up + (final - pre-HUD snapshot))
  left upscaled(x) - bilinear(x) of whatever the HUD covered; in the menu the game's captured background (with the
  hints) is part of the "scene" the upscaler sharpens, so opaque cards showed the hints' outline. Now where the HUD
  changed the pixel the game's own image is taken (smoothstep 1.5/255 .. 0.03 of the difference). Reproduced only in
  REAL TIME with every frame presented (hidden deterministic runs present only the captured frames: no history, no
  ghost) - scratchpad ghrt.sh style: LARECOMP_HIDDEN=1 XCDE_PRESENT_ALWAYS=1, no XCDE_DETERMINISTIC, the user's ini.
  XCDE_TMP_NO_HUD_MASK=1 removed it (confirms the composite). Field: frame-to-frame change in the minimap / hints areas
  unchanged (0.022 / 0.041 vs 0.023 / 0.041): no new shimmer.
- [x] T218 (2026-10-22, party mod session) **Area-entry freeze: programs dropped from the prewarm + pipelines linked ahead**
  (exec.c).
  Cause: vk_program_registered kept at most 256 programs between two draws. An area registers ~1,000 during its black
  transition, so the rest were dropped silently: no libraries and no recorded pipelines. Their first draws then
  translated and built on the render thread: ~350 programs and ~300 pipelines in the area's first frame, all of them
  in cache/variants.bin.
  Fix:
  - The queue grows (pw_pending 8192, pl_pending 4096, lv_pending 8192).
  - On GPL GPUs with 24 GB of RAM or more, the recorded pipelines are linked ahead on the workers. Their optimized
    pipeline is queued at their first draw (Pipe.how 0x40). XCDE_PRELINK=0/1.
  - Whole-pipeline prewarm (no GPL / iGPU): below 24 GB of RAM, only the first 256 (below 12 GB) or 768 programs of a
    registration batch, as before. XCDE_WHOLE_BATCH.
  - XCDE_BUILD_WAIT_MS=<ms>: [build-wait] log threshold.
  Measured on coldroot (fallen_arm, turnrun60, warm, area's first frame):

  | Configuration | Before | After | Peak memory before | Peak memory after |
  |---|---|---|---|---|
  | GPL | 1,166-1,554 ms | 195-219 ms | 7.2 GB | 8.3 GB |
  | GPL, queue fix only (XCDE_PRELINK=0) | - | 231 ms | - | 8.06 GB |
  | LARECOMP_VK_GPL=0, 8 GB budget | 1,540 ms | 1,012 ms | 6.93 GB | 6.86 GB |

  In-play hitches after the area appears: none (GPL).
- [x] T220 (2026-10-22, party mod session) **FSR 3: frayed HUD text on the title screen** (user shot: the copyright line,
  grass showing through the letter edges; DLSS clean).
  Cause: on the title screen the pass that composites the scene into the presented image goes on with the HUD glyphs
  in the same pass:
  - draw 1 is the full-screen composite;
  - draws 2-9 are instanced glyphs ("Drücke einen beliebigen Knopf", the copyright).
  The image before the HUD (tmp_hud_snapshot, taken at that pass's end) therefore held the text, so FSR 3 took it as
  scene: sharpened, reprojected with the grass. XCDE_TMP_NO_HUD_MASK=1 gave the same image, which confirmed it.
  Fix (exec.c, before begin_pass in draw_): in that pass, after the scene and before the HUD started, the pass ends
  after its first draw, so the snapshot is the scene alone. tmp_hud.frag also takes its weight from the HUD change one
  render texel around the pixel.
  Checked, real time at 4K (XCDE_PRESENT_ALWAYS=1):
  - title text at its opaque peak: FSR 3 now as clean as DLSS;
  - fallen_arm field with FSR 3 / DLSS, old vs new: HUD, minimap and scene unchanged.
- [x] T222 (2026-10-22, party mod session) **Save list thumbnails: pink / green garbage or black in-game until saving**
  (user shots). Reproduced in real time:
  - fallen_arm save, then the in-game Save list (scratchpad route savelist_rt);
  - every other frame showed garbage in slots 1-2, with the old exe and the new one alike.
  Cause: T181 copied the picture into its twin buffer only when the twin looked empty (the 0xf3 marker + zeros). On the
  title the twins are fresh memory; in-game their memory held leftovers, which were neither "empty" nor the picture.
  Fix:
  - A patch on the game's own copy of the loaded .tmb (games/xcde/patches.py 0x700057dab4, the bl memcpy in
    f_700057da00) records which buffer holds the game's picture and its hash.
  - slot_thumb_fix copies that buffer into its twin whatever the twin holds. The twin must be a live one (drawn for
    the slot within 2 frames).
  - The empty-marker guess stays only if the hook never fired.
  - generated/main/main_115.c was hand-patched with the same text (build/obj/main/main_115.o rebuilt).
  Checked: title load list (2 frames) and in-game save list (3 consecutive frames): all 4 thumbnails right.
- [ ] T224 (2026-10-22, party mod session) **Cutscenes feel like 30 fps; Dickson's ponytail vibrates** (user, first save
  slot, a few steps ahead).
  - Measured:
    - presents are steady at 16.7 ms;
    - in the Dickson close-ups the frame-to-frame difference alternates (2.81 / 0.84), so character animation advances
      on every other frame only;
    - the field animates every frame.
  - The cutscene script runs as fiber coroutines (interpreter f_70004e84c0; f_70004f4860 / f_70004eb4a0 / f_70004f5220
    on the stack). f_7000603870 (double-buffer index toggle) is not the gate.
  - Tools (ab71342):
    - XCDE_REC / F10 recorder;
    - fnprof even / odd counts;
    - XCDE_MEMWATCH.
  - Lead from MacNativeGames 290ec9f: TOTK's hair / cloth clock was built as factor / 30 every rendered frame, so it
    swung too fast above 30 fps. Look for a fixed 1/30 step in the cloth / hair update the cutscene path uses.
  - 2026-10-23 (deterministic repro: user save, scratchpad ud_rt.txt, XCDE_INI=build/ini_raw60.ini, frames 6300-6303):
    - frame-to-frame image difference 0.32 / 0.03 / 0.30: the alternation reproduces without real time.
    - Ruled out:
      - the even-frame-only functions from the earlier fnprof runs (f_70004e43e0, f_700002c4f0, f_70005aad40)
        are one-off bursts inside one frame, not a per-frame gate;
      - f_70004f5220 is the camera sequence (rtmevt_seq_cam_impl.h, a circle of sin / cos), not a coroutine;
      - counter 0x7271380a1c (+1 every 2 frames) sits in a GPU-written page (no CPU access trips the watch).
    - Found:
      - a global 30 fps tick: f_70007b4b00 adds [obj+0x68] (0.4985 at 60 fps, 0.997 at 30) to a float at
        *(0x7000b94e50)+0xc and acts when its integer part changes (callback every 32 ticks);
      - 534 per-object clocks also advance 0.4985 a frame (time is right; the pose is sampled every other frame);
      - the cutscene system is rtmevt (src/game/rtmevt/*; model animation in evt_res_mdl_impl.h:
        f_700050a8b0 / f_700050d1d0).
    - Tools: XCDE_MEMWATCH_CLK=1 (clocks only), + XCDE_MEMWATCH_STEPS=1 (monotonic counters),
      XCDE_MEMWATCH_AUTO=cnt (watch the counter found); scratchpad nsostr.py reads the assert strings (source paths).
    - Next: find what makes the character update of a cutscene skip a frame. Test: force the tick delta
      [obj+0x68] to 1.0 during the cutscene. A 2x-speed cutscene that animates every frame would tie the pose
      updates to that tick.
  - Fallback if the gate can't be fixed (Metroid-Dread-Recomp 17b72bb): run cutscenes at 30 and present them on an
    exact 33.3 ms grid (as the Switch does), so the camera and the characters step together instead of a smooth
    camera over 30 fps poses.
- T226 addendum (2026-10-23): Metroid-Dread-Recomp, all 15 commits, checked:
  - ccd609c (the state cache not reset after the DLSS pass froze the picture): n/a. XCDE forgets its cached state
    (ss_forget) at every render pass begin and after its own passes.
  - 5893d31 (a dotted glow grid at 4x from the game's downsampling passes): n/a. XCDE scales the whole 16:9 chain
    (bloom 320x180 and below included), so the ratios match the Switch.
  - The rest is Dread-specific: DLAA on its OpenGL renderer, a skip-cutscene patch, icons, Steam shortcut.
- [ ] T226 (2026-10-23, party mod session) **General fixes from the other recomps, any PC** (found in the commit review
  of docs/spec_lowend_gpu.md 1.3; not low-end specific). Check each against XCDE.
  - Rule: apply only what fits Xenoblade and changes nothing else. Each one needs deterministic captures in the noise
    band (or the bug it fixes visibly gone) and fps not lower.
  - Performance:
    - [x] letsgo 741fa87: n/a. Buffer-to-buffer copies do wait on the whole GPU, but none happen on walk / battle
      (LARECOMP_VK_PROF waits: only SyncWait and ring slot).
    - [x] letsgo 72a33d9: n/a. Vertex work is 25 ms of a 2 s battle window on the render thread.
    - [x] LAS cc2341f: have (texture write watch: "tex unwritten"; redundant-state filter ss_need).
    - [x] LAS 6f1348c: have (exec.c "copy elision (depth copies)").
    - [x] Wonder eabf8a4: tried and **rejected**. 26.6 % of sets were reused (battle), but the render thread was slower
      with the hashing: sets 77-81 -> 82-88 ms per 2 s; NVIDIA writes sets cheaply.
    - [x] MacNative 426f1d7: n/a. The game issues no indirect draws (no UNIMPLEMENTED line).
  - Visual:
    - [x] PokeZ-A 6a4a713: have (TLD4 / TLD4S); no translation failure names them.
    - [x] MacNative 29dd997 / be82504: n/a (Metal emulation; Vulkan samplers do border colour per axis).
    - [x] PokeZ-A 302bd07: have (draws wait for their build: "build waits", 0 skipped).
    - [x] PokeZ-A 7253341: kept at 0 on purpose (one-lane warps). The game uses no subgroup operations. VOTE is
      emulated to match, see below.
  - Timing:
    - [x] LAS / PokeZ-A de59a87: n/a. Xenoblade's world speed is dt-based (60 fps option notes).
    - [ ] AstralChain 5403cd0 / 6e716d9: cutscene cuts keep exact time at 60 (see T224).
    - [x] Found on the way (all PCs): 36 programs never translated, so all their draws were skipped:
      - 35 fragment programs with SUATOM.D;
      - 1 vertex shader with VOTE + ATOM.
      Implemented (4387cfd); captures in the noise band.
- [ ] T228 (2026-10-23, party mod session) **Jagged moving objects with DLSS / FSR 3** (user shots: Shulk's outline,
  hair and sword, and the grass, step-edged while the camera moves; the rock and the ground are fine). XCDE's motion
  vectors are camera-only (depth + this / last frame's camera): right for the static world, wrong for what moves on
  its own (animated characters following the camera, grass in the wind). The upscaler then drops their history and
  shows the raw jittered image.
  - Fix: per-object motion vectors, as Metroid-Dread-Recomp 578f6ec (motion from transform-feedback captures replayed
    against last frame's).
  - In XCDE the moving vertices come from writer draws (skinning / cloth / grass instance data) into the T197 / T205
    mirrors. So:
    1. keep last frame's copy of each mirror and of the scene draws' camera constants;
    2. a velocity pass redraws those objects with a translator variant of their vertex shader (current and previous
       position);
    3. merge with the camera vectors (where the pass wrote, it wins).
  - Simpler partial steps to weigh first: a reactive mask over those draws (less history, less ghosting, still
    aliased); SMAA on the upscaler input (not recommended by either SDK).
  - 2026-10-23 study (XCDE_TMP_MV_SHOT captures, colony9 load_walk, deterministic + XCDE_TMP_DETERMINISTIC=1, DLSS):
    - The motion handed to DLSS / FSR is the same with and without the game's velocity in the meadow (frame 3500,
      Shulk running): 0 % of pixels differ; frame 2600 10 %.
    - XCDE_TMP_VEL_FIT=3500: the game's velocity buffer correlates 0.993 (sqrt fit) with our camera-only motion,
      and "0 pixels moving where the camera's is 0". The game computes it as the current position against the
      previous camera, not the objects' previous positions. So T215 can't give characters / grass their own motion.
    - tmp_note_target (e0...): the buffer, once found, counts in frames where the game renders into it. Its readers
      run only with the game's AA on; harmless, kept.
    - Way forward, the T228 design above. Characters: keep last frame's copy of each vertex mirror (the skinned
      positions) + last frame's draw constants (camera, model). A velocity pass redraws those draws, a translator
      variant writing current - previous clip position. Grass (wind in its vertex shader, a function of time): the same
      variant with last frame's time constant.
- [x] T230 (2026-10-23) **Keyboard + mouse as an MMO; everything remappable; party switch as Xenoblade 3** (user).
  - New default keyboard layout (runtime/hle/bindings.c DEF_KEY / DEF_KEY2; the launcher migrates an older xcde.ini
    with `bind_layout = 2`):
    - WASD move; F / Enter = A; Space / Backspace = B; I = X (menu); M = Y (map); Esc = Plus; J = Minus.
    - Q / E (Tab) = L / R (targets); C / V = ZL / ZR; arrows (R / G up / down) = the d-pad; Left Shift / middle
      button = the stick clicks.
  - A second key per input (`bind_key2_<input>`). Mouse buttons and the wheel bind like keys (`Mouse Left`..`Wheel Down`).
  - Mouse camera: right button held, `mouse_look` / `mouse_sens` / `mouse_invert`.
  - Actions:
    - `art1`..`art8` (1-8) and `talent` (T): runtime/hle/party.c art macro. It reads the palette cursor (object of
      vtable 0x7000b4ac68, +0x1c8 = slot 0-8, left to right, 4 = talent; found with XCDE_DELTAFIND_PAT), presses
      d-pad left / right until it is there (an empty slot is skipped by the game: the macro stops), then A. Writing
      the cursor doesn't move the game's selection.
    - `party_up` / `party_down` (Z / X).
  - Controller: hold L2 and press L1 / R1 = the member above / below (L2, L1, R1 hidden from the game while L2 is
    held; a lone L2 is sent as a short press on release). Launcher Controls tab: key, key 2, controller columns;
    mouse options.
  - Checks:
    - colony9 battle_a: keys 4 / 5 selected Back Slash / Light Heal and used them (Light Heal opens its target
      choice, as with the d-pad).
    - load_walk: X / Z switched leader.
    - Walk / battle captures in the run-to-run noise band (the same as two runs of 53fb5a3).
- [x] T232 (2026-10-23) **Xbox / PlayStation button icons** (user's GameBanana links: CompC "Xbox control layout"
  694794, "PS5 DualSense control layout" 541180).
  - Both are romfs mods (menu/image/*.wilay, 64 / 78 files).
  - Their license is CC BY-NC-ND: download and install yes, redistribution only with permission. So they are not in
    the repo or in tester; the user installs them in mods/icons_xbox and mods/icons_playstation (mods/ is
    gitignored).
  - Launcher Controls "Iconos de botones" (xcde.ini button_icons = auto | switch | xbox | playstation): turns the
    matching folder on (mod_icons_*; auto = the connected controller's type) and hides both from the Mods tab.
  - Runtime: an icons_* folder without a mod_ line is off.
  - Checked in colony9 battle_a: the battle help shows LB / RB / LT / RT and L1 / R1 / L2 / R2.
- [x] T234 (2026-10-23) **Keyboard button icons, following the key bindings** (user: "un icono por cada tecla",
  since any key can be bound).
  - runtime/services/kbicons.c builds them when the romfs is assembled: menu/image/icon_button, icon_button_hud,
    icon_button_deco, button .wilay (LAHD).
    - Texture: block-linear mibl, BC7 / BC3 decoded with third_party/bcdec (MIT).
    - In each atlas the game's SL key (its label erased) is the key for every Switch button. Each gets the name of
      the bound key (arrows as triangles, LMB / RMB / MMB / wheel, WASD for the move stick, a mouse for the camera
      stick with the mouse camera).
    - Re-encoded as BC3 with one mip, the LAHD texture size updated.
    - button.wilay's cells are in another order (Layout k_glow).
  - On with xcde.ini mod_icons_keyboard = 1: launcher "Button icons: Keyboard", or Automatic without a
    controller.
  - XCDE_KBICONS_DUMP=<dir>: the atlases as .rgba.
  - Checked in colony9 battle_a: battle help ◀▶ / Q E, load menu F; off = captures in the noise band.
  - Not done: font_icon.wilay (icons inside text, tutorials).
  - 2026-10-23: drawn only when the bindings change.
    - cache/kbicons/<file>_<hash>: the hash covers the key bindings, the mouse camera, the game file's size and
      KBICONS_VERSION. An older copy is removed when a new one is written.
    - Drawing all four takes ~7 ms (RTX PC: 1.3-2.0 ms each).
    - Second launch: read from the cache, the same capture.
- [x] T236 (2026-10-23) **Mouse camera feel like a PC game** (user: "no se siente como Dark Souls / The Witcher 3").
  - Measured, colony9 field (XCDE_FLOATFIND found the yaw at 7204cadd7c in the deterministic run, an atan2 result
    of f_7000861000, so writing it does nothing; XCDE_FTRACE traced it per frame).
    - The camera turns at a speed the right stick sets: a dead zone up to ~15 %, then a curve (19 % -> 4 % of the top
      speed, 25 % -> 7 %, 50 % -> 30 %, 75 % -> 63 %).
    - No inertia (it stops the frame the stick is released).
    - The old linear mouse -> stick lost small moves in the dead zone and crushed the rest in the curve.
  - input.c mouse_stick: pixels -> a turn (a fraction of the top speed), then the curve inverted -> the stick value
    giving it. A turn beyond the top speed carries over (up to 10 frames).
  - XCDE_MOUSE_TEST=<frame>:<dx> check: 5 / 30 / 80 / 200 / 300 px -> 0.0023-0.0026 rad a pixel (linear), turning
    from the same frame.
  - 2026-10-23 follow-up (user: big turns have a top speed; turning right then up waits for the turn to finish).
    - The stick path can't exceed the game's top speed: the carried-over turn queues up. A stick past 32767 isn't
      usable either: measured faster up to 2x only to the right, and it stops at 3-4x.
    - Found the camera's own state: object of class vtable 0x7000b381f0, yaw at +0x1f0 / +0x1f4 and pitch at
      +0x1f8 / +0x1fc (radians).
      - Seen with XCDE_FLOATFIND: held right 20 frames then left 10 gives exactly -0.5.
      - Writing +0x1f0 turns the camera that much the next frame.
      - The game clamps the pitch to -0.99 .. 1.19.
    - party.c mouse_camera: with the player in control, the mouse's pixels go straight to yaw / pitch (0.0025 rad a
      pixel at sens 50): no dead zone, curve, top speed or queue. Elsewhere the stick fallback stays.
    - The scanner looks for the camera only once the cursor is captured.
    - Check: 5 / 30 / 80 / 200 / -200 / 600 px each turned within one frame, 600 px = 1.50 rad.
    - Walk / battle captures in the noise band.
  - 2026-10-23 follow-up (user: the field's "Mission ZR" still Switch's; Shift too small).
    - 15 single glyphs inside the screens' LAGP layouts are now redrawn in place, each its own key template (k_single).
      The list is what GameBanana's Xbox pack redraws: mnu001 +, mnu013 LS click, mnu038 / 040 / 043 / 053 / 073 ZL /
      ZR (053 #27 = "Mission"), mnu061 Y, mnu069 R.
    - Each is re-encoded as BC3 into its own block (no larger than the BC7 / BC3 it replaces), so nothing else in the
      file moves.
    - A label touching the key's frame (the framed R) falls back to the key's middle.
    - Shift / Enter / Space / Backspace are drawn as symbols (⇧ ↵ ␣ ⌫) instead of words that shrank to fit.
    - Text 18 % larger.
    - Not done: the tutorial images (tutorial_gb/, English only in the Xbox pack) and font_icon.
- [ ] T238 (2026-10-23) **Session log: keyboard / mouse / icons - what was tried, what failed, what the user still has to
  check** (complements T230-T236).
  - Done but not written above:
    - Mouse camera "Siempre" (xcde.ini mouse_look = 2, dd37e17): the cursor is captured in the focused game window.
      F1 / Alt+Tab free it; moving the mouse over the game captures it again. Launcher combo No / right button /
      Always.
    - Launcher crash on the Controls tab without a controller (1748b87). "Button icons: Automatic" resolved to
      the keyboard (4), and the missing-pack warning read k_icon_mod[ic - 2] past its 2 entries. It now warns for
      Xbox / PS only.
  - Dead ends (kept so nobody repeats them):
    - The arts palette cursor, first search (XCDE_DELTAFIND +1 / +1 / -1 / +1): the single survivor 0x70012dde0f was
      audio sample memory. The real cursor wraps (centre -> right -> left), so a pattern (XCDE_DELTAFIND_PAT=ABCBCBCB)
      found it.
    - Writing the palette cursor (+0x1c8) doesn't move the game's selection. The arts macro presses the d-pad instead.
    - Mouse camera through the right stick, linear (T230): small moves lost in the game's dead zone (~15 %), big ones
      flattened by its curve.
      - The curve inverted + carry-over (243f47c) made a pixel a fixed turn, but a flick queued up behind the stick's
        top speed (~0.07 rad / frame), so "right, then up" waited.
      - Replaced by the direct camera (09ba5c9).
    - The camera angle first found (0x7204cadd7c) was a stack temporary: the atan2 in f_7000861000 called from
      f_70008292a0 (a function that reads / sends the camera's values). Writing it did nothing. The real state is the
      camera object 0x7000b381f0 +0x1f0 / +0x1f8.
    - Stick values beyond +-32767 (XCDE_RX_RAW): up to ~2x faster to the right only; 3-4x slows down or stops; left
      stays at 1x. Not usable.
    - Speed constant search (XCDE_FVALFIND 2.06 / 118 / 0.0688...): only code bytes and an unrelated rodata value.
    - kbicons, first build:
      - text invisible: the label colour was read after it was erased;
      - button.wilay assumed in the plain atlases' cell order (it starts with the d-pad);
      - windows.h's `far` macro;
      - the screens' files are LAGP, not LAHD.
  - Still to be checked by the user (only measured / simulated here):
    - the direct mouse camera with a real mouse: sensitivity 50, vertical direction, in battle as well as the field;
    - L2 + L1 / R1 on a real controller (host_test runs skip the combo);
    - arts 1-8 in real battles with full palettes (tested with Shulk's 2 arts + talent).
  - Not done: tutorial_gb/ images and font_icon.wilay (keyboard icons inside text). In-game remapping menu: the user
    dropped it ("forget it").
  - Diagnostics added this session (all env, off by default; runtime/hle/framepace.c unless noted):
    - XCDE_DELTAFIND (+ _RANGE, _PAT): small-value search by deltas / patterns, + pointer and vtable scan of survivors.
    - XCDE_FLOATFIND (+ _PAT u/a/b, _RATIO, _ALL), XCDE_FVALFIND, XCDE_FPOKE, XCDE_FTRACE: float searches, write
      tests, per-frame traces.
    - XCDE_STATESNAP, XCDE_MEMWATCH_*.
    - XCDE_ART_AT (party.c), XCDE_MOUSE_TEST, XCDE_RX_RAW (input.c), XCDE_KBICONS_DUMP (kbicons.c).
- [~] T240 (2026-10-24) **Graphics glitches everywhere / friend's Intel device lost** (session work, diagnostics first):
  - Friend's crash: GPU hang (device lost) in Colony 9 battles, after the game's dynamic resolution drops (896x504 ..
    1208x680 in his log; a fast GPU never drops). Reproduced the drop on the RTX GPU with `XCDE_TEST_GPU_SLOW=15`
    (counter pairs scaled: the game believes the GPU is slow) - no crash, validation layer 0 messages through every
    resolution change; the layer itself hangs at battle start (timeline wait before signal), so battles are unchecked.
    `XCDE_TEST_GPU_SLOW=0.25` = the opposite (a slow GPU keeps 1280x720): bat C for the friend, against bat A (full
    barriers + device-lost trace).
  - Translator: a depth-compare texture flagged integer by key->tex_uint emitted uintBitsToFloat(vec4(...)), which
    does not compile (friend's precompile log, ~10 programs). Shadow compares now stay float. load_walk 3500: ~1,000 px
    of shadow shading on a rock top change (noise band 0.15-0.45 %); 1200 / 2600 identical.
  - User's video: Shulk's hair black for exactly one frame 1.6 s into the lab cutscene (log: compile 0, build waits 0,
    upload 168 MB). Friend's video: one frame of flat blue behind the grass in a cutscene. Not pipelines.
  - Tools: `XCDE_GLITCH_WATCH=1` ([glitch] a texture changed soon after its first upload - possible upload before the
    game finished loading it; 0 on new_game_h to 9000); `XCDE_REC_SIZE=1280x720` / `XCDE_REC_OUT` for the frame
    recorder; `tools/flicker_scan.py` (short local flicker in a recording; found the hair frame in the user's video);
    `XCDE_TRACE_FILE=<substr,..>` (+`_BT`) first read of matching romfs files with the frame.
  - Debugger plan (user: every map and cutscene, no saves): string xrefs in the lifted main - f_7000031540 builds
    "ma%04u", f_70000693b0 "WarpGm%02d%02d", f_7000070d10 registers the bdat tables (landmarklist, EVT_cs, the Event
    Theater MNU_EventTheater_*, gimmickWarplist / gimmickJumplist). Next: LARECOMP_FNPROF_BT on them during a map load
    to find the map-change call, then an env-driven teleporter and event player for an all-maps / all-cutscenes tour
    with the frame recorder + flicker scan.
  - Open (2026-10-24 afternoon): **rare freeze while loading the save** (~3 of ~200 tour boots; slot crash/stall_*.txt):
    the game's main thread waits in nvnSyncWait -> backend_wait_ticket for the async render worker, which never answers;
    another guest thread waits for g_klock. The stall dump lists guest threads only - add the render worker's host
    stack to it, then find what it waits for.
  - **Found (2026-10-24 evening): the first-viewing glitches were not the pipeline wait itself but races it widened**
    (the render worker falls behind the game on a cold driver cache / slow build; cold A/B with the user's GLCache moved
    aside: prelink, texture re-checks every frame and synchronous shader builds all kept them; XCDE_GLITCH_WATCH logged
    a shader sampling a 3D / cube unit that held a 2D texture - black - in the exact glitch frames):
    1. BindProgram recorded the NvnProgram object; the game sets other shaders on it (or finalizes it and a new one gets
       its memory) while the worker still has draws of the old ones -> they drew with the new shaders (faces with other
       textures / black, Reyn's body as his weapon). Fix: objects.c program_freeze, cmdbuf.c records the frozen copy.
    2. Shader code was translated from the game's memory when the translator got to it; a freed / reused blob gave
       "VS translate failed: unknown instruction 0000000000000000" and the content-keyed program stayed failed (its
       draws skipped: Reyn's face gone). 51 times in the 190-cutscene tour. Fix: objects.c code_snapshot at registration.
    3. Texture / sampler pool registrations now apply in command order (exec.c backend_pool_write, XCDE_POOL_IMMEDIATE=1:
       old way).
    4. nvnTextureCompare compared addresses (SavageWindRecomp bc8a374 found the same): now the texture state. The game
       never calls it here (logged), kept for correctness.
    Cold driver, 5 reference scenes (vs01140100 vs01230100 vs01290100 vs02010100 vs05060100), async and synchronous
    builds: p306 (1+2) and p308 (1+2+3): no real glitch left (the scanner's remaining dark hits are motion), 0 failed
    translations, no mismatch but the LUT one below. Warm, the 9 cutscenes that had failed translations (p310): 0
    failed, 0 skipped draws (vs01270100 skipped 363 draws per 2 s before), fps as before or better, no crash.
    5. A masking shader (fs 72c2982800: discard where .r of a screen-space lookup <= a threshold, no colour output)
       samples the game's 64x32x15 RGBA8 3D pattern as 2D: it got the black dummy. Now a 2D copy of slice 0 (what the
       Switch reads), refreshed once a frame (textures.c slice0_copy). Deterministic captures of vs01140100 at 10 frames:
       identical with and without it (nothing visible depended on it there); the mismatch log is now empty.
  - EDS3 measured on the 29,679-variant seed (2026-10-24): dynamic blend / write mask / logic op / a2c / fill would
    leave 29,383 pipelines (-1 %); with dynamic vertex input too 25,030 (-16 %); the floor (shaders + keys) is 8,789 -
    formats, samples and vertex layouts make the variants here. Not worth the renderer rework (the whole list
    precompiles in ~50 s); not done.
  - (Earlier theory) **a draw waiting mid-frame for its pipeline corrupts the rest of that frame** (Reyn's hair dark / his weapon
    over his body, reproduced with XCDE_TEST_SLOW_BUILD=100..150 on vs01230100; a pure 100 ms present hitch does not).
    Wanted outcome (user): a short stutter, never a wrong image. The loading / scene-start holds (vk_prewarm_hold) made
    the game drop cutscenes: tours run with XCDE_LOAD_HOLD_MS=0 XCDE_REG_HOLD=0 until it is redesigned.

## Session 2026-10-25 - after the 48-item review (pending)
- [x] T241 (c262fe4) **Pipeline budget by RAM** (b82a198 has a fixed XCDE_PIPE_BUDGET=8000): every PC needs a cap (pipelines pile up
  with 32 GB too), only its size changes - ~8000 with 8 GB, ~16000 with 16 GB or more (~0.32 MB each). Keep the env
  override. None of the 20 reviewed repos evicts pipelines (emulators / DXVK keep them all; native games free a level's
  on unload): our cost per pipeline is what is unusual.
- [x] T242 (c262fe4: GPL library eviction; the rest is the driver - T246) **Why ~0.32 MB per pipeline** (p344 soak: +656 pipelines = +208 MB): measure the share of the optimized whole
  pipeline, the fast-linked one and the GPL libraries (never freed). If the libraries dominate: free a variant's
  libraries once its optimized pipeline replaced the link (rebuild = whole from the driver cache). Data:
  <work dir>/soak_p346 [mem] lines against the "pipelines N" count.
- [x] T243 (2e6d580) **D16 depth compare** (p348 log): fs 72c2895f00 compares against a 1024x1024 D16 shadow map in field, battle
  and cutscenes. Maxwell rounds the reference to 16 bits first (LASRecomp 6283599); NVIDIA matches, AMD / Intel may
  not (dark streaks on lit surfaces). Fix = round the reference in the shader when the bound texture is D16 (needs the
  format per slot at draw time, e.g. a bit in the tsize data); prove on NVIDIA that the image is identical.
- [ ] T244 **Vega 8 / min-spec tests** (need the hardware or the friend's PC): heap import window (~256 MB) instead of the
  whole 3.2 GB heap; what to do when the device-local carve-out fills (memory budget is now reported in [mem]); T243
  result on AMD.
- [ ] T245 Remaining of item 48 (~30 translator / NVN details without symptoms in XCDE): measured so far - packaged
  layout block height (never set), 16-bit packed formats RGB5A1 / RGBA4 / RGB565 (never used), EarlyZ (handled), D16
  (T243).
- [ ] T246 **Driver memory growth** (T242 follow-up): what still grows in long sessions is the NVIDIA driver's own
  memory (outside all Win32 heaps; fills while pipelines compile and is not returned when they are destroyed). Lever:
  compile less on low-RAM PCs (prewarm volume, eviction churn: an evicted pipeline compiled again grows it too).
  Measure the AMD / Intel drivers on real hardware before tuning.
