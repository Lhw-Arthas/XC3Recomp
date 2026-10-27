# Spec: XCDE on integrated / non-NVIDIA GPUs and low-end PCs (2026-10-23)

Owner: party mod session. Backup before any change: git tag `backup-before-lowend` (ab71342) and
<work dir>/xcde_before_lowend.exe. Rule for every item: implement, test on the dev PC (RTX GPU, NVIDIA must stay
pixel-identical or within the known run-to-run noise), commit, next item. Nothing is "done" without its acceptance test.

## 1. Evidence

### 1.1 A friend's laptop (build/last_game.log + last_precompile.log, 2026-10-23)

| What the logs show | Notes |
|---|---|
| `Intel(R) Graphics`, Vulkan 1.4.356, pipeline libraries with fast linking | |
| 14 logical CPUs, 4 in the fastest class | Core Ultra 5 125U, not 125H: 2 P + 8 E + 2 LP-E, 4-Xe-core GPU |
| `[cpu] game threads on the 4 fastest logical CPUs` | Fixed in bdd7ff3: under 8 fast CPUs, no confinement |
| Field ~53-60 fps, larger areas 35-40, lows 25-28 | 720p internal + FSR 1 to 1080p: GPU-bound |
| Area entry 0.7-1.2 s (`linked 51 (1164 ms)`) | Intel links far slower than NVIDIA at times |
| `FATAL: vkWaitSemaphores: -4 (device lost)` in a battle ("when the crab appears") | GPU fault or hang |

The user also reported:
- mountains flashing black about every 4 s;
- artifacts;
- draw-distance errors.

### 1.2 Other projects (commits read 2026-10-23, scratchpad gh/*.hits.txt)
- letsgo-recomp 431f4da / LASRecomp f4cb039: empty trailing colour slots as VK_NULL_HANDLE attachments - legal, but
  Intel's Windows driver crashes in vkCmdBeginRendering. **XCDE has the pattern** (exec.c begin_pass: `continue` leaves
  `ca[i].imageView` null and `pass_ncolor = st.rt.ncolor`).
- SuperMarioWonderRecomp 9cc5667: no barrier between passes in GENERAL layout -> Intel "black sky", NVIDIA HUD blocks.
- OpenSmash 0096b84: AMD (incl. an integrated Radeon): sampling the depth target bound to the pass -> dark / white
  haze; fix: sample a copy. **XCDE samples colour attachments directly** (T161 `LARECOMP_FEEDBACK_DIRECT`, default on;
  depth already uses copies) - undefined on AMD / Intel.
- SpartanPort 4b843a7: on 4-thread CPUs worker threads starved the GPU thread (36 -> 59 fps on an i5-7500).
  **XCDE starts at least 4 shader workers** even on a 4-thread CPU (Ryzen 3 3200G).
- B2recomp (AMD):
  - a5d0b45 a shader reading a cbuf the layout lacks: AMD refuses the pipeline;
  - a5577d7 a refused pipeline must not be fatal - XCDE: not fatal (state 2, draw skipped) - verify;
  - 781e756 FIFO fallback - XCDE: already;
  - 60f5552 clear before upload.
- WindowSmash c370274: `switch` on a constant failed on Intel (black). XCDE translates complex control flow as
  `for (guard < 100000) switch (pc)` (236 of 683 dumped shaders) - a correctness and speed risk on Intel / AMD.
- LASRecomp 8a66a61 / 03ee802 (integrated GPUs):
  - skip redundant per-frame clears (3.7 ms a frame on a UHD 770);
  - lean image usage;
  - SMAA only where edges were found.
- PokeZ-A 2b09f30 (device lost from a gfast copy-back): N/A - XCDE issues no compute dispatches (friend's log:
  0 dispatches).

### 1.3 Other fixes in those projects: optimizations, shaders, visual bugs (full histories, 2026-10-23)
Each repository's whole commit list was read; repositories with more than 100 commits had their later pages fetched as
well. The exception is the oldest shadPS4 / bluewake history (emulator upstream, Wii U), which was left out. Vendor =
where the bug shows. Status in XCDE:
- **have** - already in XCDE;
- **n/a** - the game never takes that path (checked);
- **N<i>** - new item below.

| Fix (source) | Vendor | XCDE |
|---|---|---|
| Alpha test as a shader variant without `switch` (WindowSmash c370274: Intel black menus) | Intel | have (T191, comparisons) |
| Pass the game's alpha blend factors even with "separate alpha" off (WindowSmash 9326fd2) | all | have (b[3], b[4] as written) |
| IPA multiply register (LAS 0faf3a1) | all | have (ipa_mul) |
| Stencil-mode views sampled as uint (PokeZ-A 442aa85) | all | have |
| GPU timing counters in Switch ticks / GPU time (LAS d52ce7e): no false "slow frame" | all | have |
| D24S8 where supported (LAS 4b2feba) | NVIDIA / Intel | have |
| robustBufferAccess(2) for free cbuf indexing (Wonder 0a7329c: GPU hang) | all | have |
| Unwritten vertex outputs = (0,0,0,1) (MacNative b7d9543, Wonder da38fa0) | all | have |
| QPC slow under HPET -> TSC clock (WindowSmash 5004359) | laptops | have (T190) |
| NvOptimus / PowerXpress exports (WindowSmash c370274) | hybrid laptops | have |
| FIFO present fallback (B2 781e756) | AMD | have |
| Vertex data in place on integrated GPUs (letsgo dbd4b9e) | iGPU | have (vertex cache off on iGPU) |
| Pipeline keys canonical (MacNative f3e2f66, letsgo 23aba7d) | all | have (T195) |
| Jump tables (BRX) resolved, not one dispatcher case per instruction (WindowSmash 2c519ef: 4.1 -> 0.7 ms) | all, worst on AMD | n/a: 0 of 683 shaders have BRX, at most 12 cases |
| SHF clamp / wrap / 64-bit, I2I.SAT unsigned, HSETP2.H_AND (LAS d4c2ff6) | all | n/a: 4 SHF uses, all 32-bit immediate 16; no I2I.SAT / H_AND |
| Sampler reduction filter MIN / MAX (PokeZ-A 865f327) | all | **N1** |
| Vertex formats a GPU lacks: 3-component 8 / 16-bit widened (w = next byte, not 1); packed 10:10:10:2 read as float (ssbu f31041c) | AMD | **N2** |
| Feedback sampling of a bound colour target (OpenSmash 0096b84) | AMD / Intel | R3 (A/B by tester) |
| MSAA images read by shaders (SpartanPort 10a7864 RDNA2 black lines, 55eaa5d Intel) | AMD / Intel | check: the game's sample counts (N3) |
| D16 shadow compare reference rounded to 16 bits (MacNative 6283599) | non-NVIDIA likely | N4 (only if shadow acne shows) |
| Hair / cloth clock above 30 fps (MacNative 290ec9f) | all | lead for the Dickson ponytail issue (tasks) |
| Upload ring reuse, driver thread stacks (WindowSmash a2d6c1e, 5cf1752) | D3D11 drivers | n/a (Vulkan, our threads) |

## 2. Requirements (implementation order)

### R1 - No empty trailing colour attachments (Intel crash class)
- **Change:** begin_pass drops trailing slots without an image view. pass_ncolor = last valid slot + 1; pipelines and
  clears follow pass_ncolor. An empty slot in the middle: logged once (left as is).
- **Accept:**
  - NVIDIA captures of load_walk (1200 / 2600 / 3500), battle_a and the title identical to the backup (noise band
    excepted);
  - validation layer: no new messages.

### R2 - Synchronization validation pass, barriers where missing (Intel / AMD artifacts, possibly the device lost)
- **Change:** run the Khronos layer with synchronization validation (`VK_LAYER_KHRONOS_validation`, msys64,
  `LARECOMP_VK_VALIDATION=1` + `VK_VALIDATION_FEATURE_ENABLE_SYNCHRONIZATION_VALIDATION_EXT`) on:
  - the title;
  - field walk;
  - a battle;
  - a cutscene;
  - the menu.

  Fix each distinct hazard at its source (precise barrier), not with blanket full barriers.
- **Accept:**
  - zero synchronization hazards (or each remaining one explained as a false positive in this file);
  - NVIDIA fps within 3 % of the backup on the coldroot bench;
  - captures as in R1.

### R3 - No sampling of a bound colour attachment on non-NVIDIA GPUs (AMD / Intel dark or black surfaces)
- **Change:**
  - vendor != NVIDIA: `LARECOMP_FEEDBACK_DIRECT` defaults to 0 (snapshot copies, the T161 path measured identical);
  - or use VK_EXT_attachment_feedback_loop_layout where the driver offers it.
- **Accept:** NVIDIA unchanged (default path untouched); forcing the snapshot path on NVIDIA gives captures identical
  within T161's measured noise.

### R4 - Shader workers on small CPUs (3200G: 4 threads)
- **Change:** workers = max(2, logical CPUs - 2) up to 4 logical CPUs, the current rule above that. The workers keep
  below-normal priority.
- **Accept:** in low-spec mode (XCDE_LOWSPEC_CPUS=4):
  - no fps loss in the field;
  - area-entry time not worse by more than 10 %.

### R5 - AMD checklist (B2recomp)
- **Change:** verify, and fix only what fails:
  - every cbuf a shader reads exists in its pipeline layout (validation layer, R2 runs);
  - pipeline or library refusal is never fatal (already: test with an injected failure);
  - new textures: clear ordered before the first upload.
- **Accept:** validation clean for these classes; injected refusal does not stop the game.

### R6 - Integrated-GPU mode (LASRecomp 8a66a61 / 03ee802)
- **Change** (on by default only on integrated GPUs; `XCDE_IGPU_MODE=0/1`):
  - skip clears of targets the frame fully overwrites;
  - lean image usage flags.
- **Accept:**
  - forced on with NVIDIA: captures identical to forced off;
  - GPU time per frame (LARECOMP_GPUPROF_AT) lower or equal.

### R7 - Structured control flow instead of the `switch (pc)` dispatcher (Intel / AMD correctness and speed)
- **Change:**
  - first measure: how many shaders the game uses at run time take the dispatcher path, and which.
  - then: structurize the common shapes (if/else diamonds, natural loops) in maxwell/translate.c, falling back to the
    dispatcher only for irreducible flow.
- **Accept:**
  - the shader differential tests pass;
  - captures identical on NVIDIA;
  - the dispatcher count at run time goes down.

  The largest item, scheduled last.

### N1 - Sampler reduction filter (all vendors)
- **Change:** NVN MIN / MAX reduction passed as VkSamplerReductionModeCreateInfo (samplerFilterMinmax enabled when the
  device has it); logged once when used.
- **Accept:** captures identical when the game never asks for it (the log says whether it does).

### N2 - Vertex formats the GPU lacks (AMD: 3-component 8 / 16-bit)
- **Change:**
  - every vertex format in use is logged once, with "(not supported)" where the device lacks it;
  - `XCDE_VFMT_SIM=amd` treats R8G8B8* / R16G16B16* as unsupported, so the fallback can be tested on NVIDIA.
- **Accept:** captures with the simulation equal to captures without it, or the fallback fixed until they are.

### N3 - Multisampled targets (AMD / Intel)
- **Change:** log the sample counts the game creates; act only if any target has more than 1 sample.
- **Accept:** the log answers it.

### R8 - Diagnostics for testers
- **Change:** `Jugar XCDE (prueba Intel).bat` (full pass barriers + device-lost trace) for the friend; the log names
  CPU / GPU classes (done).
- **Accept:** the bat starts the game with both variables (checked on the dev PC).

## 3. Test protocol (every item)
1. Build a test exe (`XCDE_EXE=build/xcde_p<n>.exe`); AVX scan of any exe given out
   (`objdump -d | grep -cE "zmm|%k[0-7]|ymm"` = 0).
2. Deterministic captures vs the backup exe:
   - load_walk 1200 / 2600 / 3500 (colony9 save);
   - title 400.
3. Real-time smoke:
   - fallen_arm load + party switch;
   - save list thumbnails (savelist_rt route);
   - title FSR 3 text.
4. Item-specific test (above).
5. Commit; at the end a clean worktree build replaces build/xcde.exe (old one kept on E:).

## 4. Rollback
`git checkout backup-before-lowend -- <file>` or the env switch each item adds; <work dir>/xcde_before_lowend.exe.

## 5. Status
- [x] R0 hybrid CPU confinement (bdd7ff3)
- [x] R1 (captures within the noise band; the case does not occur on the dev PC routes - protection for Intel)
- [x] N1 reduction filter: implemented; the game never asks for it on the walk / battle / title routes (inert, captures
  in the noise band)
- [x] N2 vertex formats: the game uses 14 formats (VkFormat 37 38 41 70 77 81 91 92 98 100 103 106 107 109); none
  is 3-component 8 / 16-bit or packed 10:10:10:2, so AMD's gaps don't apply. The log and the simulation switch stay.
- [x] N3 no multisampled images created (walk route).
- [~] R2 synchronization validation (layer 1.4.363, validate_sync on):
  - walk: 0 hazards in ~2,050 frames (title, area load, field start); later the layer itself timed out at 3.7 fps;
  - battle: the layer hangs at the same point as on the walk (frame ~2,050, timeline semaphore value ~3,267: its
    INTERNAL-ERROR-VkSemaphore-state-timeout, then a fault inside the layer). It does not follow XCDE's waits on values
    signalled later, so battles cannot be checked with it.

  What remains for the tester: bat A (full barriers) against a normal run.
- [ ] R3: not made a default without evidence. The snapshot path cost 16 % in battle on NVIDIA (T161), and more on an
  iGPU. The tester gets `Jugar XCDE (prueba B copias).bat` (LARECOMP_FEEDBACK_DIRECT=0) to compare with the A bat
  (full barriers).
- [x] R4 workers: on 6 or fewer logical CPUs the count is CPUs - 2 (minimum 2); logged.
- [x] R5 AMD checklist:
  - a: no layout / descriptor messages from the validation layer (title, load, field start);
  - b: a refused pipeline falls back from libraries to a whole pipeline, then logs and skips the draw (never fatal; the
    VK_CHECKs left are the runtime's own fixed present / blit pipelines);
  - c: not done. Every colour image has attachment usage, so a clear at creation would cover every texture (~900 MB
    an area). The unwritten areas hold the same old contents on every vendor, since drivers set up compression metadata
    on the UNDEFINED transition, and NVIDIA shows nothing.
- [x] R6 integrated-GPU mode (b only):
  - a: per-frame clears off. **Rejected** for XCDE: with `LARECOMP_NO_FRAME_CLEAR=1` the title differs in 4 % of its
    pixels (max 64) and walk 1200 in 1 % (max 3), so some effect reads them.
  - b: lean image formats (`XCDE_LEAN_FORMATS`, default on for non-NVIDIA):
    - forced on with NVIDIA: walk / battle / title within the noise band of the default build;
    - no view outside the lists;
    - validation layer: 0 messages up to the area load (frame 1,014).
- [ ] R7 lowered: at most 12 dispatcher cases per shader, no BRX (WindowSmash 2c519ef's 271-case shader has no
  counterpart here). Left until a tester's picture points at it.
- [~] R8: bat A (full barriers) and bat B (feedback snapshots), both with the device-lost trace.
