# Lessons from XCDE-Recomp for a Xenoblade Chronicles 2 recomp

Written 2026-10-23 at the end of the XCDE work (Xenoblade Chronicles: Definitive Edition, Switch -> Windows / Vulkan
static recompilation on top of LASRecomp). It covers what worked, what failed and why, and how things were found, so
the XC2 project starts from it instead of from zero. The details of each item are in `tasks.md` (task number given)
and in git history; this file is the map.

**What transfers.** Both games are Monolith Soft titles on the same in-house engine family, so the file formats and
tool paths transfer. These are checked in XCDE:

| | |
|---|---|
| Archives / layouts | `xbc1` (zlib), `LAHD` / `LAGP`, `mibl` / `LBIM` textures, SPCH shader containers |
| Graphics config | `lib_nx.ini` |
| Controls | `.pad` tables |
| Cutscenes | `rtmevt` |

**What does not transfer.** Addresses, vtables, object offsets and function names all have to be found again in
XC2. Each finding below says *how* it was found, so it can be repeated.

Notation: `f_70xxxxxxxx` = a lifted guest function; `0x7000b...` = vtables / data in the main image.

---

## 1. Method: what made bugs findable

These paid for themselves many times. Set them up first in XC2.

1. **Deterministic mode + recorded routes** (T029, `XCDE_DETERMINISTIC=1`, `XCDE_INPUT_REPLAY=<route>`,
   `scripts/drive_env.sh <route> <shot frames> <secs> <name>`).
   - A route is `frame buttons lx ly rx ry` lines.
   - Captures at given frames are compared with `cmpcap.py`, and "in the noise band" was the acceptance test for every
     change. Do it before any optimization.
   - **Measure the run-to-run noise first:** two runs of the same exe differed in a band of sky / cliff edges (T176 note).
     Without that baseline, every diff looks like a regression.
2. **Start routes from the user's save** (copied read-only to `<work dir>/saves/...`, never the live `save/`).
   Booting a new game every time wastes minutes per test and can't reach later areas.
3. **Hidden deterministic runs present only the captured frames.**
   - Anything with history is invisible there: TAA / DLSS / FSR ghosts, HUD composites (T216, T181 "ruled out" wrongly
     because of this).
   - For those use real time with every frame presented: `LARECOMP_HIDDEN=1 XCDE_PRESENT_ALWAYS=1`, no
     `XCDE_DETERMINISTIC`.
4. **Routes stall with `fps = 60` in the ini** (menu timing changes): use an ini without the fps line for routes.
5. **Shader overrides / pass dumps** (`LARECOMP_DEBUG_FRAME=N`, F9) to find which pass makes a wrong colour. Bisect by
   zeroing a pass output, replacing samples with constants, etc. This found the two big lighting bugs (T176, T180).
6. **Data-watch with backtrace** (`XCDE_WATCH="<frame>:<lo>:<hi>"`, `XCDE_WATCH_BT=1`): page-protects a range and logs
   which lifted function (+ callers) touches it. It found the camera writer chain and the save-thumbnail copy.
7. **Memory searches by behaviour** (`runtime/hle/framepace.c`), all env-driven:
   - `XCDE_DELTAFIND` + `_PAT` for small integers (cursors, counters).
     - Pattern mode `ABCBC`, for values that wrap (the arts palette cursor wraps centre -> right -> left).
     - Pure delta mode found an audio buffer instead (false positive).
   - `XCDE_FLOATFIND` + `_PAT` (u / a / b) + `_RATIO` for floats.
     - Hold a stick 20 frames, then the other way 10.
     - The real state changes by exactly -0.5 of the first turn; derived copies (matrices, sin / cos) don't.
     - The ratio filter was what isolated the camera.
   - `XCDE_FPOKE` (write a candidate, see if the game obeys) and `XCDE_FTRACE` (per-frame value). **Always poke-test a
     found value.** The first "camera yaw" was a stack temporary (an atan2 result); writing it did nothing.
   - Survivors log the vtables before them and the pointers to them, so an object can then be found by class.
8. **Find objects by vtable with a background heap scan** (`runtime/hle/party.c` heap_scan / party_scanner).
   - The scan runs on its own thread, once a second only when the cached objects are stale.
   - The game thread only checks the vtable before use.
   - A scan on the game thread was a 0.2-0.6 s hitch.
9. **Call guest functions from the host** (party.c `call_guest`) to do what the game's own menus do (set leader, rebuild
   follower group) instead of poking state. Robust across states.
10. **Patches in the lifted code** (`games/xcde/patches.py`) for compares / hooks, with the expected bytes checked.
11. **Hitch / stall logs** that name the cause: `[hitch]`, `[build-wait]` (queue / lock / translate / compile times),
    `[variant-miss]`. T200's "frame drop" was a 98 ms wait on an unfair translator lock, invisible without it.
12. **Sampling profiler** (`XCDE_SAMPLE`). Caveat: ~40 % of samples land on kernel wait returns; read per-thread totals.
13. **One-frame flicker detector** (`XCDE_FLICKER_CHECK`), **duplicate-frame check** (`XCDE_DUP_CHECK`), **NaN
    detector** (`XCDE_CHECK_NAN`), **NVN call census** (`XCDE_USAGE`), and an `[audit]` log of unimplemented paths
    running in every build (players' logs show new classes).
14. **Compare with the Switch.** The user's Switch video / YouTube walkthrough settled ~5 "bugs" that were the game's
    own look: silhouette fades near the camera (T173), orange HUD bars (T140), shadow colour (T150), depth of field
    (T183). Check the reference before fixing.

---

## 2. Graphics: bug classes that hit (fix them up front in XC2)

The 2026-10-20 audit grouped every graphics bug into a few classes. Expect the same in XC2.

**NVN state stored but never applied**:
- **Barriers** dropped (`CMD_BARRIER`) -> exploded hair / cloth in cutscenes (T133).
- **Logic op** (OR) not in the pipeline -> probe lighting overwrote instead of merging (T176 part 1).
- Transform feedback pause / resume, rasterizer discard, occlusion counters (T139).
- Rule: grep every NVN setter the game calls (`XCDE_USAGE`) and confirm it reaches Vulkan.

**Maxwell translator sign / precision**:
- **LDC immediate offsets are signed** (T176 root cause: navy cliffs; probe matrices read past the buffer).
- `LDC.64` with the address register as a destination (T127).
- Constant reads past the bound range must read 0 (T126).
- FLO .SH/.INV, BFE.BREV.
- SUATOM.D, VOTE, ATOM: 36 programs were never translated, so every draw using them was skipped silently (T226).
  **Log translation failures loudly.**

**Storage images in fragment shaders**:
- Need `early_fragment_tests` when they store (a fragment with side effects otherwise runs before depth / stencil;
  T180 black boxes).
- Raw views for non-32-bit formats (T192: a ramp read as 0).
- Coordinates scaled with the internal resolution, own pixel -> own scaled pixel (T178: a 1-column line at 4K from
  3x3 pixels racing on one texel).

**GPU hazards Maxwell hides**: Maxwell runs draws in order, Vulkan overlaps them inside a render pass.
- A transform-feedback capture rewrote a scratch buffer the previous batch was still reading -> black grass flashes
  (T136). Barrier before and after memory-writing draws.

**Texture layout**:
- 3D block-linear deswizzle (T068: whole image black).
- Small-texture block height (T147: scrambled small textures).
- Two NVN textures over the same memory must share one image (T107).

**Render-target scaling**: the scalable-target rule (16:9 only) missed the 192x544 portrait targets (T182).
- List every render target size at 4K once.

**Draws dropped while their pipeline compiled** (T174): an object whose colour pass was skipped but whose depth
prepass drew showed black. A draw must wait for its build; never skip.

**Vertex mirrors** (VRAM copies of GPU-written vertex data, a big perf win, below) need care:
- **A new mirror must retire every mirror it overlaps**, of any kind. Stale overlapped mirrors gave faces drawn as
  vertical strips (T205), seen only after long play.
- A first try with a margin after the buffer copied the skinning palettes stale (T175 redo).

**The CPU reads a render target's guest memory**: the save thumbnail is drawn on the GPU and then read block-linear
from guest memory (T181). Write that target back to guest memory after its draw.
- The load / save list then alternates two buffers, one with a marker, and offsets the quad off-screen until loaded
  (T181 / T222). Patch the game's own memcpy to know which buffer is real.

**Program cache keyed by guest code address** -> wrong shaders after streaming, and a fixed-size table that filled
and froze the render thread after 69 min (soak T185). Key by content hash; growable tables.

**Not bugs** (the game's own effects, see §1.14): near-camera silhouettes, depth of field, the HUD bars.

---

## 3. Performance: what worked and what did not

Target hardware set by the user: Ryzen 3 3200G (4 threads) + Vega 8 iGPU + 8 GB at 720p. Rule: cut our overhead only,
never the game's features. Every change was measured A/B and checked with captures.

### Worked (keep / redo in XC2)

**CPU and GPU work**

| Change | Result |
|---|---|
| `Cpu *restrict c` on every lifted function (T165) | -13 % CPU process-wide, -37 % on the game's workers |
| GPU deswizzle in a compute pass (T164) | 5-11 ms CPU uploads gone |
| Submissions split every 400 draws (perf 10-20) | 49 -> 60 fps at 4K (the GPU starts while recording continues) |
| Async render worker with fence tickets (rq_*) | +24 % worst case |
| One frame in flight above 60 fps (frame lag) | 133 -> 162 fps; not at 60, where it only added latency |
| VRAM mirrors of transform-feedback and store-written vertex ranges (T175 redo, T197) | -37 % GPU (grass read over PCIe before). Off on iGPUs (no PCIe; it only cost memory). |
| Barriers narrowed from full to tracked / memory / graphics-only (T162 parts 1-4) | -6.6 % GPU |
| Render-thread memo of last program / format | -12 % exec |

**Shader stutter** (the big one for users)
- Record every pipeline variant used (`cache/variants.bin`); prewarm a program's variants when the game registers it
  on a loading screen (T163).
- **Precompile from the RomFS SPCH containers** (T187): 11,649 shaders, 188 s on the dev PC, re-run after every exe
  change (stale precompile = T211 part 1).
- Vulkan graphics pipeline libraries: link first (~0.3 ms) and swap in the optimized pipeline later (T188, T211, T212).
- A shipped variant seed (T211 part 3); precompile reading SPCH input / texture names to guess integer variants (part 4).
- Prewarm queue big enough for an area's ~1,000 programs (T218: it silently dropped all but 256 -> 1.5 s freeze).
- Translator lock: waiting draws go first (T200).
- Pipeline-cache save on its own thread (T209: ~100 ms freeze every 2 min).
- Known limit: the NVIDIA driver's shader cache defaults to 1 GB and evicts the libraries (T215 note); keep them in
  our own file.

**Other**
- QPC -> TSC fallback on slow-QPC PCs (T190).
- Hybrid-CPU confinement (R0).
- Fewer workers on <= 6 threads (R4).

### Did not work (do not repeat without a new reason)

| Tried | Result |
|---|---|
| Guest registers as C locals (T165) | x86-64 has ~14 GPRs vs 31, so it spills anyway; +5.6 % instructions |
| `-march=x86-64-v3` (AVX2 / FMA) for the generated code | worse than restrict alone; Zen+ splits 256-bit ops. Also, nothing given out may contain AVX: scan every exe (`objdump -d \| grep -cE "zmm\|%k[0-7]\|ymm"` = 0). |
| Descriptor-set reuse / caching by content (several times, also Wonder eabf8a4) | hashing costs what the driver saves (NVIDIA writes sets cheaply) |
| Descriptor update templates | no gain |
| Extended dynamic state 3 / dynamic vertex input / push descriptors | ~1 pipeline per program anyway; not worth it |
| GPU-resident copies of GPU-only heap ranges, first version (T175) | grass missing; the "saving" was grass not drawn |
| Per-frame target clears off on iGPUs (R6a) | some effect reads them; pixels change |
| Key / program memo by state generations | the game changes key state between almost all draws |
| Locking our pacing to DWM vblanks (T199) | unreliable; FIFO present at 30 / 60 is the answer |

---

## 4. Frame rate, pacing, timing

1. **The game's own limiter** busy-waits on the system tick (T157).
   - Its interval (2 = 30 fps) is an int behind a pointer, and the period constant (0.997) is in rodata.
   - 60 fps: force interval 1 every frame.
   - > 60: scale the period constant.
   - Find the limiter by profiling a frame that waits.
2. **World speed is dt-based** (checked: same in-game clock / positions at 30 / 60 / 120 with time-scaled routes).
   Exceptions are **frame-count thresholds**: field followers fell behind at 60 because "restart after > 9 frames" ran
   twice as often (T210). Patch such compares to scale with the frame rate. Expect more of these in XC2.
3. **Cutscenes animate characters on alternate frames at 60** (T224).
   - The pose is sampled every other frame while the camera moves every frame: it looks like 30 fps / vibrating hair.
   - The gate was never found (a global 30 fps tick f_70007b4b00 was found, not the cause).
   - The shipped answer: cutscene detection, then cutscenes at 30, FIFO presenting each frame exactly twice on 60 Hz.
     Optionally FSR 3 frame generation only in cutscenes (launcher "Frame generation in cutscenes only").
4. **Present mode:** FIFO at 30 / 60 (the Switch holds frames to vblanks; mailbox drifted: "laggy at a steady 60",
   T199). At 30 on 60 Hz, present each frame twice (flat 33.3 ms in the user's frametime graph).
5. **External caps fool measurements:** RivaTuner's global limit, NVIDIA forced vsync, a hidden test window composed
   at 60 by Windows (T156).

---

## 5. Upscalers and frame generation (FSR 3.1 / DLSS / FSR 3 FG)

1. **The camera comes from the scene draws' vertex constant buffers** (a 512-byte buffer with view 3x4 + projection,
   row `0 0 -1 0`).
   - Jitter every draw into a depth image of the scene depth's size. Jittering only the scene depth's image removed
     geometry: the depth prepass and the EQUAL colour pass use different depth images.
   - The jitter must start at the frame's first scene draw: the game writes the window image early, and a wrong
     "HUD began" trigger turned jitter off for everything (T213 follow-up).
2. **The game's velocity buffer (gTVelocity) is camera-only.** It correlates 0.993 with our own camera motion (T228
   study). Moving characters / grass need real per-object vectors (T228 design: redraw with previous positions; not
   done). Without them they look aliased under DLSS / FSR while moving.
3. **HUD:** the upscalers need the image before the HUD. Snapshot at the end of the scene composite and add the HUD
   back after upscaling (T213 / T216 / T220).
   - Watch for passes that composite the scene and draw HUD glyphs in the same pass: split after the first draw.
   - Never jitter HUD draws.
4. **DLSS through Streamline in manual-hooking mode**: instance / device extensions at creation, swapchain calls
   through its proxies.
   - For DLSS + FSR 3 frame generation, Streamline must see the swapchain (hand out its proxies through the FG
     backend's function table, `fgsc_proc`), or it hangs.
5. **FSR 3 frame generation swapchain:** count images first, then fetch. Asking for 8 at once crashed the driver on
   AMD's 3-image swapchain (T204).
6. Give FG a **HUD-less** image too, or the HUD smears.
7. The user's verdict: FG at 60 in gameplay felt wrong (input-latency / pacing). FG only in cutscenes (which run at
   30) is what they kept.

---

## 6. Game-specific mods and UI (methods transfer, addresses don't)

**Options in the romfs.**
- `lib_nx.ini` holds the game's TAA / AA / motion blur / fur blur: an edited copy served from memory gives a "game
  blur off" option (T198).
- The DOF chain is identified by program hash; skipping its splat + composite gives a DOF option (T183).
- Mods layer `mods/<name>/romfs/` (Ryujinx layout) with per-mod on / off (T203).

**Party switch, XC3-style (T206).**
- The method: find the party manager by vtable, then call the game's own set-leader + rebuild-follower-group +
  focus, as its Party menu does.
- In battle, also re-point the HUD's character handle and set its rebuild bit.
- Refuse in menus / cutscenes: player-control flags + per-action lock counters.
- Controller: hold L2 + L1 / R1. L2 alone is sent as a short press on release.

**Keyboard + mouse (T230 / T236).**
- One key per Switch button was not enough: added a second key per input, mouse buttons / wheel as bindable keys, and
  actions.
- **Arts hotkeys:** find the palette cursor (vtable + offset, pattern search). Press the d-pad until it reaches the
  slot, then A. Writing the cursor doesn't move the game's selection. In XC2 the arts are on face buttons: check
  first, a macro may not be needed.
- **Mouse camera.** The game's right-stick camera has a dead zone (~15 %) and a curve (50 % stick -> 30 % speed),
  and is capped at a top speed (~0.07 rad / frame).
  - The mouse through the stick feels wrong whatever the scaling: small moves are lost, flicks queue behind the cap.
  - **The fix is writing the camera object's yaw / pitch directly** (found by the float search, poke-tested; the game
    clamps the pitch itself). It applies only with the player in control, with the stick conversion as the fallback
    in menus.
  - Exceeding the stick range (values beyond 32767) is not usable: asymmetric, it stops at 3-4x.

**Button icons.**
- Atlases `menu/image/icon_button*.wilay`, `button.wilay`: LAHD, one BC7 mibl, 8 x 4 cells, cell order differs in
  `button.wilay`.
- Single glyphs inside screen layouts (`mnuXXX_cont*.wilay`, **LAGP**, many textures each). Found by diffing what a
  community Xbox pack changed.
- Keyboard icons are generated at startup from the bindings (`runtime/services/kbicons.c`):
  - decode with bcdec (BC7);
  - take the game's own key shape as template and erase its label (non-face pixels not connected to the edge);
  - draw the key name (symbols ⇧ ↵ ␣ ⌫ and arrows drawn as shapes; long words are unreadable);
  - re-encode BC3 with 1 mip in place (same space as the original, nothing else in the file moves);
  - cache by a hash of the bindings (~7 ms).
- The game accepted raw LAHD / LAGP where the original was xbc1.
- **Community icon packs (GameBanana) are CC BY-NC-ND:** install for yourself only; never redistribute (not in the
  repo or the friend's folder).

---

## 7. Platform / runtime pitfalls

1. Files the game opened were never closed (no `on_close`) -> DeleteFile failed -> crash saving over a save (T208).
2. Intermittent hang: condvar timeout returning without the mutex (T067); lazy-commit race (LAS 2332e74).
3. Movie decoder: the game reads the output from its own buffer (T118). One silent movie track was the file's own (T171).
4. Audio crash: the movie's own IAudioOut buffers (T170).
5. Thread stacks: 64 MB for shader-build threads; NVIDIA driver threads start with 64 KB (T191).
6. Laptops: export NvOptimusEnablement / AmdPowerXpressRequestHighPerformance (T194).
7. Windows heredocs: Python / bash heredocs turned `\n` inside C strings into real newlines several times. Write edit
   scripts to a file, or use the editor. `windows.h` defines `far` / `near` and `MB_*` macros: avoid those identifiers.

---

## 8. Process lessons (how the work was organised)

**Builds**
- Test exes always under their own name (`XCDE_EXE=build/xcde_p<n>.exe`).
- The user's `build/xcde.exe` is replaced only by a **clean worktree build** of a committed HEAD, AVX-scanned, backed
  up as `<work dir>/xcde_<hash>.exe`, and noted in HANDOFF.md.
- A friend's copy goes in `build/tester/`.

**Tests and evidence**
- At most 3 game runs at once (more made GPU timings meaningless).
- Bulky data (frames, dumps) on `E:`.
- Every perf change needs captures in the noise band before it is kept.
- When an attempt fails, record it with numbers (§3 "did not work" saved repeated work twice).

**Working with the user**
- The user tests on an RTX GPU PC, 4K, 60 Hz; a friend tests on an Intel laptop iGPU.
- Their screenshots + a description were the best bug source; ask for the spot / save when not reproduced.
- Short answers in Spanish; keep working without asking between steps; ask only when blocked or a choice is really
  theirs (e.g. what feels right).

**Other projects**
- Read other recomps' histories (LASRecomp, Let's Go, Mario Wonder, TotK Mac, Metroid Dread, Astral Chain, SSBU,
  WindowSmash): several bugs were already solved there (`docs/lessons_*.md`).
- Ideas only, never copied code.

---

## 9. Open at the end of XCDE (may matter for XC2 too)

- T228 per-object motion vectors for DLSS / FSR (design written).
- T224 cutscene 30 fps pose gate (worked around).
- Tutorial images and `font_icon` keyboard icons.
- Mouse camera, L2 + L1 / R1, and arts 1-8 still to be confirmed by the user on real hardware.
- iGPU checks: T196 AMD checklist item c; the R3 / R7 items waiting for a tester's picture.
- Soak beyond 69 min after the table fix; T185 private-memory growth explanation.

---

## 10. Shaders, pipelines and first-viewing glitches (added 2026-10-24, T240)

**Goal the user set:** no graphical glitch on any GPU, in cutscenes or gameplay; a short stutter is acceptable, a
wrong image is not.

### Debugger tours: collect every pipeline the game can draw

Do this early in XC2. It is what makes the shipped precompilation complete.

- **Teleport.** The map-jump request, the same call the game's own warp uses: `f_70000e19f0(jump manager, req)`. The
  request holds area / sub-area as u16, then x, y, z and a rotation.
- **Cutscene by name.** The scripts' `realtimeEventPlay` native, found through the script binding table in `.data`
  (name pointer, function pointer pairs). The other natives in that table are the way into the other event kinds:
  `eventStart`, `simpleEventStart`, `kizunaTalkStart` (heart-to-hearts), `battleEventStart`.
  - A cutscene's length is in its header: `cs/<name>.pcbeh` +0x4c, frames at 30 fps.
  - "Has a scene started" is a counter in the event manager. The playing flags miss some scenes.
- **Tour points come from the game's own tables.** Landmarks, enemy spawns (`poplist`), collectibles, gimmicks and
  locked areas, thinned to one point per 150-unit cell, with a camera spin at each point.
  - Check the units: XCDE's `Gimlist` / `FieldLock` positions are in hundredths. Read raw, they sent the party off the
    map and crashed it.
- **Battles.** The tour steps:
  1. Resolve entity handles 1..4095 with the game's handle-to-object lookup. Character objects include the enemies.
  2. Jump next to the nearest one that isn't in the party.
  3. Press R to target and A to attack, and fire an art every few seconds through the arts-hotkey macro.
  - Use a 100% save, so every character and their arts are drawn.
- **Run the tours as many short jobs in parallel.** One boot per scene or zone, each in its own slot folder with its
  own `cache/variants.bin`, merged at the end into `data/variants_seed.bin`.
  - Coverage check: the user's own play cache compared with the tours' list. 98.6% was already in the tours.
- **The in-game flicker scanner finds glitches without anyone watching.** It is a cheap per-frame block diff that
  saves only the suspicious frames. Look at the contact sheets: most hits are just motion.

### Precompile the final pipelines, not only shaders

- **What the launcher builds:** for every recorded variant, the whole optimized pipeline, into the driver's cache.
  - This is not the fast-linked GPL pipeline: that one gets swapped for the optimized one a few frames later, which
    is a second compile.
  - XCDE: 29,616 pipelines in about 50 s on 15 threads, about 1.1 GB peak.
- **Test cold.** Move the NVIDIA cache (`%LOCALAPPDATA%\NVIDIA\GLCache`) aside and always put it back. A warm driver
  cache hides everything; that is why the glitches stopped reproducing after the tours.

### The first-viewing glitches were races with the render worker, not shader waits

These four bugs, plus the fifth item below, are likely in any LASRecomp-based port with an async render thread. Fix
them up front in XC2.

**Symptoms:** Shulk's hair black, faces with another material's texture, Reyn's face missing or his body drawn as his
weapon.

**Why they appeared:** when the worker lags behind (a pipeline compile, a cold driver cache, a slow PC), it records a
command list after the game has already changed what that list refers to.

1. **`BindProgram` recorded the program object.**
   - The game sets new shaders on that object, or finalizes it and a new one gets its memory.
   - Fix: record an immutable frozen copy of the shaders.
2. **Shader code was translated from game memory late.**
   - A freed blob translated as zeros, and the program stayed failed for good, because programs are keyed by content.
     Its draws were then skipped.
   - Fix: copy the blob when it is registered (that is also the moment its hash is computed).
3. **Texture and sampler pool registrations applied immediately.**
   - Fix: queue them and apply them in command order.
4. **`nvnTextureCompare` compared addresses.**
   - NVN compares the texture's state. SavageWindRecomp found this through trees "exploding".

**How the cause was found:**
- Cold A/B runs ruled out every guess: prelink, texture streaming (re-checking every texture every frame) and pipeline
  waits (synchronous builds still glitched).
- Then per-draw logging of "the shader samples type X but the slot holds type Y, so black". It matched the glitch
  frames exactly.

**Also:**

5. **A 3D texture sampled by a 2D lookup reads its first slice on the Switch.** Give it a 2D copy of slice 0, not a
   black dummy.

### Lessons

- **"Shaders" is the first guess for a first-time glitch, and it can be wrong.** Check whether the image is wrong or
  just late. A pure present hitch caused nothing; a slow pipeline build did, through the races.
- **Holding frames at load or scene start makes the game drop cutscenes.** Don't stall a scene's start; precompile
  instead.

## 11. From the review of 20 other recomps (added 2026-10-25)

The general, game-independent notes are in `docs/RECOMP_KNOWLEDGE.md` (keep that file whole: XC2 / XC3 / XCX may hit
items XCDE never did). This section says what XCDE took from them and what must be re-measured per game.

**Carries over as is (same runtime family):**
- Kernel: the condvar key is set before the mutex is released (`svc_wait_process_wide_key`); WaitForAddress /
  SignalToAddress change the word with compare-and-swap. Both were lost-wakeup / lost-update hazards that look like
  rare random hangs.
- The async render worker starts through `pthread_once`.
- The memory-region table holds 16384 entries and logs at 1024 / 4096 / 12000 (long sessions).
- Translator: SSY / PBK / PCNT stacks resolved at translation (`resolve_stacks`): no run-time stack arrays in 3002 of
  XCDE's 3006 programs that use them (NVIDIA lost writes / GPU resets and AMD scratch memory in other ports).
  `XCDE_STATIC_STACKS=0` turns it off.
- Measuring before fixing: `XCDE_XLAT_STATS=1` with `--precompile` prints, per program, the fragile constructs
  (SSY / PBK, BRX, BAR, FMZ multiplies, SHFL in vertex shaders, stacks resolved). Run it first on a new game: in XCDE
  it showed which of the other ports' translator bugs could matter (only the stacks) in five minutes.

**Not used by XCDE, so not fixed here - re-measure in XC2 / XC3 / XCX before assuming the same:**
- Compute shaders: XCDE dispatches none ("0 dispatches" in every log). Other games do, and then these matter:
  `barrier()` inside the translated branch state machine (divergent warp: AstralChain's exposure went inf / NaN),
  compute subgroups of 32 (`requiredSubgroupSize`, RADV runs wave64), SR_LANEID / ballot.
- BRX (indirect branch) in shaders: 0 programs in XCDE; the translator marks every instruction as a target when one
  appears (slow; AMD may never finish compiling). Resolve the jump table if XC2 has them.
- FMZ multiplies (0 * inf = 0 on Maxwell): 0 programs in XCDE, not emulated.
- SHFL in vertex shaders returns the lane's own value: 1 program in XCDE (skinning in other games exchanges data
  between lanes).
- Transform feedback, TMML: not used by XCDE (0 translation failures over 307 battle runs).
- `nvnCommandBufferSetDepthClamp`: a no-op that now logs once when called; implement it if the game calls it
  (other ports: shadow casters clipped, a near-plane card flickering).
- Movie / audio end-of-stream semantics, atomic saves (the save's Commit is a no-op here), the iGPU heap import window
  and VK_EXT_memory_budget (min-spec Vega 8): open items, see HANDOFF.md / RECOMP_KNOWLEDGE.md section 1.

**Tour data pitfall:** a debugger warp far outside the map (XCDE battle tour ma0601 e15: -7626 -2608 -1660) puts the
party under the world and the battle AI loops forever (render worker idle, main thread in game code). Check warp
coordinates against the map's range before calling a hang a runtime bug.
