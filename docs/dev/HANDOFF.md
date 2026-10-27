# HANDOFF — Monado

## 0000000000000000000. FINAL BUILD 6bfa524 + MEMORY WORK (2026-10-25 ~10:40)
- **build/xcde.exe, build/xcde_launcher.exe, build/tester/ (exe, launcher, data/variants_seed.bin 30,338) replaced:**
  clean worktree build of 6bfa524 (<work dir>/wt_final), AVX scan 0 for both. load_walk vs p354: prefix 2021, 1200 /
  2600 / 3000 / 6000 identical, 4317 noise. Backups: <work dir>/xcde_f0d332c.exe, xcde_launcher_f0d332c.exe; this one
  <work dir>/xcde_6bfa524.exe. Players: run "Precompilar shaders" once (new seed; T243 changed the shadow shaders).
- New since the 48-item entry below: b82a198 pipeline eviction, c262fe4 T241 budget by RAM + T242 GPL library eviction
  (reference-counted: NVIDIA crashes if a fast-linked pipeline's library is destroyed), 2e6d580 T243 D16 compare
  reference rounding (**new deterministic baseline: compare frame hashes against p354 or later**), 6bfa524 memmap
  heap summary.
- **Memory findings (soaks over the battle tour, <work dir>/soak*):** ~3.2 GB is the guest heap (fixed). GPL
  libraries were the growth we own (+465 MB / 35 min vs +63 MB without GPL) - now capped. Pipelines themselves cost
  ~0.025 MB. The rest of the growth is the NVIDIA driver's own memory (outside every Win32 heap: one block filled
  338 -> 1023 MB while ~7,000 pipelines compiled at boot, another 160 -> 497 MB over 30 min); our malloc stays ~250 MB.
  It grows only with new compiles - nothing to free from our side; fewer compiles is the only lever (T246).
  Integrated GPUs already run without the vertex cache (T169) and below 12 GB RAM get the small budgets.
- Running when this was written: soak_friend (p355, 4 cores, 8 GB budgets, no vertex cache: the friend's PC
  simulated - read working_mb in its mem.tsv) and soakl_p353_8g.
- Pending: T244 (Vega 8 / friend's PC: heap import window, carve-out full, T243 on AMD), T245 (item-48 details),
  T246 (driver memory growth: compile less on low-RAM PCs; measure the AMD driver).
- **Coverage tours (2026-10-25, final exe, 8317cd2):** tour events now set `story <scenario_flag>` first (that was every
  "never started"). Future Connected (fc_all, 11 maps): 11/11, no crash / stall, scanner hits = loading screens and
  motion. Menus (routes/menu_all.txt): 32 captures, all right (black save thumbnails = the 10-19 save's own .tmb; new
  saves get real ones). The 16 cutscenes that never started in the old events tour: 16/16 now. Heart-to-Hearts
  (h2h_all, 65): 56 played (the tour's A presses skip the text: ~3 s each, ending in "Affinity Coin!"), 0 crashes;
  8 never start (0501e2 0601e1 0601e3 1202e1-e3 1401e3 1501e2) - also with the dl_100 save, the kizuna flag or the
  Event Theater position: a condition of their own (affinity?), not a renderer issue. Still not run with story fix:
  the other 301 side events (tests/tours/sev_other.txt) and the full 190-cutscene tour.

## 000000000000000000. THE 48-ITEM LIST WORKED THROUGH (2026-10-25 ~07:30; build/xcde.exe = f0d332c, unchanged)
- Commits b78be40 (kernel / translator / saves / audio / crash handlers / budget / ini / launcher) and f2b801b (SPIR-V
  pack). Verified on test exes: load_walk equivalence p343 vs p332 (identical prefix 2021 frames, 1200/2600/3000
  identical, 4317/6000 inside the T124 noise measured with self-baselines p330 vs p330b), save tests, audio runs.
  Newest test exe: build/xcde_p345.exe (everything). build/xcde.exe and build/xcde_launcher.exe NOT replaced yet:
  next final build = worktree of f2b801b + seed merge (below) + AVX scan + backup, then rebuild the launcher
  (tools/launcher/build.sh: new "Crear reporte" button and dead-zone slider).
- **Done / closed (44 of 48; the list is in the 2026-10-25 chat and the CHECK triage (not part of the public copy), the snapshot before it):**
  - Kernel condvar order, CAS address arbiter, regions 16384, pthread_once worker start; static SSY/PBK/PCNT stacks
    (3002/3006 programs; equivalence above). BRX / divergent BAR / FMZ: 0 programs in XCDE. SHFL in VS: 1 program,
    only seen in the precompile scan - deferred to the RenderDoc phase. SetDepthClamp, WriteTexels partial/strided:
    never called. Packaged-layout block height check: XC never sets it (0 log lines).
  - Saves: journal (save_N.journal, dropped on Commit, restored on the next mount: torn-save test passed), backups
    save/backup/save_N_<date> (newest 5) at the session start. XCDE_SAVE_JOURNAL_OFF / XCDE_SAVE_BACKUPS=0.
  - Audio: audout/audren threads HIGHEST (2 cores, 5 min, paired: 7 underruns vs 63; LARECOMP_AUDIO_PRIO=0 off);
    "[audout] N underruns" counter. XCDE uses audout, not the audio renderer (reverb cost item n/a).
  - Validation layer (LARECOMP_VK_VALIDATION=1 + VK_ADD_LAYER_PATH=C:\msys64\ucrt64\bin): 0 real messages over
    boot + load + walk to frame 2055; past that the LAYER hangs in its timeline-semaphore tracking (not us).
  - D32S8 (forced with LARECOMP_VK_D24=0, as AMD/Intel get): field shadows pixel-identical to D24 - no acne, no fix.
  - Already present: Intel trailing empty colour slots, pipeline fallback (link -> whole -> skip draw), minimize,
    quick exit, getenv caches (env_cache.h; added to audio.c), 256 MB default stacks, async worker ordering (T240).
  - Measured not worth it: native memcpy (no guest function > 1 % of 0.24 busy cores), per-thread pipeline cache,
    spin-before-sleep.
  - Paths with accents and commas: boots and loads from "<work dir>\prueba á, ñ". Characters outside the ANSI code
    page (Cyrillic / CJK user names) would still need a UTF-8 manifest.
  - SPIR-V cache as one file: a cold open of a loose .spv costs ~3.7 ms (Defender), 7,000 at boot = +25 s after each
    reboot / definition update. cache/spirv.pack + spirv.idx (multi-process safe, migrates loose files on hit). The
    user's cache/ already holds a 51 MB pack from a p345 profiling run (byte-identical entries: harmless). The loose
    cache/spirv folder is 8.8 GB (110,580 files, ~2/3 stale variants): can go once the user's exe has the pack.
- **Open:**
  - 21 soak: baseline p328 (<work dir>/soak_base2) finished the tour (153 battles, 2 h 19 min) but private memory
    grew 6.1 -> 11.4 GB while textures stayed ~800 MB and pipelines grew 5,680 -> 21,081 (never destroyed). Soak of
    p344 with LARECOMP_VK_PROF ([mem] lines) running in <work dir>/soak_p344 (started 06:50): correlate private MB
    with the pipeline count, then decide on pipeline eviction (LRU, destroyed once the GPU is past them) - the 8 GB
    min-spec PC can't afford +5 GB.
  - 18 loading staging peak: read it from the same [mem] lines.
  - 13 heap import window (~256 MB) for the iGPU: needs the Vega 8 to test.
  - 48 ~35 translator / NVN details without symptoms: only the packaged-layout check measured so far.
- **Lessons:** NVIDIA's driver shader cache is per exe NAME - a new test exe boots with cold pipeline builds (2 cores:
  ~40 s later to the title); compare boot times only between runs of the same exe name. Deterministic drives turn
  the async worker off (XCDE_ASYNC_RENDER has no effect there). Test runs in the repo share cache/ with the player:
  pass XCDE_SPIRV_LOOSE=1 or run from a separate folder (<work dir>/packtest*) when a cache format changes.
- Seed merge still pending: `python tools/merge_variants.py data/variants_seed.bin data/variants_seed.bin
  <work dir>/tb_battle/slot*/cache/variants.bin`; tests/tours/battle_types.txt ma0601_e15 still to fix or drop.

## 00000000000000000. OTHER-RECOMP REVIEW + KERNEL FIXES IN TEST (2026-10-25 ~01:30; build/xcde.exe = f0d332c, unchanged)
- **Review of 20 public recomps / ports done (notes only):** every commit + issue of LASRecomp, MacNativeGames,
  SpartanPort, issn_pc, axylpup shadPS4, dod3, WindowSmash, ssbu-recomp, PokeZ-A, uDPR, letsgo, AstralChain-PC,
  SavageWind, ACNH, Metroid Dread, AC-Recomp, B2recomp (cloned 10-24 to <work dir>/repos/B2recomp).
  - Raw notes: <work dir>/research/notes.md (867 entries, 297 marked "CHECK"); commits/issues dumps next to it.
  - docs/RECOMP_KNOWLEDGE.md (commit c79056d): general, by topic, for ANY recomp. Keep it whole (XC2/XC3/XCX may need
    items XCDE does not).
  - the CHECK triage (not part of the public copy) (NOT committed, partial): verdict per CHECK line. The final count, from the verdict script
    $TEMP/fmat/verd.py (the file on disk still shows 110 "M" - regenerate with the script once the 2nd block of
    s(...) lines is in it: that Edit failed when the permission classifier was down; the lines are in the chat of
    2026-10-25): A 42 (~20 distinct), done 77, B 141, N 37.
  - User request (2026-10-25): two docs - RECOMP_KNOWLEDGE.md (general) and docs/LESSONS_FOR_XC2.md (direct
    heritage: what carries to XC2/XC3/XCX and what does not). LESSONS_FOR_XC2 not updated yet with this review.
- **Battle tour finished** (<work dir>/tb_battle, p320, dl_100 save): 306/307 done, 659 new variants
  (seed 29,679 -> 30,338: merge with `python tools/merge_variants.py data/variants_seed.bin data/variants_seed.bin
  <work dir>/tb_battle/slot*/cache/variants.bin`, not done yet, then a new final exe). 8,957 flicker-scanner hits =
  battle effects (29 samples checked, no glitch). The 1 timeout ma0601_e15 is a TOUR DATA bug: its warp
  (-7626 -2608 -1660) is far outside the map, the party lands under the world and the battle AI loops (render worker
  idle, main thread in f_70000cfef0, reproduced 2/2 with p328). Fix or drop that line in tests/tours/battle_types.txt.
- **Code changes (uncommitted, in build/xcde_p330.exe, NOT TESTED YET):**
  - runtime/kernel.c svc_wait_process_wide_key: condvar key set BEFORE releasing the mutex (Horizon order; a signal
    in the gap was lost - PokeZ-A 52359cc).
  - runtime/kernel.c WaitForAddress (decrement) / SignalToAddress (increment, modify-if-equal): compare-and-swap
    instead of load + store (LASRecomp 1144aea).
  - runtime/kernel.c memory-region table 1024 -> 16384 (MAX_REGIONS), log at 1024 / 4096 / 12000.
  - runtime/nvn/vulkan/exec.c backend_async(): pthread_once (two first callers could start two render workers,
    LASRecomp bd76094).
  - runtime/nvn/cmdbuf.c nvnCommandBufferSetDepthClamp: logs "[nvn] SetDepthClamp(n) called (not applied)" once -
    to learn whether XC uses it before implementing (implementing changes pipeline keys -> seed).
- **Next (user: "do and check EVERYTHING, nothing may break"; 1 game slot reserved for a 2-3 h soak + 3 for tests):**
  1. Soak 2-3 h: tools/soak.py <exe> <work dir> [every=2] (one process, ~150 battles across maps, mem.tsv every
     30 s). The first try (<work dir>/soak_base, p328) died after 150 s when the Claude session restarted: launch it
     DETACHED (Start-Process), not run_in_background. Baseline p328, then p330.
  2. Test p330: mixed tour (6 battles + 6 cutscenes) on 3 slots: all done, no new stalls, captures equal; grep the
     logs for SetDepthClamp.
  3. Then the list (docs/RECOMP_KNOWLEDGE.md section 1, chat 2026-10-25): translator SSY/PBK stacks as scalars, BRX
     jump tables, divergent compute BAR, FMZ, SHFL in VS; Vega 8 (heap import window, VK_EXT_memory_budget, D24->D32
     depth bias); atomic saves; audio/video EOS test; validation-layer run; thread priorities on 4 cores.
- The permission classifier ("auto mode") failed repeatedly on 2026-10-25: in auto mode no shell command runs while it
  is down; normal mode works.

## 0000000000000000. FIRST-VIEWING GLITCHES FIXED + FULL VARIANT SEED (2026-10-24 ~20:00; build/xcde.exe = f0d332c)
- build/xcde.exe, build/xcde_launcher.exe, build/tester/: clean worktree build of f0d332c (AVX scan 0). Backup
  <work dir>/xcde_f0d332c.exe; 63f7bf6 before it. tester/data/variants_seed.bin: the new seed (copy it over the
  friend's data/variants_seed.bin, then "Precompilar shaders" again).
- 74677c3: the first-viewing glitches (Shulk's black hair, faces with other textures, Reyn's face gone / body as his
  weapon) were races with the render worker when it lags (cold driver cache): BindProgram now records a frozen copy of
  the shaders, shader code is copied at registration (translations no longer read freed memory and fail), pool
  registrations apply in command order. Cold A/B on 5 reference scenes: no real glitch left. tasks.md T240.
- f0d332c: data/variants_seed.bin 10,175 -> 29,679 variants (all tours). --precompile: 29,616/29,616 pipelines, 141 s
  total here, ~1.1 GB peak.
- Open: a fixed shader samples the 64x32x15 3D LUT as 2D every frame (black dummy) - find what it draws; coverage
  tours still missing: sv events, Heart-to-Hearts, battles, Future Connected, menus.

## 000000000000000. DEBUGGER TOUR + INTEL FIXES (2026-10-24 ~08:00; build/xcde.exe = 63f7bf6)
- build/xcde.exe, build/xcde_launcher.exe, build/tester/: clean worktree build of 63f7bf6 (AVX scan 0; load_walk
  1200 / 2600 byte-identical to the test exe p256). New since bcc8d6a: defined dynamic state at every command buffer
  start + blits only where the format supports them (9318540: the Intel D32S8 depth pyramid blit is skipped and logged
  as "[vk] blit ... not supported"), finalized textures leave the texture pools (8dcc32b). Backup
  <work dir>/xcde_63f7bf6.exe; bcc8d6a before it.
- Debugger: XCDE_WARP / XCDE_EVENT / XCDE_TOUR=<file> (runtime/hle/party.c), tours from tools/tour_gen.py in
  tests/tours (events_all: 190 cutscenes, maps_all: 219 landmarks). XCDE_GLITCH_WATCH=1 also logs draws that sample an
  empty texture pool slot (the black-hair hypothesis: a slot finalized while still drawn).

## 00000000000000. GLITCH HUNT + FRIEND'S INTEL CRASH (2026-10-24 ~02:10; build/xcde.exe = bcc8d6a)
- build/xcde.exe, build/xcde_launcher.exe, build/tester/: clean worktree build of bcc8d6a (AVX scan 0). Adds the
  T240 shadow-compare translator fix and the diagnostics (tasks.md T240). load_walk 1200 identical to 4c8dd7b.
  Previous: <work dir>/xcde_bcc8d6a.exe is this one; 4c8dd7b before it.
- tester has bat C (`XCDE_TEST_GPU_SLOW=0.25`: no dynamic resolution drop) next to bat A (full barriers): the
  friend's battle crash happens after the resolution drops; whichever bat stops it names the cause.
- Next: the debugger (teleporter to every map, event player for every cutscene) for an automatic tour with the frame
  recorder at 720p + tools/flicker_scan.py (recordings deleted once scanned). Leads in tasks.md T240.

## 0000000000000. LOW-END / NON-NVIDIA WORK (2026-10-23 ~14:15, party mod session; build/xcde.exe = 4c8dd7b)
- The plan, its results and what each item still needs are in docs/spec_lowend_gpu.md. The status is at the end of
  that file.
- build/xcde.exe, build/xcde_launcher.exe and build/tester/: clean worktree build of 4c8dd7b (AVX scan 0; launcher dd37e17). Keyboard icons also in the screens' single glyphs (Mission ZR). T236: direct mouse camera (yaw / pitch written). T236: mouse camera 1:1 (the game's stick dead zone + curve inverted). Mouse camera 'Siempre' (mouse_look = 2). Keyboard icons cached in cache/kbicons per set of bindings. T234: keyboard button icons drawn from the bindings (launcher "Iconos de botones: Teclado" / auto without a controller). T232: launcher "Iconos de botones" (the user installs the GameBanana packs in mods/icons_xbox, mods/icons_playstation). T230: keyboard + mouse MMO layout (1-8 arts, T talent, Z / X party, right button camera, second key, mouse bindable; the launcher moves an older xcde.ini to the new keyboard layout), L2 + L1 / R1 party switch. Before that, 53fb5a3: T228: exact camera motion where the game velocity only repeats it. Frame generation also with DLSS; launcher "Frame generation in cutscenes only". Also: cutscene detection + "Cinemáticas" option + FPS 60 + FG on 60 Hz = FG only in cutscenes. Also the battle-hitch sampler (XCDE_HITCH_SAMPLE, off by default; bat in the repo root). Also: T205 strips after a defeat (mirror moved 32 KB) fixed by retiring overlapped mirrors; V-Sync at 30 fps on 60 Hz presents each frame twice (flat 33.3 ms), T205 mirror overlap refresh. It adds the T226 translator fix (36 programs that never translated now draw) and the FSR 3 frame generation HUD-less frame (the HUD no longer smears; needs the user's eye check). Tests run:
  - captures within the noise band;
  - save list thumbnails right.

  Previous exes: <work dir>/xcde_53fb5a3.exe (if kept), xcde_e78c31d.exe, xcde_cfd6813.exe, xcde_afeed1c.exe, xcde_91d9d2a.exe, xcde_0c94617.exe, xcde_9d4c865.exe, xcde_d626958.exe, xcde_49bbefc.exe, xcde_fde082c.exe, xcde_before_fde082c.exe.
- The friend (Intel Core Ultra 5 125U) tests with two bats in build/tester, to tell the cause of the black
  mountains:
  - A: full barriers;
  - B: feedback snapshots.

  Both add the device-lost trace.
- Next:
  - T226 (general fixes from the other recomps, being checked);
  - T224 (cutscenes at 30 / ponytail).

## 000000000000. OPEN - WHAT IS STILL TO FIX (2026-10-22 ~19:40, party mod session; build/xcde.exe = b23fdb1)
1. ~~HUD ghost over the menu with DLSS~~ - fixed (T216, tmp_hud.frag). Note for any DLSS / HUD test: reproduce in real time
   with XCDE_PRESENT_ALWAYS=1 (hidden deterministic runs present only the captured frames).
2. ~~Save / load list thumbnails blank~~ - fixed (T181, exec.c slot_thumb_fix; tasks.md T181).
3. ~~Area-entry freeze~~ - mostly fixed (T218).
   - Cause: registrations past 256 were dropped from the prewarm. The area's first frame went from ~1.2-1.5 s to
     ~0.2 s on GPL GPUs; without GPL it went from 1.5 to 1.0 s with the same memory.
   - The rest are variants never seen (data/variants_seed.bin covers them for new players; grow it with
     tools/merge_variants.py from real play).
4. **Fix 2 for PCs without pipeline libraries / iGPUs (min spec 3200G + Vega 8, 8 GB)**
   - What exists: the recorded variants are built whole while the area loads (T163, batch capped by RAM - T218), and
     cache/vk_pipelines.bin keeps them across sessions.
   - What is missing: a measurement on such a PC. A friend's Core Ultra 5 125H (Intel Arc iGPU, 16 GB) can provide
     it: build/last_game.log, line "[vk] graphics pipeline library" plus the [hitch] lines.
   - If that GPU has GPL with fast linking, consider prebuild_libs_on() for integrated GPUs with 16 GB (today it is
     off on every iGPU).
5. **T205 faces as strips**: fix in cb3918c (T214: any new vertex mirror retires every mirror it overlaps); needs a
   long session to confirm - watch the "[vk] mirror ... retired" log lines if it shows again.
6. ~~Build scripts~~ - done: hle/party is in scripts/build_rt_gfx.sh + link_gfx.sh (build/rt/hle_party.o), the include
   in input.c is gone. A partial build of another object still links the existing hle_party.o.
7. **Other frame-count logic at 60 fps** (T210 found one: follower move restart). Method if the user reports
   something that only happens at 60: same scene at 30 vs 60 fps, compare state / positions (XCDE_PARTY_PROBE style).

## 00000000000. TWO CLAUDE SESSIONS IN PARALLEL (2026-10-21 ~15:30, user's decision) - READ FIRST
Two accounts work at the same time in this same checkout. To not step on each other:
- **Session "graphics" (account 1):** T205 faces drawn as vertical strips (fix in exec.c xsh_retire_overlaps, being
  verified), cutscenes that feel 30 fps at FPS 60, the remaining pipeline-build stutters (slow builds bypassing the
  pipeline-library fast link), then the graphics options (docs/graphics_options_research.md).
  Owns: runtime/nvn/** (exec.c, device.c, textures.c, shaders.c, precompile.c, temporal.c, dlss.cpp), runtime/hle/
  framepace.c, runtime/hle/vi.c, tools/launcher (graphics tab), scripts/build_rt_gfx.sh.
- **Session "party mod" (account 2):** Xenoblade 3-style character switching (docs/plan_party_switch.md,
  docs/party_switch_research.md). Owns: the new mod files it creates (e.g. runtime/hle/party*.c), runtime/diag/diag.c
  tools (XCDE_FIND / XCDE_POKE), docs/party_switch_*.md, the launcher's controls / gameplay additions.
  If it needs a change in a file the other session owns, write the request below ("Requests") instead.
- **Saves (read-only, on E:):** `<work dir>/saves/faces_1515` (Fiora + Shulk, Colony 9, faces broken before T205 -
  both sessions may use it), `<work dir>/saves/cutscene_1520` (Shulk alone, walk forward = a cutscene; graphics
  session), `<work dir>/saves/user_20261021_1520` (full copy of the user's save folder). Every run copies the save
  into its own build/save_<run name> (rtrun.sh / drive_env.sh), so runs never touch each other or the user's save/.
  Load with tests/routes/load_a.txt (loads the newest = the only slot in those folders).
- **Builds:** always `XCDE_EXE=build/<own name>.exe scripts/build_rt_gfx.sh <objects>` (graphics: build/xcde_g*.exe;
  party mod: build/xcde_p*.exe). Without XCDE_EXE the script kills every running xcde.exe. Objects are written to a
  temp file and renamed (cf7ea2f), so a parallel link never reads half an object; still, compile only what you changed.
  **build/xcde.exe** (what the user plays): only replaced with a verified build; note it here with the commit.
- **Game runs:** at most 3 at once in total (user's rule): graphics session up to 2, party mod 1. None while the user
  plays (check `tasklist | grep -i xcde` for an xcde.exe started by the launcher).
- **Git:** both commit to main; `git add` only your own files (never `git add -A`); if you change a shared header
  (settings.h, vk.h), rebuild everything and say so here. Task numbers: graphics uses T205+ odd, party mod T206+ even.
- **build/xcde.exe log:** 2026-10-21 ~23:58 party mod session: cb3918c (T212, T214 incl. T205 redo; clean worktree; smoke-tested).
- **2026-10-21 ~22:30 (user): the shader-cache-for-every-PC + pipeline-link stutter task moves to the other session** - read docs/handoff_shader_pipeline.md (root cause, fix, file ownership for it).
- **Requests between sessions:** (party mod -> graphics) please add `hle/party` to RT in scripts/build_rt_gfx.sh and
  `build/rt/hle_party.o` to scripts/link_gfx.sh; then the party mod drops the `#include "party.c"` at the end of
  runtime/hle/input.c (a stopgap so it builds without touching your script).
- **Request (party mod -> graphics), 2026-10-21 ~22:20: T205 again** - the user's shot (Fallen Arm, Trümmerstrand
  warp, build/xcde.exe 9d41615): Shulk's face drawn as a vertical striped strip. build/last_game.log (22:11) shows
  overlapping **transform feedback** mirrors: 7265f79c00 +61248 covers 7265f7c000 +288 and 7265f7c300 +61472.
  xsh_retire_overlaps (T205) only runs for store mirrors (xsh_stored); the transform-feedback path (the "[vk]
  transform feedback mirror" log, exec.c ~3850) adds a mirror without retiring the ones it overlaps, so the same
  stale-vertices case remains there. -> Fixed by the party mod session in cb3918c (T214), the graphics session agreed.
- **build/xcde.exe replaced, 2026-10-22 ~18:50 (party mod session)**: clean worktree build of 6939001 - **no AVX-512 / AVX2
  any more**. vma.o had been built by hand for the build PC's CPU (Zen 5: AVX-512), so xcde.exe carried 189 AVX-512
  instructions; the launcher had no -march at all. A friend's Core Ultra 5 125H crashed with 0xC000001D. Both are now
  built for x86-64-v2 (build rules for vma / paths in build_rt_gfx.sh). Check any new exe with:
  `objdump -d build/xcde.exe | grep -cE "zmm|%k[0-7]|ymm"` (must be 0).
  Fixed exe + launcher for the user's friend: build/tester/. Previous: <work dir>/xcde_427bc76.exe.
- **build/xcde.exe replaced, 2026-10-22 ~18:00 (party mod session)**: clean worktree build of 427bc76 (T194 laptop GPU
  exports, T195 canonical keys, P-cores on hybrid Intel, texture / pipeline counts in the stats line). Smoke-tested
  (fallen_arm load + switch). Previous: <work dir>/xcde_874b557.exe. <portable copy> (the user's laptop copy) still has
  874b557 - the user is testing it: leave it until they say.
  Optimization review (other recomps / emulators), measured here:
  - XCDE has no ASTC textures (all game textures ~360 MB): ASTC -> BC7 and texture eviction are moot.
  - EDS3 / vertex-input dynamic state would cut pipelines by 1 % / 10 %.
  - Push descriptors: ~1.2 ms of ~5.8 ms of render-thread time per frame, one push set per layout.
  - Background compiles in play: no frame drops at 4 cores.
  - GPU hang: already a fatal error with diagnostics.
  - Still open: the iGPU mode (T193) - needs an iGPU (the friend's Core Ultra log).
- **build/xcde.exe replaced, 2026-10-22 ~17:20 (party mod session)**: clean worktree build of 874b557 (T218 prewarm
  fix, hle/party own object, seed 10,175). Smoke-tested (fallen_arm load + switch). Previous: <work dir>/xcde_eb53466.exe.
  Portable copy for another PC: <portable copy> (scripts/make_dist.sh; runs without msys64).
- **build/xcde.exe replaced, 2026-10-22 ~16:30 (party mod session)**: clean worktree build of eb53466 (T216 HUD ghost +
  T181 thumbnails). Smoke-tested: real-time load list with all 4 thumbnails, plus fallen_arm load into the field.
  The previous exe (cb3918c) is kept at <work dir>/xcde_cb3918c.exe.
- **build/xcde.exe replaced by the party mod session, 2026-10-21 ~21:26 (user: "put them in now, as the final game")**:
  built from HEAD 1502860 in a clean worktree (<work dir>/wt_final: your committed code only, none of your uncommitted
  exec.c / shaders.c / temporal.c work) = fea8e0e + party mod T206 + T208 + T210. Smoke-tested (fallen_arm load, two
  switches). Previous exe kept at <work dir>/xcde_fea8e0e_backup.exe. The launcher will re-precompile (exe changed).
- **Lag the user saw with the 19:29 xcde.exe (~21:20)**: its run linked 731 pipelines on loading a save ("gpl cached 0",
  24 s of link time, 2 s freezes) while a p* exe session just before had thousands of cache hits. cache/vk_pipelines.bin
  is one file for every exe: the last process to exit saves its in-memory cache over it, so a run of another build
  (test exes with different shader code) leaves a cache the user's build misses. Suggest: test runs (LARECOMP_HIDDEN /
  deterministic) don't save the user's cache, or one cache file per exe build.
- **FYI (party mod session), 2026-10-21 ~21:15 - T210 done (committed): field followers no longer fall behind at fps = 60.**
  Cause: a frame-count threshold tuned for 30 fps - a follower restarts its "follow while running" move once its
  movement component (+0x200) counted more than 9 frames of a condition (f_7000443760 / f_70004439f0, `cmp w8, #9`);
  at 60 that tripped every ~11 frames, so they never got past a walk (2 -> 17.5 m behind in 200 frames). Fix: two
  patches in games/xcde/patches.py (T210) call xcde_frames_gt(9) (runtime/hle/party.c: same time at the current
  rate - x2 at 60, measured above 60). **Shared files touched:** generated/main/main_097.c (hand-applied,
  byte-identical to what tools/lifter/gen.py now emits for those patches) and build/obj/main/main_097.o rebuilt; it needs
  xcde_frames_gt, which is in build/rt/hle_input.o (runtime/hle/party.c is included by input.c). Measured: fallen_arm
  save running straight, 60 fps: followers ~6.8 m behind like at 30 fps; 30 fps: positions identical to before.
  Other frame-count logic may exist (the user asked); the same method finds it (compare a scene at 30 and 60 fps).
- **FYI (party mod session) - T208: runtime/services/fs.c never closed the game's files** (no on_close on IFile /
  IDirectory): on Windows an open file can't be deleted, so the game's DeleteFile of a save it had read failed and it
  aborted (nn::fs::DeleteFile -> svcBreak) - it happens when a save from another game version is saved over (it is
  deleted and created at the new size; reproduced with build/xcde.exe on <work dir>/saves/dl_100). Fixed (on_close
  closes the fd / DIR). Committed with the party mod (user: merge it).

## 00000000000. START HERE — session 15 (2026-10-21 ~05:40, second account)
Same standing rules as session 14 below. Done this session (all committed, build/xcde.exe = HEAD, DLLs copied by
scripts/copy_upscaler_dlls.sh): T200 entering-area frame drops (draws waited 98 ms for the translator lock behind the
prewarm queue; `[build-wait]` log lines explain any wait > 8 ms), T201 FSR 3.1 + DLSS (temporal.c / dlss.cpp,
tasks.md has the details and limits), T202 F1 in-game options menu (runtime/ui/menu_vk.cpp), T203 mods folder +
launcher Mods tab, T204 FSR 3 frame generation (DLSS-G not done). **Task C research started:
docs/party_switch_research.md** (party order at save-data +0x1526d8; a save edited to Reyn-first loads with Reyn as
the controlled leader; next: fix XCDE_WATCH, find the runtime party object). Known: the HUD is part of the upscalers' input (a
pre-HUD snapshot of the window image would give a reactive mask / clean FG); motion vectors are camera-only.
perf4k.sh runs came out capped at 60 fps (cause not checked) - compare GPU ms, not fps.

## 0000000000. START HERE — session 14 (written 2026-10-21 ~01:10, for another account)
Work in English, answer the user briefly (they write Spanish). Never stop to ask between steps. One chat only. Max 3
game runs at once; never run the game while the user plays. Bulky data on <work dir>. Commit verified work.
**State of main:** 4K uncapped meadow 166 fps avg / 129 worst (frame lag, VRAM vertex mirrors T175/T197, splits at pass
boundaries); T198 option to turn off the game's own AA / TMAA / motion blur (lib_nx.ini served edited by the virtual
romfs; the user's xcde.ini has `game_blur = 0`); build/xcde.exe = bedef68. Backup: git tag backup-before-perf2,
<work dir>\backup\2026-10-20_e8ac693.
**Uncommitted in the tree (session 14, being finished by the first account - check `git status`):** frame pacing at
60 fps on the user's 60 Hz monitor (user: "feels laggy, Afterburner frametime is flat"): (a) platform
`plat_display_vblank` (DWM timing, windows.c), (b) framepace.c `vblank_wait` (frame ends locked to display vblanks
when fps divides the refresh; XCDE_VBLANK_LOCK=0 off), (c) objects.c frame lag only when fps > 60 / unlimited (it
added a frame of latency at 60 for nothing), (d) device.c XCDE_LOG_PHASE diagnostic. (b) not yet shown to help (the
DWM-based metric may be unreliable); (c) is sound. Finish or drop (b) with a better measurement (e.g. PresentMon if
the user allows a download, or VK_GOOGLE_display_timing / DXGI frame statistics).
Also reported by the user (video <local file>
<work dir>\vid1021): a graphics bug in Colony 9 at night (not yet located in the frames - ask the user for the second
it happens) and grass looking noisy now that TMAA is off (expected: TMAA was the game's temporal AA; options: SMAA
already exists, or the FSR 3 / DLSS AA mode below = the real fix).

### Task A: DLSS 4 (SR + frame generation) and FSR 3.1 (upscaling + frame generation), user-selectable
Already done / known:
- SDKs downloaded and signature-checked: <work dir>\sdk\ffx (FidelityFX SDK v1.1.4 = last with Vulkan; FSR 3.1.4;
  bin\amd_fidelityfx_vk.dll, C "ffx-api" headers ffx-api\include\ffx_api\{ffx_api.h,ffx_upscale.h,
  ffx_framegeneration.h,vk\ffx_api_vk.h}) and <work dir>\sdk\sl (NVIDIA Streamline v2.14.16: bin\x64\
  sl.interposer.dll, sl.dlss.dll, sl.dlss_g.dll, nvngx_dlss.dll 310.9.16, nvngx_dlssg.dll, sl.reflex.dll; headers in
  include\). Our compiler is zig cc (mingw ABI): use the FFX C API through LoadLibrary; Streamline is C++ (write a
  small C++ shim with zig c++, functions via GetProcAddress; it wants to interpose Vulkan: use its manual hooking
  mode, see Streamline docs ProgrammingGuideManualHooking.md).
- Camera: vertex cbuf k=3 (512 bytes, e.g. guest 7265cc5800 in the meadow; bound by most scene draws) rows (vec4,
  row-major, world -> clip = dot(row, pos)): 0-2 view (3x4), 3-6 projection (cot(fov/2) = 2.4142 -> 45 deg vertical,
  aspect 1.778, near 0.8, infinite far, depth = 1 - 0.8 / -z_view, NOT inverted), 7-10 view-projection, 28 = (1/1280,
  1/720). Detect per frame by signature (row6 = 0,0,-1,0 and rows 7-10 = P*V), keep last frame's for motion vectors.
- Depth: the scene depth is the 1280x720-guest D24S8 (fmt 0x35) used by the depth prepass / G-buffer passes; post
  chain: DOF composite fs 72c28b6f00 -> fs 72c28d0600 writes the window image 724d510400, then the HUD passes.
- The game HAS temporal AA (lib_nx.ini tmaa=on, tmaaNewUpScale) and per-object + camera motion blur (blur2): it
  computes motion somewhere (velocity or previous matrices) - find it (a pass that reads two matrices / writes RG16F):
  real per-object motion vectors would stop characters ghosting.
- Hook point: exec.c post_process() (SMAA / FSR 1 at present) has the final image; internal resolution already
  scales via output_scale.c (resolution modes) so "render at 67 % + upscale" exists for FSR 1 / bilinear.
Plan: (1) jitter: sub-pixel viewport offset (Halton, FFX jitter query) on scene draws only (depth test on + the scene
depth attached), none on full-screen / HUD passes; (2) motion vectors: a compute pass from depth + this / previous
view-projection (camera motion), later the game's own velocity if found; (3) FSR 3.1 upscale in post_process (color =
pre-HUD image ideally: split the window image at the first HUD pass; v1 may upscale with the HUD and a reactive mask),
quality modes Quality/Balanced/Performance/Native AA; (4) FSR 3 frame generation (ffx swapchain replacement for
Vulkan: it owns present - device.c create_swapchain / vk_frame_end must go through it); (5) DLSS SR + DLSS FG via
Streamline (NVIDIA only; Reflex marker calls); (6) launcher: replace the disabled "NVIDIA DLSS / FSR 2+" checkbox
with Upscaler = FSR 1 / FSR 3.1 / DLSS, Quality, Frame generation on/off (greyed when the GPU can't), xcde.ini keys;
DLLs copied next to build/xcde.exe at build/package time. Verify: deterministic captures with it off = identical; with
it on, captures + real-time runs (battle_b, change_time, the meadow spin), fps with build/perf4k.sh.

### Task B: mod support
- Today: only the internal lib_nx.ini edit (romfs_virtual.c maybe_edit: File.mem replaces a file's bytes).
- Goal: `mods/<name>/romfs/...` (Ryujinx / yuzu layout) - files replace or add to the game's romfs; launcher tab
  "Mods" lists folders with on/off (xcde.ini `mod_<name> = 0/1`), load order = alphabetical, later wins.
  Implement in romfs_virtual.c scan(): after scanning targets/romfs, overlay each enabled mod folder (replace File.path
  / size, add new entries; tables are built after scanning, so adds are free). exefs / NSO patches (IPS, pchtxt) do not
  apply to recompiled code: support pchtxt "memory patches" only for data addresses, or document that code mods need
  a port. The GameBanana AA/Blur mod (452909) then works as a plain romfs mod too.
- Verify: a test mod folder replacing lib_nx.ini and a bdat, log lines listing applied files, no change without mods.

### Task C: Xenoblade 3-style character switching (battle + overworld)
Full plan: docs/plan_party_switch.md (research phase first: party / leader structures, per-character battle state,
input -> actor binding; then overworld leader switch, then in-battle control switch keeping arts recharge, talent /
party gauge, position, target, aggro, buffs; launcher option, bindings; deterministic + real-time verification).

## 00000000. START HERE — session 12 (written 2026-10-20 ~12:00, account switch mid-task)
Work in English (user's request, saves tokens). Never stop to ask between steps. One chat only (user: no parallel sessions).
**State:** main has everything merged (lighting T176 fix, visual T181/T182/T183, precompile T187 + soak freeze fix T185,
T162 parts 2-4 barriers, render-thread cuts, 60 fps option). build/xcde.exe + launcher rebuilt from main at 10:33; the
user is playing it (`Play Monado.bat`, 4K window, FSR, 60 fps on). Their saves are copied to
<work dir>\saves\user_20261020_1044 (4 slots; the load_a route loads the newest = bfsgame02).

## 000000000. START HERE — session 13 (written 2026-10-20 ~13:00, account switch; usage limit)
Work in English, answer the user briefly (they write Spanish). Never stop to ask. One chat. Max 3 game runs at once.
**ROOT CAUSE FOUND (not fixed yet) - Colony 9 gate black ramp = T192:** fs 72d95acc00 (the ramp mesh) reads the
10:10:10:2 normal buffer 7252f34000 with a raw SULD (D mode, R32UI) - `storage_uint_format()` (textures.c) only knew
32-bit-per-channel formats, so the image was bound to the DUMMY storage view: loads read 0, stores are dropped. Bug CLASS:
every SULD/SUST on RGBA8 / RGB10A2 / RG16 / R16 / R8 ... textures in the whole game was broken.
**Uncommitted work in the tree (finish it):**
1. textures.c: `storage_uint_format` now maps by texel size (8/16/32/64/128-bit -> R8/R16/R32/R32G32/R32G32B32A32_UINT);
   `want_storage[]` table + `storage_wanted(t)`; `create_image` adds STORAGE (+ `VK_IMAGE_CREATE_EXTENDED_USAGE_BIT` when
   the format itself can't) for wanted textures and sets `b->has_storage`. vk.h: `TexBackend.has_storage`.
2. TODO textures.c: `bool vk_tex_add_storage(NvnTexture *t, VkCommandBuffer cb)`: if has_storage or no uint format ->
   return; add (addr, format, width, height) to want_storage; `TexBackend old = *b; views_forget(b); b->image = b->mem = 0;
   create_image(t, b);` full barrier, vkCmdCopyImage all levels / layers old.image -> b->image (GENERAL), full barrier,
   `defer((Dead){.img = old.image, .mem = old.mem})`. Declare it in vk.h. (Storage on all RTs up front was rejected:
   costs DCC on Vega = min-spec.)
3. TODO exec.c: before `resolve_feedback(pr)` in the draw (and in dispatch), for every fragment/vertex/compute texture with
   `is_image`, resolve it like `storage_view_for` (st.img table, handle 0x120) and if `!b->has_storage`:
   `vk_end_pass(); st.rt_dirty = true; vk_tex_add_storage(t, vk_cmd());`. Also `vk_storage_view` should use
   `storage_uint_format` only (drop the `base_type` 2D check only if arrays are needed).
4. Build ALL vulkan objects (vk.h changed): `XCDE_EXE=build/xcde_s1.exe scripts/build_rt_gfx.sh nvn/maxwell/translate
   nvn/vulkan/exec nvn/vulkan/precompile nvn/vulkan/shaders nvn/vulkan/device nvn/vulkan/textures`.
5. Verify: `DRIVE_SAVE=<work dir>/saves/user_20261020_1158 DRIVE_EXE=build/xcde_s1.exe scripts/drive_env.sh
   tests/routes/change_time.txt 3700 1200 s1` -> ramp in front of the gate bridge must be lit (compare build/ct_3700.png =
   black). Then regressions (load_walk colony9 save 3000/6000/9000 vs build/xcde_e3.exe; ghost repro load_a 3000 from
   user_20261020_1044), then commit, rebuild build/xcde.exe (user not running it), tasks.md T192.
Also uncommitted: **T191 NVN alpha test** (shader.h alpha_func/alpha_ref in padding, translate.c discard epilogue,
exec.c CMD_SET_ALPHA_REF + key + f32_to_f16 + `| atest` log) - the game never sets it (no draw logged); keep, commit with T192.
New route tests/routes/change_time.txt (load newest save, X menu, Change Time -> 18:00, back to field) - commit it.
**Then (user's request): systematic audit** of the same bug class - log once per kind every NVN state stored but not
applied and every translator approximation (SULD "P" formatted mode uses a raw view = wrong for unorm; ignored ColorState /
Multisample / Polygon fields; dummy views bound anywhere; `fail()` messages), run the field/town routes, fix what the game
uses. Past root causes of this class: logic op ignored (T176), signed LDC offsets (T176), late stencil for image stores
(T180), raw storage views (T192).
Still open: T178 thin line (user: the save WITH Reyn shows it; screenshot <work dir>\user_reports\20261020_s12\shot3.png
- line also faintly over Reyn's shield), 60 fps dips (56-57 fps in the meadow, low CPU/GPU use: serial bottleneck).

**WAS IN PROGRESS (session 12, ~12:30) - Colony 9 main gate black ramp (user shot <work dir>\user_reports\20261020_s12\shot5.png;
black at night too):** save <work dir>\saves\user_20261020_1158 (newest autosave = the gate). Repro with sun:
`DRIVE_SAVE=<work dir>/saves/user_20261020_1158 scripts/drive_env.sh tests/routes/change_time.txt 3700 1200 x` (new route:
X menu -> Change Time -> 18:00). The ramp mesh is drawn by fs **72d95acc00** (XCDE_SKIP_PROG=72d95acc00 removes it):
3 RTs (albedo 72527b4000 blend, material 7252b74000 mask RG blend, normals 7252f34000 f0x3d mask RGBA) and it SAMPLES the
normal buffer it writes (tex1). Ruled out: probe pass (zeroing it keeps the black), cube maps, NVN alpha test (game never
sets it; implemented anyway as T191, `XCDE_ALPHA_TEST=0`, uncommitted in translate.c/exec.c/shader.h), feedback mode
(LARECOMP_FEEDBACK_DIRECT=0 same). Next: XCDE_GLSL_DIR overrides of 72d95acc00 outputs (RT2 alpha flag / normal).
User wants root-cause classes + an audit of ignored NVN state / approximated instructions (see chat), not one-offs.
Routes: `fps = 60` in the ini breaks routes (use an ini with display lines only). Still open: T178 line (save with Reyn),
60 fps dips.
**FIXED (session 12, tasks.md T180):** the ghost boxes = probe fragment shaders' imageStore ran with late stencil tests;
translate.c now emits `layout(early_fragment_tests) in;` for fs with SUST (`XCDE_EARLY_FS=0` = old). build/xcde.exe
rebuilt 11:42 with it. **Next:** T178 thin vertical line at 4K (report 1 below), then the 60 fps dips (report 2).
History of the hunt (kept for reference):
**WAS IN PROGRESS - "ghost" bug (T180 = T177 dark rectangles, user confirmed):** hard-edged black boxes on the cliffs behind
Shulk. Reproduced: `DRIVE_SAVE=<work dir>/saves/user_20261020_1044 DRIVE_EXE=build/xcde_mg.exe scripts/drive_env.sh
tests/routes/load_a.txt 3000 900 us1` (frame 3000, cave entrance at night). Chain found (debug frame 2999, pass images in
<work dir>\ghost\p1, log us2.log there):
- pass 267 = probe lighting fs 72c2d52000 (640x360) -> black in the boxes. Its probe index map t3 = 640x360 RG32UI
  @725c620000 is 0 in both words there (shader override in <work dir>\ghost\glsl visualizes it: idx2_big.png).
- The index map is built by passes 229-265 (probe volume boxes, two-pass stencil: marking fs 72c2cd1d00, OR fs
  72c2d2e100, logic op OR) and pass 266 (full screen, global probe, fs 72c2d14e00). Each probe shader appends itself only
  if its bit is not set in a per-pixel "slots used" STORAGE IMAGE i0 = 640x360 R32UI @725c800000 and popcount < 4, then
  imageStores the bit. So black boxes = i0 holds stale bits there (not cleared).
- The game clears i0 each frame with ClearColor as a render target (`[cclear] frame 2999 idx 0 640x360 f0xb`).
  **Next step:** check that the cleared render target and the storage image i0 are the SAME VkImage. The [cclear] log
  now prints @addr / obj / img; compare with i0's img in pass 266's tex lines. Run with XCDE_TRACE_RT=1
  LARECOMP_LOG_CLEARS=1 LARECOMP_DEBUG_FRAME=2999 on a fresh build
  (`XCDE_EXE=build/xcde_dbg4.exe scripts/build_rt_gfx.sh nvn/vulkan/exec`). Suspects: two NvnTexture objects at the
  same address -> two backends (alias), the storage (uint) view vs the attachment image, the clear's scissor, or the
  barrier between the clear and the image draws (T162 part 4 now tracks storage images).
  Not stencil: XCDE_NO_STENCIL_FS=72c2d2e100 (new debug switch) is still black. Not the float bitcast either.
- Debug additions committed (506cd3b): stencil-state line in debug draws, XCDE_NO_STENCIL_FS, [clear-tex] log, [cclear]
  with address / image.

**Other user reports today (in order):**
1. Thin black vertical line (T178), in all 4 autosaves; user screenshot at 4K (window 3840x2160, resolution match, FSR):
   a one-pixel column over the wall and grass but NOT over Shulk. Not seen at 720p deterministic. Repro at 4K from the
   user's saves (real time, LARECOMP_WINDOW=3840x2160, XCDE_INI=xcde.ini) and find the pass.
2. Perf: the 60 fps mode dips to 57 in the meadow with low CPU/GPU use; user expects ~120 fps at 4K. 60 is the cap (game
   frame interval 1, runtime/hle/framepace.c); 120 needs the period constant at 0x70009d3dcc (0.997) halved and the
   world dt checked. Dips with low usage = a serial bottleneck: profile the render thread / game main thread at 60 fps
   (XCDE_SAMPLE).
3. The yellow pillar in the user's 2nd shot is NOT a bug report (that shot was about fps).
4. Still open: T181 menu thumbnails (files fine, menu shows the placeholder), T177/T179 Colony 9 town checks, DLSS/FSR 3
   (no motion vectors; SDK downloads need the user's OK), battle character-switch mod.

## 0000000. START HERE — session 11 (written 2026-10-20 ~02:00, session 10 cut short by the usage limit)
- Done in session 10 (main): T162 part 2 committed (f64dee3): full barriers ~170 -> ~64 a field frame, captures identical.
  GPU gain NOT measured (PC loaded by parallel runs): redo the A/B (`XCDE_MEM_BARRIER=0` vs default, same exe, in parallel).
  `scripts/wt_setup.sh` prepares a git worktree to build/run (junctions targets/.venv/generated).
- Three parallel sessions were started in worktrees (.claude/worktrees/*), each committing to its own branch, NOT merged:
  `claude/lighting-bugs-*` (T176/T177/T179), `claude/visual-bugs-*` (T178, T180-T183), `claude/precompile-soak-*`
  (T187 precompilation + T185 soak). Check each branch's commits and tasks.md entries, then merge into main and rebuild
  build/xcde.exe (the launcher's exe is still the session 9 one).
- Next: merge branches, GPU A/B of T162 part 2, sampling-hazard barriers (~53/frame left, narrow to attachment -> shader
  read), render thread CPU.

## 000000. START HERE — session 10 (written 2026-10-19 ~23:45 at the end of session 9)
**State at the end:** `build/xcde.exe` = HEAD (7b275cc + this handoff), built 23:42, smoke-tested (field 30.1 fps). The
user plays it through `Play Monado.bat` (launcher). 22 commits this session (0f172b7..). Field GPU busy on the RTX GPU
~3.4 ms a frame at 720p (grass ~2 ms of it: PCIe reads, dGPU only); render thread ~13 ms a frame in battle in low-spec
mode (~25 ms estimated on the 3200G); process RAM flat ~6.1 GB private / ~4.4 GB working set on the dGPU after warm-up.
**First thing next session:** T162 part 2 - of the ~12,000 full barriers per 2 s that remain, ~10,000 are passes
"ended by something else" (memory-writing grass / skinning draws, the game's CMD_BARRIER, copies, clears): find which
(counter by vk_end_pass line, `pass ends:` in the VK_PROF line) and narrow each to the stages / resources it needs.
The "no barriers at all" test build showed -35 % GPU, so the room is there. Then T187 (precompile), then the bugs.
Read this block, then §00000 (session 9 start) below. Same standing instructions (Spanish answers, short; keep going;
root cause with data; commit verified fixes; bulky data on <work dir>; look at images yourself). New this session:
- **Min-spec target (user):** a friend's **Ryzen 3 3200G (4c/4t, Zen+) + Vega 8 iGPU + 8 GB RAM**, 720p + FSR (DLSS is
  NVIDIA-only). Optimize only OUR overhead, never the game's own features. **No optimization may change graphics, logic
  or HUD**: prove equivalence (deterministic captures vs the old exe, byte self-checks, differential tests) before commit.
- **Order (user):** 1) optimization to the max, 2) shader precompilation (T187/T188), 3) the bug list T176-T184
  (user's screenshots in <work dir>\user_reports\20261019_s9\; RenderDoc 1.46 portable in <work dir>\tools\renderdoc,
  installed with the user's OK, untested on our device).
- **Parallel runs:** at most 3 game runs at once (4 only when the user says they're going to sleep); 4K only for fps;
  each run ~4 GB RAM (4 at once nearly froze the PC).
- **Low-spec mode:** `XCDE_LOWSPEC_CPUS=4` pins the process to 4 physical cores. Measure CPU changes there, with the
  sampler (`XCDE_SAMPLE`) and **without** `LARECOMP_VK_PROF` (its per-draw timers cost ~7 % of the render thread).
  Series of runs share cache/: alternate the order (A B B A) or later runs look better.
- **Done (commits 0f172b7..7b275cc):** tracked pass barriers (T162 part 1: GPU -8 %), GPU deswizzle (T164), shader workers below normal priority (T160), LAS
  leftovers removed (T186), `Cpu *restrict c` in all lifted code (T165: -13 % process CPU, game workers -37 %; x86-64-v3
  measured WORSE - not used), graphics pipeline libraries (T188), TSC clock on slow-QPC PCs (T190), vertex cache off on
  iGPUs (T169), `[mem]` report + `XCDE_MEM_MAP`, FLO .SH/.INV + BFE.BREV (translator), upstream lazy-commit race fix,
  battle routes (`tests/routes/battle_b.txt`: 29.9 fps in battle in low-spec mode).
- **Tried and dropped (measured):** descriptor set reuse (no gain), guest registers as C locals (x86 has too few
  registers: worse), x86-64-v3.
- **Other recomps reviewed:** docs/lessons_astral_ssbu.md (AstralChain-PC, ssbu-recomp, AC-Recomp, EoWRecomp, B2recomp,
  SkyRecomp, and updates of LASRecomp branches, WindowSmash, SMW, letsgo, MacNativeGames). Memory file
  other-recomp-repos lists them all. Tasks T187-T196 come from them.
- Descriptor update templates also tried: no gain (tasks.md), reverted.
- **Next, in order:** T162 part 2 (above), render thread CPU (driver ~37 % of it in battle: descriptor writes - set
  reuse and update templates both gave nothing; next ideas: fewer descriptors per draw, VK_EXT_descriptor_buffer),
  T185 soak test (1-2 h, when the user sleeps: 4 runs allowed then), T187 precompilation, then bugs T176-T184.
  The dev PC's Ryzen iGPU is disabled in BIOS; the user may enable it later for real low-end GPU tests (T193 iGPU path).
- **Pitfalls this session:** `
` in C strings written through python/bash heredocs became real newlines 4 times (use
  the Edit tool for any C string with escapes); `cp` of a pdb over the one the linker just wrote (relink to fix);
  `git checkout <file>` to drop an experiment also drops other uncommitted edits in that file.
- **User ideas noted, not planned:** switching the controlled party member in battle (XC3-style), as an optional mod.

## 00000. START HERE — session 9 (written 2026-10-19 ~17:15 at the end of session 8)
Read this block, then §0000 (session 8 start) below. Work in English; the user writes Spanish (answer in Spanish, short,
plain). Standing instructions unchanged: keep going without asking between steps, root cause with data, commit verified
fixes, bulky data on **<work dir>**, look at images yourself, **use the whole PC** (the user asked twice: run several
test exes in parallel). Python with PIL: `python`.
**User's goal:** a hyper-optimized port ("otherwise what is the point of porting it"): no hitches, stable frame times, low
CPU/GPU, then 60 fps. Measure every change (before/after in tasks.md).

**State:** the user played New Game -> Colony 9 and **saved** (backup `<work dir>\saves\colony9_20261019_1235`, the
user's own `save/` is never touched by tests). Real time field: 30 fps steady, GPU ~9 ms of 33, CPU 0.85 cores.
`build/xcde.exe` = HEAD (69b98ce), built 17:14. 15 commits this session (fca6a99..69b98ce), all in tasks.md T155-T175.

**Done this session (measured):**
- CPU: frame limiter spun on the tick -> sleeps (T157, main thread 0.77 -> 0.31 cores); clock reads did 128-bit software
  division (T158); getenv per draw cached (T159). Process 1.38 -> 0.85 cores.
- GPU: colour feedback copied the whole render target ~1,700x per battle frame -> samples the attachment (T161, battle
  +16 %). 3D LUT uploads scanned write-combined memory (T155, 5-80 ms hitches gone).
- Bugs: crash after "accept bonus" with audio on (T170, garbage AudioOutBuffer offset from the movie's IAudioOut).
  Black grass flashes = GPU write-after-read race on the grass transform-feedback scratch (T136: barrier before
  memory-writing draws). Draws were dropped while their shader compiled -> they wait (T174). Black characters near the
  camera = **the game's own effect**, also on Switch (T173; proven with the user's Switch video, see below).
- Hitches: shader variant precompilation (T163): startup build waits 7.9 s -> 0.23 s, in-field 519 -> 141 ms.
- Tried and reverted: T175 (GPU-only heap ranges in VRAM: it made most grass disappear).

**Test infrastructure (use it):**
- `DRIVE_SAVE=<work dir>/saves/colony9_20261019_1235 scripts/drive_env.sh tests/routes/load_a.txt <frames> <secs> <name>`:
  deterministic run from the save, field at frame ~2400 in ~1.5 min. `tests/routes/load_walk.txt` = load + walk in circles
  turning the camera (frames 2500-12000). Drives run `build/xcde_dev.exe` (copied from xcde.exe; `DRIVE_EXE=` for another),
  never kill the user's game, use a scratch save, stop after the last capture. Build test exes with
  `XCDE_EXE=build/xcde_devN.exe scripts/build_rt_gfx.sh <objs>` (a running exe can't be relinked: use a new N).
- Real-time runs: `LARECOMP_SAVE_DIR=build/save_<n>` (copy of the save) + `LARECOMP_WINDOW=1280x720 LARECOMP_HIDDEN=1
  LARECOMP_NO_AUDIO=1 XCDE_INPUT_REPLAY=<route>` with `build/xcde_devN.exe targets`; retry loop on "not free" (T135).
- **Deterministic runs are not representative for GPU time** (vertex cache off there: vertices read from host memory).
  Measure GPU in real time: `LARECOMP_GPUPROF_AT=<frame>` (+ `XCDE_GPUPROF_VS=<vs,...>` per-draw timestamps).
- `XCDE_SAMPLE=<from>:<to>` sampling profiler (per thread/function, PDB symbols) -> build/samples.txt.
- `XCDE_FLICKER_CHECK=<dir>` in-game one-frame dark flash detector; `tools/video_flicker.py <video> <out>` the same on
  a video file. `LARECOMP_LOG_PACE=1` frame periods; `[hitch]` lines (LARECOMP_VK_PROF=1) break slow frames down;
  `LARECOMP_VK_PROF=1` waits by cause; `XCDE_FB_STATS=1`, `XCDE_TRACE_VC=1`, `XCDE_TRACE_3D=1`.
- Pitfalls: `LARECOMP_DEBUG_FRAME=N` dumps the frame captured as `XCDE_SHOTS` N+1. `\n` in C strings written through
  bash heredoc/python breaks (use Write/Edit, or chr(92)). Field pass dumps ~270 PNGs: move them to E:.
- **Reference:** the user's Switch video, full 30 fps: `<local file>
  Walkthrough Part 1 - No Commentary Playthrough (Switch) [ca1U134yIRY].f137.mp4` (2 h 05 min; 1 fps frames in
  <work dir>\full). The user's own PC captures: `<local file>`.

**Next, in order (user agreed: hitches -> battle -> launcher precompile -> 60 fps):**
1. **T160 remaining hitches**: ~13 frames > 40 ms per 5 min in the field, not compiles any more. Break each down with
   `[hitch]` (LARECOMP_VK_PROF=1) + pace log: texture uploads on the render thread (T164, 2-3 ms per big texture),
   GPU waits.
2. **Battle**: measure a battle frame in real time with `LARECOMP_GPUPROF_AT` (battle was ~25 fps before T161). Needs a
   route to a fight from the save (Colony 9 outskirts has enemies; the user's video shows Mechon fights).
3. **Precompile for areas not visited yet** (T163 part 2): launcher button / shipped variant list; cold-cache first run.
4. **60 fps patch**: the game's limiter is `f_70005bcfe0` (patched for T157, games/xcde/patches.py); find its target and
   the world's fixed step, then a launcher option.
5. Then T162 (barriers/passes), grass overdraw (~3 ms GPU, prepass vs 72c293c900), T165 (generated code registers),
   T166, T168 (load times), T169 (RAM). Open visual bugs: T154 navy cliffs (layer hypothesis ruled out).

---

## 0000. START HERE — session 8 (written 2026-10-19 ~10:30 at the end of session 7)
Read this block, then §000 (session 6). Work in English; the user writes Spanish (answer in Spanish, short). Standing
instructions unchanged: keep going without asking between steps, root cause with data, commit verified fixes, bulky data on
**<work dir>**, look at images yourself. Python with PIL: `python`.

**State:** the game plays through the whole prologue: battle tutorial completes (`tests/routes/new_game_h.txt`: approach the
target, close "Battle Introduction 3" / "Using Arts 1", Enchant = D-pad left + A, Buster = right + A), cutscenes, "One Year
Later", Colony 9 outskirts with Shulk and Reyn (Krabble fight, Using Arts 2 / Talent Arts / Treasure Chests popups, minimap
HUD, in-game clock). `tests/routes/new_game_j.txt` walks in circles from 50000 pressing A (found the treasure chest pillar at
~53900; the story didn't advance yet - the next trigger is unknown: video at 780 s shows "Aggro and Positioning" popups and a
Reyn cutscene). **No save exists yet**: X / + / - from the field opened no menu in the route (maybe still locked by the
tutorial). **Real time (not deterministic) runs a stable 30 fps** in cutscenes and battle (GPU ~33 % busy, render thread
~33 %): plenty of headroom. Progress ~45 %.

**Done this session (all committed on `main` except the last block below):**
- Launcher: `Play Monado.bat` (root) -> `build/xcde_launcher.exe` (tools/launcher/launcher.cpp, SDL3 + ImGui SDL renderer,
  `tools/launcher/build.sh`). Spanish UI: window/fullscreen, internal resolution, FSR 1 / bilinear, SMAA, FPS in title,
  key + pad remapping, volume, language. Writes `xcde.ini` (gitignored); the game reads it in `runtime/host/settings_ini.c`
  (test runs - hidden / deterministic / replay - ignore it unless `XCDE_INI=<file>`). Tested: Spanish text, 1600x900, FSR 2x,
  SMAA. `--shot <bmp> <tab>` renders the launcher to a file (tests). DLSS/FSR2+ shown as "not available" (none of the other
  recomps has them either; LASRecomp = FSR 1 + MetalFX).
- SMAA was never built in (stub in stubs_gfx.c) and crashed the game when enabled: `runtime/nvn/smaa_data.c` now built,
  `tools/gen_smaa_inc.py` generates `build/inc/smaa_hlsl.inc` (build_rt_gfx.sh).
- T153 battle tutorial routes; T152 NaN scan clean; T140 not a bug (video has the same bars).
- T154 cube-map layer stride: layers aligned to >= 16 GOBs (measured in guest memory: 64x64 BC6H cube faces are 8192 B
  apart) - correct but NOT the cause of the navy cliffs.
- Tools: `XCDE_SKIP_GPU_UNTIL=<frame>` (no GPU work before a frame; the scene must load after it - use 40500 for the field:
  reaches frame 42000 in ~13 min instead of 35; deterministic runs are capped at exactly 60 fps wall-clock, cause unknown),
  `XCDE_EXE=build/xcde_dev.exe scripts/build_rt_gfx.sh ...` (separate exe, doesn't kill running games: run 2-3 tests in
  parallel), `XCDE_SPLIT_DRAWS_TO`, `XCDE_DUMP_XFB`, `XCDE_DUMP_VB=<vs,...>`, `XCDE_TRACE_RT`, `LARECOMP_DEBUG_FRAMES=1`
  (pass files named by frame - use it when two debug runs overlap), `tools/glsl_dataflow.py` (compares gl_Position trees of
  two translated VS), `tools/contact_sheet.py` (reference video), `tools/shot_sheet.py`, `scripts/drive_env.sh`.

**Committed at the end (b0d207e) and built into build/xcde.exe, only partly verified in a game run:**
- `runtime/nvn/tegra.c`: GOB-row deswizzle + threads for big surfaces (3.3x faster: 14 GB/s); `tests/native/test_tegra_copy.c`
  passes 250 cases (added to scripts/native_tests.sh).
- `runtime/host/main_boot.c`: **T135 fix** - if the guest range is taken, the exe relaunches itself (job object, up to 8
  tries) instead of dying. Untested (the failure is random ~1/5).
- `runtime/nvn/vulkan/device.c`: pipeline cache saved every 2 min (was only at clean exit; killed runs lost it).
- `runtime/nvn/objects.c`: logs present interval + `XCDE_LOG_PACE` (vsyncs between presents: always 0 - the game does NOT
  wait on display vsync; it paces itself at 30 fps with its own timer).
- `runtime/nvn/vulkan/textures.c`: `XCDE_PROF_UPLOAD=1` breakdown of slow texture uploads; `exec.c`: transient chunk log.
- Still to do: a full `scripts/native_tests.sh` run and one launcher start to confirm the T135 relaunch and the deswizzle in play.

**User's goal (2026-10-19, their words: "in the end this has to be hyper-optimized, otherwise what is the point of porting it"):**
the port must end up **hyper-optimized** - better than an emulator, or porting makes no sense. Performance is a first-class
goal, not polish: no hitches, stable frame times, fast loading, low CPU/GPU use, shaders ready ahead of time, 60 fps
eventually. Also keep looking for other things to compare/borrow from the other recomps (LASRecomp peiikai, Mario Wonder,
Let's Go, WindowSmash, B2recomp) and keep fixing whatever else shows up, not only the list below. Measure every
optimization (before/after numbers in tasks.md).

**Next, in order:**
1. **Scene-change hitches (50-300 ms):** cause measured = 3D textures (colour LUTs 64x64x15 / 16x16x16, bd 4) taking 70-80 ms
   each in the copy step when the transient ring is BAR (device-local host-visible) memory, ~12 ms with
   `LARECOMP_VK_RING_SYSMEM=1`. Still far too slow for 0.25 MB: look at the 3D path of `copy_rows` (bd 4, gob_offset per GOB
   with z) and at writing into write-combined memory (deswizzle into a malloc'd buffer, then one memcpy to the ring).
2. **Save:** find how to open the menu / reach Colony 9 (user offered to play there with the launcher and save; the save goes
   to `save/save_0`). With a save, tests start in the field in minutes.
3. **T154 navy cliffs** (user confirmed): G-buffer albedo is right; the probe-lighting pass (fs 72c2d52000, cube array
   R11G11B10 built per frame from 7 BC6H time-of-day cubes by fs 72c2900b00) outputs blue. Check the probe list (cb6) /
   weights (tex 640x360 f0x29) / the cube array contents (`XCDE_DUMP_TEX_ADDR=725f480200` at a field frame).
4. **T136 black grass** (user confirmed): EQUAL-depth colour pass vs prepass; XFB data, vertex streams and gl_Position
   formulas are all identical (proved). Remaining suspects: depth state per draw (bias / clip / depth range), rasterizer
   differences between the two programs. Per-draw split images: <work dir>\sp2.
5. **60 fps (user asked for "parche 1"):** find the game's frame timer (it sleeps/waits to 33.3 ms itself; not vsync) and the
   world's fixed step; then a launcher option "60 fps (experimental)". Perf headroom exists.
6. Shader precompile from the launcher (SPIR-V cache already in cache/spirv; pipelines in cache/vk_pipelines.bin), then the
   feature list the user compared with other recomps: ultrawide, anisotropic 16x, mods folder, F1 overlay / F3 screenshots,
   report button, mouse camera.

---
## 000. START HERE — session 6 (written 2026-10-19 ~01:10 at the end of session 5)
Read this block, then §00 (session 5, what was fixed) and §0 (session 4). Work in English; the user writes Spanish.
**Standing instructions (user):** never stop to ask before the next step/phase - keep going until done, stop only if truly blocked; root cause with data before fixing; commit each verified fix; bulky generated data (dumps, captures, video frames) goes on **drive E:** (`<work dir>\`), not C:; for graphics, besides automatic checks, **look at the images yourself** (zoomed crops) - the user has caught several bugs by eye.

**State:** New Game route reaches the first battle and the fight runs (`tests/routes/new_game_d.txt`: A at 16600 closes Battle Introduction 1, stick walk, L target, A A closes Battle Introduction 2, A attacks; runs to frame 20000+). Party, Mechon, HUD (portraits, enemy bar, Battle Palette, hints, gauges), loading screen all verified against the user's Switch video. Real time 30 fps in battle; deterministic 3D ~20-25 fps. Progress estimate ≈ 40 %.

**In flight - step 2 detectors (user asked: build them all and fix what they find):**
1. **Vulkan validation** (`VK_ADD_LAYER_PATH='C:\msys64\ucrt64\bin' LARECOMP_VK_VALIDATION=1`; `[validation] NEW <id>: <msg>` once per id, now deduplicated in `device.c debug_cb`). Found and fixed (UNCOMMITTED until this handoff's commit, built, partly verified - a 100 s validated run showed no more errors): (a) point-list draws without a written point size -> VS always writes `gl_PointSize = 1` (`translate.c`); (b) R8_UINT (any *_UINT) textures sampled with a float sampler -> `stencil_unit_mask` in `exec.c` now marks them `usampler` (raw bits, as Maxwell). **To do:** a long validated run past the intro and in 3D. **Blocker found:** the validation layer itself leaks Windows handles (~3.5 M per 15 s; 16 M after a minute) and the process dies (error 1450) during the intro movie; a normal run stays at ~1,900 handles. Disabling its thread-safety check doesn't help. Options: try other `VK_LAYER_DISABLES` / an older layer, or validated runs in short windows; not our bug.
2. **NaN/Inf scan** (`XCDE_CHECK_NAN=<N>`: every N-th frame each float colour attachment is read back at pass end and scanned; `[check-nan]` lines). Written and compiled (`exec.c nan_scan`, `pass_tb`), **not run yet**. Run it on `new_game_d` (e.g. N=300) and fix what it reports (T136 near-grass black in the final composite is a candidate).
3. **Unwritten pixels** and **HUD clipped at edges**: not built. Idea for unwritten pixels: in check mode clear fresh colour targets to a sentinel (magenta / NaN) instead of black and look for it downstream; the black-grass class is already covered by `XCDE_CHECK_EQ` (EQUAL-depth draws that never pass).
4. Reference comparison: `python tools/ref_compare.py <captures> --window 0-900 --out <work dir>/cmp/<name>`; video frames in `<work dir>\full|idx` (levels fitted; the video lifts blacks - T150 was that). Cutscenes match at corr 0.95-0.99; live battle doesn't (compare by HUD element). Review every pair by eye.

**Pitfalls this session:** `scripts/build_rt_gfx.sh` kills running `xcde.exe` (don't build while a run you need is going); a crashed process can stay hung holding `build/xcde.exe` (link "Permission denied": `taskkill //F //IM xcde.exe`, then `scripts/link_gfx.sh`); T135 "guest address range ... not free" now hits ~1 in 5 starts - wrap runs in `for t in 1 2 3; do ...; grep -q "not free" log || break; done`; heredoc `\n` in C strings (use the Edit tool); `python` with MSYS2 first in PATH lacks PIL (run python steps in a shell without that PATH); debug prints of cbufs: hardware c3 = NVN binding 0 (`ubuf[stage][k-3]`).

**Next after step 2:** continue the route (finish the tutorial battle, toward Colony 9), compare each new scene with the video (`<work dir>`), T124 (texture change detection timing), T136, T135 (reserve the guest range earlier / retry), performance (fbcopy count, deterministic 20 fps).

---
## 00. START HERE — session 5 (2026-10-18, evening; the user was away ~5 h and asked to keep fixing from this file + plan.md)
Read this block, then §0 (session 4) below. Same standing instructions (work in English, fix root causes with data, commit each verified fix, no new downloads without asking).

**Done this session (commits on `main`):**
- `fdb83c5` **T134 black grass = transform feedback was never implemented.** XCDE animates grass with a point draw (vs `72c293a800`, no fs) whose outputs are captured by transform feedback into a scratch buffer the grass draws read as vertices; `nvnCommandBuffer*TransformFeedback*` and `SetRasterizerDiscard` were no-ops. Capture layout lives in the NVN control section: `[0x6e8]` varying count, `[0x6dc]` stride, `[0xdc+i]` slot (0x20+k = output v_k), `[0x4dc+i]` components; 9 such shaders seen, all buffer 0. Emulated as heap stores in a VS variant (`ShaderKey.xfb_*`, uniform `XfbP` binding 22, `exec.c xfb_key`), appended per draw (non-indexed lists only; others log `[xfb] ... not emulated`). Rasterizer discard = empty scissor. Draws that store to memory now end the render pass (and graphics STG sets `uses_gmem_store`, which it never did). Test `tests/native/test_translate_xfb.c`.
- `e84c742` **T138 thread stacks were committed, not reserved** (winpthreads commits an explicit stack size: 256 MB × ~38 guest threads ≈ 10 GB per process). At the commit limit `pthread_create` failed silently → deterministic hang at frame 7 with the baton on a thread that didn't exist. Now the 256 MB is the exe's default reservation (`-Wl,--stack,268435456` in `link_gfx.sh`/`link_boot.sh`) and creation failure is fatal. Game private memory: 4.6 GB.
- Route: **"Battle Introduction 1" closes with A** (the earlier "A doesn't close it" was pressing too early): `tests/routes/new_game_b.txt` (A at 16600). The battle field then shows with the HUD hint "Target L/R · Move Camera · Auto-run" and waits for L/R (L = 0x40, R = 0x80 in routes).

- **T137 invisible party/enemies in battle = occlusion counters always 0.** `ReportCounter` wrote 0 for every type; type 1 (samples passed) is XCDE's occlusion culling of field characters/enemies, so nobody was drawn in gameplay (the game issued no character draws). **T139:** real Vulkan occlusion queries (one per render pass while counting, summed per report, resolved at submission completion; "visible" provisionally). Deterministic mode always reports "visible" (keeps runs reproducible). Route `tests/routes/new_game_c.txt`: walks, turns the camera, targets with L → "Battle Introduction 2" (1/2, A = Next). Real-time route `tests/routes/realtime_tap_a_long.txt` (A every 200 frames to 30000).
- T124 rechecked: SVC digests identical, images split from frame 6171 as before (plus 914-916); not fixed by the barrier/XFB work.

- `8f72fd3` **T141 crash on the first attack** (`FATAL: no function at 70005264e8`): a jump table whose index is reloaded from a stack slot after the bounds check was "resolved" to one garbage case by the generator. `tools/lifter/gen.py`: the emulated index also fills the scratch stack window; a multi-entry table that yields one target is rejected (safe fallback). Regenerate with `cd tools && ../.venv/Scripts/python -X utf8 -E -s gen_all.py --out ../generated`, then `scripts/build_boot.sh` (only changed chunks recompile) and `scripts/build_rt_gfx.sh`. Battle runs to frame 20000+ (`tests/routes/new_game_d.txt`).
- `a45503b` **T146 everything rendered at 853x480 in a 720p window**: `output_scale.c` (LAS) assumed a 1920x1080 game frame; now the base is the game's NVN window texture size (1280x720). Sharper scene and HUD; costs fps (deterministic 3D ~15-16 fps).
- Detectors: `XCDE_CHECK_EQ=1` (deterministic runs: EQUAL-depth draws per program that never pass a sample, `[check-eq]` lines; 171 hits on `new_game_d`, many probably legit occlusion - needs the LEQUAL re-test to separate mismatches), `XCDE_SPLIT_DRAWS=<pass>` (one debug image per draw). NVN stub audit (T142): on the battle route the executor handles every recorded command except LINE_WIDTH; no other called no-op NVN entry points (4 harmless: tiled cache, control memory, scratch memory).
- User questions answered: HUD is complete after targeting (party panel, enemy bar, Battle Palette); before targeting the game shows only the hints (matches its own tutorial picture). Loading-screen Monado cut by the corner: same with handheld mode and at full resolution, likely by design (needs a Switch reference). User wants automatic bug detection: plan = T142-T145 (stub audit, per-frame detectors, reference comparison with a reference emulator - **permission asked, not yet given**).

- `34cc136`..`f6982db` **T147 scrambled small textures = wrong default block height** (user reports: loading-screen kanji off-centre, orange Battle Palette piece, quarter-disc art slots, striped enemy bar). Found draw by draw (`XCDE_SPLIT_DRAWS`, per-draw constants, `XCDE_DUMP_TEX_ADDR`, `XCDE_BH_TEST=<w>x<h>:<log2>`). Two power-of-two rules each broke a different set; final rule = thresholds on 1.5x the rows (tegra_swizzle `block_height_mip0`), every HUD element and the loading ring verified on screen. Test `tests/native/test_tegra_block_height.c` holds the measured cases.
- **Reference video:** the user's Switch playthrough (2 h, not versioned). Frames at 1 fps in `<work dir>\full` (1080p) and `idx`; `python tools/ref_compare.py <captures> --window 0-900 --out <work dir>/cmp/...` pairs and diffs (levels fitted: the video lifts blacks to ~29 and shifts dark R/G - T150 was that, not a bug). Cutscenes match (corr 0.95-0.99); live battle frames don't (camera differs): compare those by HUD element. **User wants every pair also reviewed by eye.** **Bulky data goes to drive E:, not C:** (`<work dir>\caps`, old debug dumps moved to `<work dir>\old_build`).
- Byte-level layout detector (`XCDE_CHECK_TEX`, `tegra_layout_roughness`) proved unreliable on BC7 (mostly-empty textures look "smoother" with the wrong layout): debug aid only. A decoded-pixel version (GOB-edge discontinuity on the GPU-decoded image) is the right design if needed again.

**Open, by priority:** step 2 detectors still to build (unwritten render-target pixels, NaN/Inf in HDR targets, HUD clipped at edges, Vulkan validation layers); review more scenes against the video (title, intro, Colony 9 later); T136 near grass black in the final composite; T124; T135 (startup "range not free", seen ~1 in 5 runs now: retry loop in the scripts); continue the route (Battle Introduction 2 done; the fight runs).

**Older open list (session 5 start):** T145 orange piece above the Battle Palette circle (user report; run with `XCDE_SPLIT_DRAWS` at frame 19400) → continue the battle tutorial (Battle Introduction 2: A = Next, then attack) → T140 battle HUD cut at the bottom edge? (needs a Switch reference) → T136 near-camera grass black in the final composite (fs `72c28b6f00`, likely DOF near field) → T124 (texture change detection timing, see tasks) → performance (17-25 fps deterministic in 3D; ~70k `fbcopy` per 2 s in battle).

**New debug switches:** `XCDE_DUMP_CONTROL=1` (each shader's NVN control section, 0x1000 bytes, to `build/ctrl/<stage>_<code>.bin`); debug-frame log now has `[barrier] (pass N) bits ..` and `[xfb] vs .. -> addr (+bytes ..)` lines. Note: the debug pass counter only advances for passes with a colour target (depth-only passes are not numbered).

**Pitfall:** `scripts/build_rt_gfx.sh` runs `taskkill xcde.exe` before linking — it kills any game run in progress.

---
## 0. START HERE — session 4 → session 5 (2026-10-18)
Read this block, then §10 (method) and §6 (pitfalls) below; older sections are history. Work in **English**; the user writes Spanish.

**User's standing instructions:** keep testing and fixing **without asking permission** between tasks (they may be in class); commit each verified fix; find the **root cause with data before fixing** ("revisa bien la causa raíz y luego soluciona"); give honest measured progress, no deadlines. Still ask before downloading/running new third-party binaries. Never commit game data (`build/ play/ crash/ cache/ save/ targets/ generated/`).

**State:** the New Game route reaches the first battle tutorial in deterministic mode (frame ~15,600) and in real time at ~30 fps: title → bonus → intro movie (T118 fixed) → "Eons have passed" → Sword Valley in-engine cutscenes → "Battle Introduction 1" (waits for a button: A does not close it; try B / Plus next). Progress estimate ≈ 35–38 %.

**In flight when the chat ended — verify first (T133):** in-engine cutscenes showed **exploded geometry** (hair/cloth as huge shards, real-time too). Root cause, proven step by step: XCDE computes skinning palettes **on the GPU** (point-list draws whose vertex shaders store matrices to memory, `fs=0`), into **one scratch range that each mesh's writer refills from index 0** (palette A = current, B = previous, e.g. `7263f11400` / `7263f6f130`); the mesh draw reads it right after. The game separates them with `nvnCommandBufferBarrier`, which our executor **dropped** (`[vk] UNIMPLEMENTED command 51` ~5,300 per 2 s since forever). Fix in `runtime/nvn/vulkan/exec.c` (`case CMD_BARRIER`: bits ≠ 0 → end the pass; the next `begin_pass` does a full barrier). **VERIFIED and committed (2026-10-18):** frames 9600/11400/12000/13800 now show Dunban, Mumkhar and the soldiers intact (before: shards); deterministic run speed unchanged (~22 fps). Still to do: `scripts/drive.sh tests/routes/new_game_a.txt 9600,11400,12000,13800 520 fix` → hair/characters intact? Then measure fps impact, rerun two deterministic runs + `tools/hash_diff.py` (T124 image split from frame ~6027 is very likely the same cause), `scripts/ci.sh`, `scripts/native_tests.sh`, update tasks (add T133) / plan changelog, commit. If barriers cost too much fps, refine by barrier bits (NVN: ORDER_PRIMITIVES 1, ORDER_FRAGMENTS 2, ORDER_FRAGMENTS_TILED 4, ORDER_INDIRECT_DATA 8, INVALIDATE_TEXTURE 0x10, INVALIDATE_SHADER 0x20, INVALIDATE_TEXTURE_DESCRIPTOR 0x40, INVALIDATE_ZCULL 0x80, INVALIDATE_L2_CACHE 0x100 — verify these values before relying on them).
Ruled out on the way (measured, don't redo): vertex/index fetch (`LARECOMP_VK_COPY_VERTICES=1`, model-space draw coherent), vertex cache, CPU/GPU submit race (`LARECOMP_SYNC_SUBMIT=1`), stale pages in the heap import (`XCDE_GMEM_CHECK`: GPU sees the same bytes), `maxStorageBufferRange` (4095 MB), LDC.64/carry chains/XMAD/FTZ in those shaders, vertex ID / `first`.

**Done this session (commits on `main`):** T118 movie output into the game's buffer (`movie_buf.h`, test) · T119 vertex cache off in deterministic mode · T122 HLE mutex vs deterministic baton deadlock (`kernel_det_mutex_lock`) · T125 program cache keyed by shader content · T126 zero-padded constant buffers · T127 LDC.64 address snapshot (test) · T128 upstream LASRecomp #108 fence seq + #127 fatal GPU wait timeout · reviews: `docs/lessons_windowsmash.md`, `docs/lessons_other_recomps.md` (Let's Go recomp, Mario Wonder recomp, TotK Mac port: their bug logs are worth rereading).
Committed with T133: `CMD_BARRIER`, `scripts/build_rt_gfx.sh` (**new: builds all runtime objects + links; use it instead of hand-compiling**: `scripts/build_rt_gfx.sh` or `scripts/build_rt_gfx.sh nvn/vulkan/exec kernel`), debug switches `XCDE_ONLY_VS`, `XCDE_GLSL_DIR` now also for `<addr>_vs.glsl`, `XCDE_GMEM_CHECK`, vertex-stage `[sbuf]` trace, vbuf address in `[attr]` trace, `maxStorageBufferRange` in the import log.

**Open tasks, by priority:** thin black streaks near the characters' feet at frame 11400 (particles/debris? new task T134) → T124 recheck with two deterministic runs (likely fixed by T133) → close the battle tutorial (route: B/Plus) and continue the route: battle → Colony 9 → save/load (T070/T071) → T124 (if not fixed by T133) → T129 (textures re-initialised mid-submit; Wonder #55-57) → T130 movie slots/EOS → T131 shader semantics audit → T121 vertex cache variance → performance (15–30 fps in 3D; ~17,000 `fbcopy` per 2 s; deterministic 3D runs ~20 fps) → new: intermittent startup `FATAL: guest address range 7000000000-7320000000 is not free` (retry works; needs a task: reserve earlier / retry with backoff).

**New tools/switches this session (also in §7/§12):** `XCDE_DET_DIGEST=1` (per-frame digest of the guest SVC stream — compare runs with this; image hashes still split, T124) · `XCDE_HASH_MEM(_FROM)` · `XCDE_PASS_HASH=<from>:<to>` · `XCDE_WATCH="<frame>:<lo>:<hi>"` (page watchpoint; reports CPU readers/writers; GPU writes don't show) · `XCDE_TRACE_DST` (+`LARECOMP_FNPROF`) · `XCDE_SKIP_PROG=<fs>` / `XCDE_ONLY_VS=<vs,...>` · `XCDE_GLSL_DIR` (fs and vs overrides) · `XCDE_GMEM_CHECK` · `XCDE_TEX_EXACT` · `XCDE_TRACE_MOVIE`, `XCDE_LOG_MOVIE` · `LARECOMP_SAVE_MSL=1` (translated GLSL to `build/glsl/`) · thread dumps print host call stacks of threads running without SVCs · `tests/routes/realtime_tap_a.txt` (A every 200 frames, for real-time runs). Workflow that worked: `LARECOMP_DEBUG_FRAME=<n>` + `XCDE_TRACE_ATTR=1 XCDE_TRACE_CB=2` to find a draw, `XCDE_DUMP_MEM` to pull its buffers, Python to check on the CPU, `XCDE_GLSL_DIR` variants to test hypotheses on the GPU.

**Pitfalls hit again:** `\n` inside C strings written through heredoc/sed/Python becomes a real newline — use the Edit tool (check with `cat -A`). **Never use `build/rt` or `build/nvn` as an output folder** (I wiped the runtime objects once; `scripts/build_rt_gfx.sh` rebuilds them). A failed link leaves the old `build/xcde.exe` silently — check `build/link_gfx.err` / the exe timestamp. Deterministic runs: ~5 min to reach frame 9600; run two in parallel when comparing.

---
# (older) HANDOFF — session 3 → next chat

> The session-3 handoff (2026-10-17) was written in Spanish; this is its English summary for the public repository.
> Its open bug (static in the intro video) was solved in session 4 (§12, T118). The working method it set out is in
> `CONTRIBUTING.md`.

## 1. What this is
- A static recompilation (AArch64 → C → x86-64) of **Xenoblade Chronicles: Definitive Edition 2.0.0** (Switch) into a
  native PC executable, meant as a base for the other three Xenoblade games. Spec-driven method (rules, spec,
  research, plan, tasks: `docs/dev/`). Built on LASRecomp (MIT, the runtime base); ssbu-recomp (GPL) read only as a
  reference.
- **Hard rules** (`CONTRIBUTING.md`): nothing from Nintendo in the repo (no lifted code, shaders, captures with assets,
  reference audio), the user's own dump, no keys, MIT attribution to LASRecomp. `scripts/ci.sh` +
  `tools/package_guard.py --git .` check it. `cache/ save/ build/ generated/ targets/ crash/ play/` are in `.gitignore`;
  captures in `build/*.png` and `play/` show the game: never commit them.

## 2. Environment (Windows 11, Git Bash / PowerShell)
| What | Where |
|---|---|
| The dump (extracted) | `targets/exefs/` and `targets/romfs/` (18,529 files). |
| Python | `.venv/` (capstone, unicorn, lz4, ziglang). The generator runs with `python -E -s`. |
| Compiler | `.venv/Scripts/python -m ziglang cc` (clang 21). No `clang` on the PATH is needed. |
| Libraries | MSYS2 `C:\msys64\ucrt64` (SDL3, Vulkan, shaderc, VMA, FFmpeg, opus). To run: `export PATH="/c/msys64/ucrt64/bin:$PATH"`. ffmpeg / ffprobe also help to analyse media. |

## 3. Commands (from the repository root)
```bash
scripts/ci.sh                  # Python tests + derived-file guard (a "VIOLATION ... a.nsp" line is a negative test's normal output)
scripts/native_tests.sh        # C tests: fibers, condvar, Maxwell translator
cd tools && ../.venv/Scripts/python -X utf8 gen_all.py --out ../generated && cd ..   # regenerate the C (≈ 10 s)
scripts/build_boot.sh          # compile the game objects + a window-less exe (build/xcde_boot.exe)
scripts/build_rt_gfx.sh        # compile the runtime objects and link build/xcde.exe (Vulkan, window)
```
`XCDE_EXE=build/other.exe scripts/build_rt_gfx.sh` links a separate exe without touching a running one.
Play: `export PATH="/c/msys64/ucrt64/bin:$PATH"; build/xcde.exe targets` (or the launcher).
`scripts/drive_env.sh <route> <frames,...> [secs] [name]` drives the game without a window, deterministically, with an
input route, and saves `build/<name>_<frame>.png`. Route format: `tests/routes/README.md` (A=1 B=2 X=4 Y=8
Plus=0x400 Minus=0x800, d-pad left/up/right/down = 0x1000/0x2000/0x4000/0x8000).
`scripts/repro_stability.sh N SECS DIR`: a boot loop classifying OK / HANG / CRASH.

## 6. Things learnt (don't repeat them)
- **T067 hang** = a `pthread_cond_timedwait` ETIMEDOUT ↔ condvar signal race in `block_current` (`runtime/kernel.c`):
  the result was overwritten and the thread blocked on its own mutex. **T108 close** = the virtual RomFS descriptor cache
  without a lock (`runtime/services/romfs_virtual.c`). With both fixed: 53/53 clean boots (≈ 13 % failed before).
- **Deterministic mode** (`XCDE_DETERMINISTIC=1`): a cooperative scheduler in `kernel.c` (one guest thread at a time,
  FIFO, switching when it blocks / yields / every 4,000 SVCs), **virtual time** (it only advances when everything is
  blocked or on a yield), vsync and end-of-audio-buffer as virtual timers, synchronous shaders, no pacer, virtual GPU
  counters. It runs faster than real time (the game sees a virtual 60 fps). With strict priorities the loader threads
  (prio 46/47) never ran: hence FIFO. `tools/hash_diff.py a b` compares per-frame hashes (`XCDE_FRAME_HASH=<file>`).
- **Pitfall no. 1 (happened ≥ 10 times):** Bash heredocs eat backslashes: a `\n` inside C strings written from
  Python / heredoc scripts becomes a real newline and breaks the build. Use a file-writing tool or `chr(92)`; after
  patching strings with `\n`, check with `cat -A`.
- **Pitfall 2:** kill a running `xcde.exe` before relinking it; `timeout` sometimes leaves it alive and the link fails
  with "Permission denied". `exit 124` = our own timeout; `127` = a crash with a report.
- **Pitfall 3:** changing a single SDK shader reorders the generated chunks: `build_boot.sh` deletes orphan objects.
- 853×480 rendering is the game's own dynamic resolution, not a bug. The title audio is soft (≈ −40 dBFS): real content.
- `LARECOMP_WINDOW_SHOT=<frame>` + `LARECOMP_EXIT_AFTER_SHOT=1` saves `build/window.png`; several captures per run:
  `XCDE_SHOTS="frame:path,..."` or `XCDE_SHOT_EVERY=<frames>[:<dir>]`.

## 7. Useful environment variables (LAS's start with `LARECOMP_`, ours with `XCDE_`)
Diagnostics: `XCDE_DETERMINISTIC` · `XCDE_FRAME_HASH=<f>` · `XCDE_INPUT_RECORD=<f>` / `XCDE_INPUT_REPLAY=<f>` ·
`XCDE_STRICT=1` (stop on anything unimplemented) · `XCDE_HLE_COVERAGE=<f>` (gaps) · `XCDE_USAGE=<f>` (census of
SVC / IPC / HLE / NVN / memory) · `XCDE_STALL=<s>` (watchdog, 5 by default, 0 turns it off) · `XCDE_WATCHDOG=<s>`
(periodic thread dump) · `XCDE_TEST_HANG_AT=<frame>` / `XCDE_TEST_CRASH_AT=<frame>` (tests) · `XCDE_NO_MINIDUMP=1` ·
`XCDE_CRASH_DUMP_REG=<n>` · `XCDE_DET_TRACE=1` (scheduler) · `XCDE_SHOTS`, `XCDE_SHOT_EVERY` ·
`XCDE_DUMP_MEM="frame:addr:size:file"` · `XCDE_DUMP_MOVIE=<n>` · `XCDE_LOG_MOVIE=1` · `XCDE_TRACE_MOVIECOPY=1` ·
`XCDE_TRACE_TEXINIT=1` · `LARECOMP_AUDOUT_WAV=<f>` (a PCM16 WAV of what plays) + `tools/wav_report.py` /
`tools/wav_compare.py`.
Rendering: `LARECOMP_DEBUG_FRAME=<n>` (dumps each pass to `build/pass_NNN.png`), `XCDE_DUMP_TEX=<pass>`,
`XCDE_DEPTH_HIST/STENCIL_HIST`, `XCDE_TRACE_CB=2`, `XCDE_TRACE_ATTR/IDX/VP/DS/CS/NVN`, `XCDE_WATCH_FS`,
`XCDE_GLSL_DIR`, `XCDE_NO_TEX_SHARE`. `LARECOMP_TRACE_SVC=1` (with thread id), `LARECOMP_FPS_INTERVAL=<s>`.
Later sections and `docs/dev/tasks.md` add many more (each is documented where it was introduced; grep the runtime for
`getenv("XCDE_` for the full list).

## 8. Map of key files
- `runtime/kernel.c` (SVCs, Horizon mutex / condvar, the **deterministic scheduler**, `kernel_dump_threads`),
  `runtime/diag/{diag.c,diag.h,watchdog.c,crashdump.c,sampler.c}`, `runtime/ipc.c`, `runtime/dispatch.c` (HLE, strict),
  `runtime/hle/{movie.c,vi.c,input.c,fibers.c,framepace.c,party.c,...}`,
  `runtime/services/{audio.c,romfs_virtual.c,fs.c,...}`, `runtime/nvn/` (objects.c, cmdbuf.c, maxwell/translate.c,
  vulkan/{exec,textures,shaders,device,precompile}.c).
- `tools/` (generator `lifter/gen.py`, `hle_audit.py`, `hash_diff.py`, `wav_report.py`, `wav_compare.py`,
  `package_guard.py`, `tour_gen.py`, `tour_batch.py`, `soak.py`), `games/xcde/` (`profile.json`, `hle_symbols.txt`,
  `hle_classes.tsv`), `tests/unit/*.py`, `tests/native/*.c`, `tests/routes/`, `tests/tours/`.
- Evidence: `docs/evidence/M*/`; audit `docs/hle_audit.md` (generated: `python tools/hle_audit.py`; its `--check` fails
  in the tests when it is out of date after adding an `HLE_FUNC` / `SERVICE`).

## 11. Addendum (end of session 3) — read this too
- **Latest commits:** `4b66157` (WindowSmash review, T111–T117, big-stack shader workers, `-ffp-contract=off`, `XCDE_LIST_IMPORTS`), `806310b`/`7f444ed` (this handoff: §10 method, English rule). Run `git log --oneline | head -20` for the full list.
- **External review done — do not redo it:** `docs/lessons_windowsmash.md` summarizes what a public SSBU recompilation project (WindowSmash: same technique, other game, D3D11) does. No magic method was visible (2 commits, no spec/prompt files). Its ideas became tasks **T111–T117** at the bottom of `tasks.md` (whole-function differential tests, sampling profiler = finish T043, `.eh_frame` cross-check of function discovery, tail-call helper, static IPC reachability, F3 capture hotkey). Ideas only: never copy its code.
- **Facts established that save you work:** 0 unimplemented imports in `main`/`sdk` (`XCDE_LIST_IMPORTS=1`); the game has **no C++ exceptions** (no unwind bridge needed); the 23 SVCs used by the title are all implemented; `HEAP_MAX` (3.25 GB) vs the game's single `SetHeapSize 0xC9400000` (≈3.15 GB) leaves ≈0.1 GB margin — watch it in later zones; audio output is `audout:u` only (Wwise opens `audren:u` just to query it).
- **Pending build step:** `-ffp-contract=off` is in `scripts/build_boot.sh` but the generated game objects were not rebuilt with it (a full rebuild is ≈131 s with 16 jobs: `scripts/build_boot.sh` after deleting `build/obj/`). Do it once before any performance work and rerun the differential tests.
- **New env var:** `XCDE_LIST_IMPORTS=1` (prints imports bound to an unimplemented host stub at load). Others added late in the session are in §7 (`XCDE_DUMP_MEM`, `XCDE_SHOTS`, `XCDE_SHOT_EVERY`, `XCDE_DUMP_MOVIE`, `XCDE_LOG_MOVIE`, `XCDE_TRACE_TEXINIT`, `XCDE_TRACE_MOVIECOPY`).
- **Task bookkeeping caveats:** `tasks.md` has two tasks numbered T070 (M4 "TLD4 PTP" and M5 route); rename one. T030/T032 are still unchecked although their work exists — verify and tick. M3 gate says Q2/Q4/Q5/Q7 answered: they are (in `research.md`), so only T037, T042, T043 remain for M3.
- **First 30 minutes for the next agent:** (1) `git status` + `scripts/ci.sh` + `scripts/native_tests.sh` to confirm a green start; (2) `scripts/drive.sh tests/routes/new_game_a.txt 1800,2400,3200 120 d1` to reproduce the video noise and look at the captures (`Read` the PNGs); (3) follow §5 "Next concrete step": print the real `t->addr` of the textures read by pass 173, dump it with `XCDE_DUMP_MEM`, compare with `build/movie.nv12`; (4) after it is fixed, extend the route and keep going per §9–§10.
- **What the user wants to hear:** short English status lines while you work; measured numbers; no deadlines promised; a ready-to-play build when the verifiable parts are verified, then the user plays with `scripts/play.sh` and sends `play/<date>/`.

## 12. Addendum (session 4, 2026-10-18)
- **§5 is solved (T118).** The static was the game's own "no signal" fill: its uploader `f_70005a8590` seeds its frame buffer with an LCG and copies NV12 rows from it to a GPU buffer that pass 172 converts (shader reads it via global memory, cb0 storage buffer 0). The HLE `GetOutputBuffer` replaced the pointer of the game-owned `movie::Buffer` instead of copying into it. Fix in `runtime/hle/movie_buf.h`. The intro now shows the titans; audio unchanged.
- **T119 closed:** the vertex cache is off in deterministic mode; 3 runs identical on all 5245 frames. Its run-to-run variation is T121. **Next blocker: T122** — the route stops presenting at frame 5245 (all guest threads blocked), deterministic.
- More switches: `XCDE_HASH_MEM="<addr>:<size>[,...]"` (+ `XCDE_HASH_MEM_FROM=<frame>`): guest memory hashes at every frame and every queue submit; `XCDE_PASS_HASH=<from>:<to>`: hash of every pass's colour target (syncs the GPU per pass, which can mask timing bugs).
- **New debug switches:** `XCDE_WATCH="<frame>:<lo>:<hi>"` (page watchpoint armed at a frame; names guest functions touching the range), `XCDE_TRACE_DST="<lo>:<hi>"` (with `LARECOMP_FNPROF=<from>:<to>`: functions entered with x0 in range, e.g. memcpy destinations, plus lr), `XCDE_SKIP_PROG=<fs code addr>` (drop draws of a program), `XCDE_TRACE_MOVIE=1` (every decoder output handed over, with frame). The `[draw]` log now prints render-target and texture guest addresses. `LARECOMP_SAVE_MSL=1` writes translated GLSL to `build/glsl/` (game-derived: never commit). Lesson: with `LARECOMP_DEBUG_FRAME`, the per-pass PNG can disagree with what later passes sample; confirm with a replacement shader (`XCDE_GLSL_DIR`) before trusting it.
- **T122 closed** (movie HLE lock held across a guest call deadlocked the deterministic scheduler; `kernel_det_mutex_lock`). The route now goes past the intro to "Eons have passed." and the first 3D scene. Thread dumps now include the host call stack of threads running with no recent SVC (`plat_thread_backtrace`; runtime frames appear as `?` or as the last `f_` plus a large offset because the PDB isn't read). `XCDE_DET_DIGEST=1` logs a per-frame digest of the guest SVC stream: equal digests mean the game ran identically, whatever the images say. `XCDE_TEX_EXACT=1`: every texture checked every frame with a full hash.
- **Open T124:** image hashes split from the first 3D scene (and sometimes during the movie) although the guest is identical. Compare runs with digests, not image hashes, until it's fixed.
