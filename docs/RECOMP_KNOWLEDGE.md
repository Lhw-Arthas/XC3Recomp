# Recomp knowledge base: lessons from 20 public ports (reviewed 2026-10-24)

What the other static recompilations and native ports learnt, sorted by topic, for this project and for any
future recomp (Switch or not). Ideas only: no code was copied (several of these projects are GPL).

Raw notes, one line per commit or issue with its hash: `<work dir>\research\notes.md`. Source dumps:
`<work dir>\research\commits_*.txt` and `issues_*.txt`. Older per-repo notes, already mapped to tasks:
`docs/lessons_other_recomps.md`, `docs/lessons_windowsmash.md`, `docs/lessons_astral_ssbu.md`,
`docs/lessons_perf_recomps.md`.

Status words used below, for XCDE:
- **done**: already in XCDE.
- **check**: may affect XCDE, not verified yet.
- **idea**: an improvement to consider.
- **n/a**: does not apply here (reason given).

## 1. The checks most likely to matter for XCDE (ranked)

These are the bug classes that showed up in two or more projects with the same runtime family as XCDE
(LASRecomp / ssbu-recomp / SuperMarioWonderRecomp, NVN -> Vulkan). Each one is a real bug someone shipped.

1. **FMA on CPUs without FMA3.** Guest `FMADD/FMLA` lowered to `fma()/fmaf()` falls back to the C library's
   software version: wrong results or NaN (zig's libc), exploding vertices (PokeZ-A #2). letsgo 628b1d0 and SavageWind
   ae42014 wrote an exact soft FMA (round-to-odd in double; checked bit for bit over 300-640 M cases).
   *check*: our no-AVX baseline; how fused ops are lowered; speed on the 3200G (it has FMA3, so runtime dispatch is possible).
2. **FPCR.FZ and the compiler.** FZ applied as MXCSR DAZ/FTZ at run time, but clang assumes IEEE denormals and
   folds them away: build the game code with `-fdenormal-fp-math=dynamic` (SavageWind #39). FZ must also flush
   where DAZ made a compare equal (SavageWind f3963fa). Rounding-mode switches per instruction cost a third of the
   game threads (PokeZ-A 1882c28: read/write MXCSR directly; cd0ce96: FZ-only ops on the native path). *check*
   Also build with `-fno-math-errno`: with math-errno on (dod3 3376743), `sqrtf` and similar become CRT calls. *check*
3. **NVN alpha test.** `nvnColorStateSetAlphaTest` + `SetAlphaRef` (float in `s0`) stored and never applied: blood
   splashes drawn solid, menus' stencil masks as whole quads (AstralChain 36e69eb, WindowSmash d33a166, AC-Recomp
   NVN_GAPS). Fix: fragment key carries func + ref, discard; drop EarlyFragmentTests while the test is active.
   On Intel, write the comparison as selects, not a `switch` (WindowSmash c370274). *check*
4. **Compute barriers inside a divergent warp.** The translated state machine can reach a `BAR` one iteration
   after the rest of the warp; host `barrier()` in divergent control flow is undefined, and NVIDIA released it early.
   As a result, the average-brightness shader summed stale shared memory, the exposure read inf or NaN, and the
   brightness pumped (AstralChain d1bc81e). Fix: park threads until the whole subgroup is there. Also force
   `requiredSubgroupSize = 32` on compute, because RADV runs wave64 and ballot-based counting breaks (PokeZ-A d83648c).
   *check* (XC tonemap and exposure)
5. **Feedback loops per mip level.** A pass writing level n of a texture from another level of the same texture.
   This covers the bloom pyramid going up (sampler pinned to level k > n, SavageWind 5cc815c) and Hi-Z built level
   by level (PokeZ-A 7995e46). A snapshot of "the levels under the one written" or of level 0 only gives blocky glow
   and missing objects. *check* (XC bloom/DOF chains; memory notes say ours samples attachments whole and
   T161 tells mips apart, so re-verify on bloom)
6. **Audio EOS / voice position.** At end-of-stream boundaries the voice's played-sample position must reset.
   Without it the streaming player counts again, the cinematic clock runs ~2x and music cuts out halfway
   (Metroid Dread f74890c, shipped broken by default). The movie demuxer must return the real EOS code `0x2000`
   (letsgo #16). After EOS, offer exactly one end-of-stream output and no more input buffers (ssbu-recomp 43e858e,
   ACNH 0a90e5b). *check* (pending "video EOS test")
7. **Clear then upload without a barrier.** A new image cleared to zero and then filled, with nothing between:
   AMD lets the clear win, giving blank icons and letters (B2recomp 60f5552). Related: `vkCmdClearColorImage` on a
   BC image is invalid and kills the whole submit on MoltenVK; zero-fill with a buffer copy instead
   (AC-Recomp BC_ZERO_FILL). *check*
8. **Vulkan things NVIDIA tolerates and AMD/Intel do not.**
   - A dynamic state declared but never set in a command buffer: RADV hung forever (PokeZ-A 13b5280, *done* here).
   - A shader binding the pipeline layout lacks: AMD refuses the pipeline (B2recomp a5d0b45).
   - Integer textures through float or linear samplers (PokeZ-A 71ab3ff, partly *done*).
   - A sampled view of a depth-stencil image with both aspects: device lost on AMD (issn ba070ff).
   - A depth+stencil blit with both aspects in one region: dark box on RADV (B2recomp #55).
   - Trailing empty colour slots passed as VK_NULL_HANDLE: Intel UHD 630 crashes in vkCmdBeginRendering
     (letsgo 431f4da; also a tester's Intel crash?).
   - Submitting the command buffer being recorded and continuing to record into it: AMD driver crash (SpartanPort 1d34202).
   - Depth sampled while attached in GENERAL layout: AMD shows fog and haze wrong (ssbu-recomp 0096b84, copy the depth).
   - A point topology with no PointSize written: GPU hang on RADV with graphics pipeline libraries (SavageWind bc13314).
   *check* each
9. **Required extensions.** `VK_EXT_vertex_input_dynamic_state` is missing on AMD Polaris (RX 400/500) and MoltenVK,
   and is broken on the Intel Windows driver (HD 630: 3D renders black or blue only). Put the vertex layout in the
   pipeline key instead (B2recomp 1642dd6, ssbu-recomp 030ff71, SpartanPort #214). AMD Windows offers no MAILBOX, and
   IMMEDIATE tore mid-frame, so fall back to FIFO (B2recomp 781e756). Old Vulkan loaders lack the 1.3 exports, so get
   1.3 functions with vkGetDeviceProcAddr or the exe won't start (PokeZ-A cf910d1). *check*
10. **iGPU memory (our Vega 8 min-spec).**
    - The device-local heap is the BIOS carve-out (256 MB). Allocations must fall back to the next memory type, and
      the GC must compare against the driver budget, not the sum of heaps (SpartanPort #532, which is a Vega 8 report).
    - Importing a multi-GB guest heap as a host pointer is revalidated by amdgpu at every submit (87% of the render
      thread on the Deck). Import a 256 MB window on iGPUs (PokeZ-A c72125e / #10).
    - VMA's estimate put a buffer in system RAM although VRAM had room: check VK_EXT_memory_budget and
      maxMemoryAllocationSize (axylpup 470d8979).
    *check* on Vega 8
11. **Logging stalls.** An unbuffered stderr with a stats line written in pieces costs 35-70 ms or one late frame per
    report (AstralChain 7717825, B2recomp 38ddc7d, dod3 29d841b: WriteFile up to 385 ms with the antivirus scanning
    the growing log). Write each report once, buffered, from a flush thread. Also: `getenv` per command took 26% of
    the render thread (UCRT lock plus environment walk, PokeZ-A cf910d1). We have many `XCDE_*` switches.
    A "first N times" log counter that keeps counting overflowed after 5.9 h and wrote 51 GB (dod3 d45fd8d).
    *check*
12. **XInput polling of absent pads.** The once-a-second probe on the game thread held the kernel lock 105-111 ms,
    which ran the sound queue dry (AstralChain 49da375). Dragging the window by its title bar ran Windows' move loop
    on the game thread and froze every guest thread (AstralChain 8e1ab24). *check*
13. **Texture identity.** Several patterns break identity:
    - The game finalizes and re-initializes a texture in the same NVNtexture object without re-registering its pool
      slot (letsgo 10812f1).
    - `nvnTextureCompare` compared addresses (*done*, T240).
    - Render-target images must be kept by storage, not by the struct, because the game re-inits its structs many
      times a frame (ACNH d0597c3).
    - NVNsampler objects copied with memcpy keep their description (SavageWind 1e98259).
    - Shaders re-loaded at addresses that held other shaders need a content-hashed cache key (letsgo 40853a5, *done* T125).
    *check* the rest
14. **Packaged texture layout and cube storage.** `GetPackagedTextureLayout` returns a presence flag and writes the
    layout through its 2nd argument. The block height is the low nibble (`0x403` = 8 GOBs), and guessing it permutes
    regions of big atlases (AC-Recomp RENDER_FIDELITY, AstralChain 100a2c3). `GetStorageSize` of a cube map is 6 faces
    even with builder depth 1, otherwise guest allocations overlap (AC-Recomp UNTILE_BC). *check*
15. **Command record memory over long sessions.** Records shadowed per list grew to 21 GB in 4 minutes. Retire them
    when the game overwrites the list. An outer list recorded once calls inner lists re-recorded every frame, so a
    re-recorded list must keep its handle (SavageWind #74/#83, f3963fa). *check* (memory notes say ours records into
    guest memory; re-verify over many area loads)

## 2. Maxwell shader translation

- **IPA in multiply mode** multiplies by its own register, not always w (PokeZ-A d1c2d8e, letsgo 0faf3a1; soft
  particles became tiled fog or opaque mist). *check*
- **LDC.64 / multi-destination ops** where the address register is also a destination: read the sources first
  (letsgo e243230). *done* (T127)
- **I2I.SAT** from an unsigned source, **SHF** clamp / wrap / `.W` / 64-bit modes, **HSETP2 .H_AND** (LAS d4c2ff6 via
  letsgo bf1c3da). *check* (T128)
- **SSY/PBK stacks**: an array indexed at run time made NVIDIA lose writes and loop until a TDR, and the array goes
  to scratch memory on AMD. Resolve the stacks statically, or keep them in 16 scalars (WindowSmash 316db6a, PokeZ-A
  5a9fb4a). Prefer structured if/else/do-while over a state machine: drivers compile it about 3x faster and the
  cache is 2.4x smaller (SavageWind 7edf74d). *check*
- **BRX jump tables** whose index the compiler shifted into another register (`IMNMX; SHL; LDC`). When unresolved,
  the whole shader became a dispatch loop, 4.1 ms instead of 0.7 ms (WindowSmash 2c519ef). *check*
- **Vertex position** must be exported after the translated control flow, or triangles go missing on NVIDIA
  (ssbu-recomp ce9a4af #47). *check*
- **Vertex-only programs** (depth or shadow passes) need an empty fragment stage; otherwise thousands of draws are
  dropped (letsgo f5bb2f3, PokeZ-A dd15d1e). *done* (T064)
- **BindProgram stage mask**: games bind separate programs per stage and NULL to disable one (letsgo #18, PokeZ-A).
  *check*
- **Lane ops**: `SR_LANEID` returned 0, so ballot-aggregated atomics counted nothing. `SHFL` in vertex shaders must be
  a real subgroup shuffle, because skinning exchanges bone data between lanes (PokeZ-A 7253341, 1882c28). *check*
- **TLD4 / TLD4S / TMML**: gather offsets, TLD4 offsets from RZ read an unwritten buffer (SavageWind #38), TMML via
  textureQueryLod (letsgo eafd615). *check*
- **Stencil-mode texture views** sample the stencil as uint (deferred lighting zebra stripes, PokeZ-A 442aa85). *check*
- **Layered rendering**: VS output attribute 0x64 is gl_Layer (a 3D LUT drawn as 32 instances, PokeZ-A b71de2f).
  *check*: compare with our slice0_copy workaround for the XC 3D LUT.
- **Half unpack**: exact conversion in vertex shaders, because NVIDIA runs native fp16 there and the depth prepass
  then disagrees with the colour pass. Native unpackHalf2x16 is fine in FS/CS (letsgo 77b975b). *check*
- **Legacy multiply** `V_MAC_LEGACY` / Maxwell `FMZ`: 0 * x = 0 (issn 86a31e2). *check* (T131)
- **Compute shaders of SDK 19+** start with a 0x100-byte header (PokeZ-A dd15d1e). n/a (our SDK)
- **A shared-memory array** must have at least one element (VUID 08737, issn ca6ecf9). *check*
- **Every translated SPIR-V should pass `spirv-val`**: amdvlk ends the process on invalid SPIR-V (issn 4ad58e5).
  *idea*: run spirv-val over the whole seed offline.

## 3. NVN semantics found missing in other runtimes

- `nvnCommandBufferSetDepthClamp` was a no-op. Shadow casters outside the light planes were clipped, and a near-plane
  effect card made the brightness flicker 150-200 times per 500 frames (PokeZ-A 4d5174e, AstralChain 3b6e02b). *check*
- `nvnDeviceSetDepthMode(1)` (NEAR_IS_ZERO) was ignored: the runtime always set negativeOneToOne clip control
  (AC-Recomp WINDOW_DEPTH). *check*
- `nvnWindowGetCrop` was unimplemented, which gave black frames. `nvnWindowSetCrop` must be honoured at present
  (handheld mode crops 1280x720 from 1600x900, AstralChain 683caa5). *check*
- Sampler reduction mode MIN/MAX (Hi-Z pyramids, PokeZ-A 865f327). *check*
- Blend factors: some runtimes copied the colour factors into alpha whenever "separate alpha" was clear. The game
  writes real alpha factors anyway, and yuzu uses them as written (WindowSmash 9326fd2). MIN/MAX blend with scale
  factors differs between PS4 and Vulkan (SpartanPort 9c88add). *check*
- `DrawArrays/ElementsIndirect` and `MultiDraw*IndirectCount` were no-ops. `ReportCounter SAMPLES_PASSED` wrote 0,
  so every occlusion-tested object was hidden (PokeZ-A 74f0c41). *check* (in the CHECK list already)
- **Timestamp counters**: the game converts Switch GPU ticks (614.4 MHz) to ns itself (x625/384). Writing ns made
  every interval 1.63x too long, and host time at translation counted as GPU time. The game then dropped to its
  30 fps mode, and its dynamic resolution sat at its floor (PokeZ-A d52ce7e, dd06cc7). *check* (XC dynamic resolution)
- `nvnSyncWait` on the window texture's sync can be answered at once. Queueing it behind the replay made the next
  frame's logic wait (B2recomp e95cbeb). nvnQueueFinish must not serialize the render thread with the game more than
  needed (letsgo #25: up to 2x when CPU-bound). *check* with our async worker
- `nvnSyncWait` returns ALREADY_SIGNALED / CONDITION_SATISFIED / TIMEOUT_EXPIRED and honours 0, finite and UINT64_MAX
  timeouts. `FenceSync` needs a completion object per execution of a reused list (AC-Recomp NVN_GAPS). *check*
- `nvnTextureWriteTexels` queued until the next sample: a movie writing YUV planes every frame grew memory by 1 GB
  every 30 s. Drop pending writes that a new one fully covers (AC-Recomp TEXEL_COALESCE). *check* (XC movie planes)
- `nvnTextureFinalize` raced a queue submit on another thread that read the texture through the pool (PokeZ-A
  8221824, 1977d86). *done* (stale pool entries, per memory notes)
- `CopyTextureToBuffer` must really be replayed: the game reads render targets back for shadows, exposure and save
  thumbnails (ACNH a0c197f, B2recomp 247617b, AstralChain thumbnails). *check* (T181)
- Format details:
  - NVN RGB5A1/RGBA4 bit order is the inverse of Vulkan's R5G5B5A1_UNORM_PACK16 (letsgo af6bfb4). *check* (T131)
  - An R8 texture sampled as (1,1,1,R) must be expanded for both pitch-linear and block-linear uploads (ACNH a6e6f75).
  - BC textures whose size is not a multiple of 4: D3D11 padding broke the coordinates (WindowSmash d33a166).
  - Packed signed 10:10:10:2 vertex attributes are not supported for fetch on some AMD hardware; decode them in the
    VS (ssbu-recomp f31041c).
  *check*

## 4. Pipelines, shader cache, precompile, stutter

- **Never skip a draw while its pipeline compiles.** This was proven again by four teams:
  - A draw the game makes once (precomputed lighting, baked textures) stays missing forever (ACNH bfe9052, AstralChain a04e781).
  - A skipped full-screen pass gives a black frame (PokeZ-A 302bd07).
  - One-off images such as the save screenshot need their draw (SavageWind 67909fd).
  *done* (our rule: stall over glitch). Keep the waits short: poll without sleeping for the first ~20 ms, and never
  loop on `sleep(1ms)` (AstralChain 7717825).
- **Lookahead pipeline prediction (the "combination prediction" idea).** MacNativeGames `docs/pipeline-prediction-stalls.md`:
  - On the first pipeline miss of a submission, scan the rest of the submission (state only, bounded to 8192
    commands, 64 keys, 2 ms) and work out the pipeline keys of the later draws.
  - Compile the missing ones on background threads. When a draw is reached, take its pipeline or wait only for the
    rest of its compile.
  - Also guess the other depth/stencil attach modes, free guesses no draw took two submissions later, and rescan
    from where a budget stopped.
  - Results: world entry 35.8 s -> 5.5 s of pipeline time, worst frame 8.7 s -> 2.7 s. Resolving not-yet-drawn
    programs from the translation index took a further case from 9.7 s to 4.4 s.
  - It costs no glitch: draws still wait, but for a fraction of the time.

  Variant combination guessing from recorded ones (LASRecomp 3e024a0, ~70% leave-one-out hits) and issn's
  permutation guessing with a holdout hit rate are the offline half of the same idea. *idea, high value*: in rq_worker,
  on a miss, pre-scan the recorded list and fan the missing keys out to the precompile threads.
- **Pipeline cache persistence**:
  - Save in the background a few seconds after builds settle, not only at clean exit, which closing the window never
    reaches (AstralChain 665591c, letsgo eafd615).
  - Write to a temp file and rename it, because a truncated blob boots to a black screen (SpartanPort edc6680).
  - Skip corrupted entries instead of stopping (issn 2cba1da).
  - Retry the rename, which fails about 1 time in 70 while a virus scanner holds the file (AstralChain d627f49).
  - Create the parent folder, otherwise the cache was never written (B2recomp 78a5ba5).
  *check* all
- **One file per cache entry is slow on Windows.** Defender scans each file and FLTMGR filters each open and close,
  which preempted the render threads 11-24 ms. The same 2 MB driver binary was copied into every file (20 GB);
  use a content-addressed shared store. A driver binary key is reused for different data, so name by content hash
  (SpartanPort #386). *check* (our cache layout)
- **NVIDIA keeps its Vulkan cache per executable name**: warm with the game's own exe (AstralChain df3f564). Our
  renamed test exes (xcde_pNNN.exe) therefore have separate driver caches, which affects cold-test readings. *check*
- Pre-built programs must stay in memory. Deleting them after saving made each one reload 10-20 ms at first draw,
  264 times in a session (Metroid Dread 4181349). *idea*
- Precompile threads need a memory budget (RADV shaders up to 1.3 GB each, SavageWind 66b110a). *done* (e34d4d7)
- Crash-safe precompile with an in-flight record and a skip list (issn). *done* (e34d4d7)
- Use one VkPipelineCache per compile thread, because a shared one is serialized by the driver. Give compute
  compiles priority over graphics (issn cabd380). *check*
- `VK_EXT_graphics_pipeline_library` fast link with the optimized pipeline swapped in later is the safety net for
  states nobody recorded: 26 -> 18 hitches, worst 2.5 s -> 0.57 s (AstralChain d23e7c1; ssbu-recomp, SavageWind).
  *idea* (T188)
- A driver that refuses a pipeline or library (AMD VK_ERROR_INITIALIZATION_FAILED) must fall back, never be fatal.
  Write a marker so the next start uses whole pipelines (ssbu-recomp cd4a024, B2recomp a5577d7). *check*
- Find shaders by scanning the game data. Containers in .nushdb start at 8-byte alignment, not 16 (43% more found),
  and some programs are embedded in the executable (WindowSmash 1b0e19d). Inventory tools: letsgo 1e9ac9a counts
  BNSH blocks, SavageWind #51. *idea*: a coverage check of our seed against every Maxwell block in XC's RomFS.
- A shipped seed holds keys and metas only, not code (issn cabd380, Metroid Dread recipes, AstralChain variants
  lists). This is the same as our design. Pitfalls:
  - Copying a seed over a played cache paired shaders wrongly.
  - New permutations must not reuse an index still named by keys (issn b525509, 7e3814f).
  - An append-mode header was rewritten at each session (AstralChain 45efba1).
  *check* our seed merge
- Shader cache size: no SPIR-V debug names, only the helpers used (SavageWind 7edf74d). *check*

## 5. Textures, memory tracking, uploads

- **Write watch shared between consumers.** One dirty bit per page, and every check reset it for everyone: the first
  checker took the news and the others stayed stale (white-outs, stretched skinned arms). Use one stamp record where
  each consumer keeps its own clock, and query and reset in one call (WindowSmash a487903/4d6ee5c). *check* (noted in
  lessons_astral_ssbu: ours stamps generations; confirm the single-call reset)
- **Resources over memory the game unmapped.** GPU-resident regions outlived guest memory freed by
  svcUnmapPhysicalMemory, which crashed the driver after 20-40 min. Get unmap notifications and use guarded reads
  (WindowSmash f33d96c, 4748053). *check*
- **Upload staging**:
  - The first CPU touch of a new block costs about 2 ms per 16 MB (kernel zeroing): keep and prefill a staging pool
    (SpartanPort 85bb14f).
  - Staging buffers of a whole scene load were retained until the submit retired (1.3 GB); complete large uploads
    separately (AC-Recomp WINDOWS_MEM).
  - Barrier before a submission's staging copies, because the previous submission may still be reading
    (PokeZ-A 4b2feba).
  *check*
- **CPU-written textures** (movie planes) checked every 8th frame gave green or stale video frames. With write
  tracking, check every frame (AstralChain 6e76ce4). The internal resolution scale must not shrink CPU-filled
  textures (letsgo #10: device lost). *check*
- **Vertex and index data read from host memory over PCIe**: keep a device-local copy refreshed from write tracking.
  Results: GPU 10.2 -> 1.2 ms (letsgo dbd4b9e), render thread 4.9 -> 3.6 ms (B2recomp eb269ed), and on compute
  global memory 8 -> 0.09 ms (PokeZ-A 21c9438). Copy back only each buffer's exact range, because merged ranges wrote
  stale bytes over CPU data, giving infinite instance counts and a TDR (PokeZ-A 2b09f30). *partly done* (vertex cache;
  T175)
- **Hashing every texture every frame** cost up to 26% of a frame in some ports. Use write tracking and ask only for
  textures used this frame, in clusters (WindowSmash 1d01406, B2recomp 5fb84b1, PokeZ-A cc2341f). *check*
- **Deferred readbacks**: CPU reads get the previously published copy, and writes outside a small copy's bytes don't
  wait: 40.9 -> 66.5 fps (SpartanPort cc3563a). 80% of readbacks brought back unchanged bytes (issn 57749a8). *idea*
- **D24S8 substitution**: if the device lacks D24S8 and D32S8 is used, rescale the depth-bias constant, otherwise
  shadow acne (ACNH b61d0ff). Use D24 where supported, because D32S8 doubles bandwidth (PokeZ-A 4b2feba). *check*
- **Aliased images** over the same GPU memory need syncing (SpartanPort 036d5d7, from cuesta4's shadPS4 fork). *done*
  (T107/T110 shared image)
- **MSAA depth read as a multisample texture** returns 0 in compressed tiles on the RDNA2 Windows driver and on
  Intel Arc. Force 1 sample by driver (SpartanPort 10a7864). *check* if XC samples MSAA depth.

## 6. Synchronization with an asynchronous renderer

Our async render worker makes these directly relevant:
- **Deferred guest-visible writes**: copies, fence values and labels must land before the fence the guest observes.
  If they don't, the guest reuses a buffer while the copy is still pending (UI flicker, SpartanPort 2720368).
- **"GPU idle" too early**: SpartanPort signalled GPU idle before the deferred fences were written. The guest freed
  objects whose fence labels were still queued, and the heap corrupted after 13-17 min. It was found with a ring of
  every GPU-to-guest write dumped on fault (542f2d4). *check*: our nvnQueueFinish / sync completion vs pending
  worker writes. *idea*: that write-log ring.
- **Two threads recording at once**: add a producer guard that reports both stacks (issn d8be4c4, e7282ae). *idea*
- **The game rewrites command memory while a replay reads it**: replay a checked copy (letsgo 32bf848). Command lists
  must stay immutable until completion (NVN contract). *check*
- **The `backend_async()` unlocked lazy start**: LASRecomp bd76094 had exactly this boot hang. Use `pthread_once`.
  *check / to fix* (top finding of this session)
- Address arbiter: WaitForAddress / SignalToAddress must use CAS on words the guest changes with its own atomics
  (LASRecomp 1144aea, PokeZ-A 12d06c1). *check*

## 7. Kernel / HLE / OS semantics

- **Condvars**: write the key before releasing the mutex (nn::os Signal skips the svc while the key is 0: lost
  wakeups, PokeZ-A 52359cc). Do not reacquire the mutex on timeout, because the SDK's TimedWait does it too
  (deadlock, letsgo #5). A signal arriving together with a timeout must keep the waker's result (letsgo #15).
  *done* (T067 per lessons_other_recomps)
- `svcWaitSynchronization` keeps a CancelSynchronization that came before the wait pending. nn::os::MultiWait lost
  wakeups that raced the wait (ACNH 238ef69). *check*
- Wake one thread at a time, each waiter on its own condvar, not a broadcast storm. Use a binary search in
  QueryMemory, because libunwind calls it 31k times a second when exceptions fly (WindowSmash 9fd8857). *check*
- Merge neighbouring memory-map regions like the console kernel does, otherwise "too many regions" after 10 min
  (WindowSmash 2a7bb23). Reclaim fiber slots, otherwise "too many fibers" (WindowSmash e883820, d74c5a5). Exception
  state belongs per fiber (ssbu-recomp 3a96916). A fiber resumed on another host thread must not use that thread's
  TLS (ssbu-recomp ce9a4af). *check* (XC has no C++ exceptions, per lessons_windowsmash; fibers?)
- **HLE return ABI**: `StandardSteadyClock::now()` returns its time point in x0, not through x8. The HLE wrote
  through x8, which was random memory (WindowSmash 143fe85). Small structs up to 16 bytes come back in x0/x1. *check*
  every HLE that returns a struct.
- **Time**: give time since 1970, not since boot (save dates showed 1933, dod3 79546d2). Windows time zones that start
  the year with a standard-time change get the DST window wrong (ssbu-recomp 3a96916). *check*
- **Offline services** must answer like an offline console, not "connected" and not "no session": nifm, ssl, bsd,
  ldn, friends, network check 0x1906e (letsgo 14f93cf, B2recomp b3a6dc6, ACNH 0a90e5b). *check*
- **Settings HLE**: GetDesiredLanguage must use the Switch codes (zh-Hans / zh-Hant, SavageWind 800a4f3). A language
  the game lacks gets English (Metroid Dread c5dfcf0). swkbd answers in UTF-16 unless UTF-8 is asked (letsgo
  56d78df). *check*
- **File system**:
  - Close host handles when the game closes IFile / IDirectory (letsgo 9de3875).
  - Open save files with FILE_SHARE_DELETE so rename and delete work while open, as on the console (PokeZ-A bb4731e).
  - Retry a rename that a scanner blocks (dod3 a1daa9a).
  *check*
- **Input**:
  - Menus mute a stick until it is back within 1% of centre, so raw SDL values resting off centre kept sticks muted.
    Use a radial dead zone with rescaling (SavageWind 95f7caa).
  - A phantom device scrolled menus forever (dod3 #15).
  - Neutral six-axis sensor values (letsgo 7880f70).
  - Out-of-range rumble values must be clamped, never fatal (AstralChain 72e01c0).
  *check*

## 8. Recompiler / CPU semantics

- FMA, FZ / denormals, rounding mode cost: see section 1.
- **SDIV / UDIV**: ARM gives 0 for division by 0 and INT_MIN for INT_MIN / -1, while x86 `idiv` traps (uDPR 3dcf8033).
  *check*
- **64-bit vector forms** (SADALP / UADALP `.4h/.2s/.1d`) must clear the upper 64 bits (ACNH #5, found by difftest).
  Vector pack saturation lowering (`vpkswss` crackle in dod3 5835e21). *check* with our difftest corpus.
- **FRSQRTE / FRECPE**: use exact tables, not a 500-step loop (ssbu-recomp ce9a4af, B2recomp 5827a39). *check*
- **AES**: AESE / AESD on AES-NI, because software AES was the top function during loads (ACNH 8e0aeff). CRC32 on the
  hardware instruction (ACNH 23ce32b). *check*
- **STLR as a seq_cst store** so a later LDAR can't pass it (PokeZ-A 52359cc). n/a on x86 hosts.
- **Guest registers in C locals** with dataflow-based spills: a few % faster, exe 961 -> 863 MB (WindowSmash b224063,
  ACNH 15dee19). *in test here* (T165)
- `GUEST_VOLATILE`: at -O1 polled guest values were kept in registers and the game hung (PokeZ-A 1882c28). *check* if
  we raise the optimization level.
- `/Zc:tlsGuards-` (clang-cl): a thread_local read after a call tested dynamic-initializer guards, 20 of the 43
  instructions of a call (dod3 8e78d25). *check* our trampoline TLS.
- Measured as a loss: PGO of the lifted code (-8%, dod3 90c7fc2).

## 9. Audio and movies

- **Pace multi-port output once**, not once per port: the output rate halved and both ports starved (SpartanPort
  1e2661d).
- **Run the sound-feeding threads at high priority**: audio gaps 88 -> 2 (dod3 4e109af, AstralChain 1c9aba2).
  CPUs with 4 threads or fewer starved the GPU thread because worker spin locks took up to 300% CPU (SpartanPort
  4b843a7: lower the workers, raise audio and IO). *check* on the 3200G.
- **After an underrun, skip ahead** so the sound stays in sync with the picture (AstralChain 625f807). Own the output
  queue and report buffers played once the device is within 20 ms of their end, because waveOut reports came late
  and in bunches (WindowSmash 33da2c1). *check*
- **I3DL2 reverb** (recompiled NEON, the console's ADSP job) was about 20% of all CPU samples in ACNH. A bypass
  option helps weak PCs (ACNH 53b9ae7). Another runtime played the reverb send bus dry at 4x volume (Metroid Dread
  5893d31). *check*: XC audio effect cost on the 3200G.
- **USB headset dongles / odd devices**: no sound at all (B2recomp #25/#30/#41). Fall back from WASAPI to DirectSound
  (SpartanPort ad2784f). *check*
- **Movies**:
  - EOS handling (see section 1).
  - Rotate the decoder's output slots, because the slot just freed is still being copied by the game (letsgo #13).
  - Pace pictures by their timestamps on a clock started at the first one, so the game keeps its frame rate
    (SavageWind 4daed41).
  - Cinematics at 30 fps on an exact 33.3 ms grid on high-refresh screens (Metroid Dread 17b72bb; *done* g_cut30).
  - A movie played by the render thread's idle tick came out on a 25/25/50 ms grid (dod3 6099f69).
  - Media Foundation codec availability (Windows N, no WebM) needs a fallback (ssbu-recomp 8c03fab).
  - Race between two calls that are 1 us apart on the Switch and a whole time slice apart on Windows (WindowSmash
    ba72ab3).
  *check* our movie path

## 10. Frame pacing, refresh rates, game speed

- **Honour the game's present interval**: presenting at the host rate sped games up (PokeZ-A 00b4044, letsgo #9).
  *done*
- **Games that step per frame** go into slow motion when frames miss vsync. Push the game into its own 30 fps mode
  with fake slow counters, or back off from 60 to 30 (PokeZ-A de59a87, 5d50af8). *check* XC on a slow PC: slow motion
  or a proper 30?
- **Display lock drift**: a VRR or FreeSync screen drifted 240.3 -> 236 Hz and the game ran 1.7% slow against
  real-time audio. Check the lock against real time every 5 s and fall back to our own clock. A vblank gap disabled
  the lock for the whole session; re-lock after 1 s of regular vblanks (B2recomp 6dfe53c, 870d9ab). *check*
- **No VRR**: present each frame N times with FIFO, locked to the screen (240 Hz -> a steady 119.9; axylpup
  9814bffa). Show a note when the monitor is not k x 60 Hz (ssbu-recomp 20bd2bf). *idea*
- **Present outside the queue lock**: a Present waiting for the GPU blocked the game from queuing its next frame
  (WindowSmash 2c519ef). *check*
- **Fine-grained limiter**: a 10/20 ms judder at a 100 Hz vblank, fixed with a fine tick (SpartanPort 7c884cd). An
  adaptive cap (dod3 c01e96c). *idea*
- **High-fps game logic** classes (only if we unlock fps further):
  - Frame-counting timers (B2recomp: 114 sites).
  - Float timers losing their overshoot at reload.
  - Smoothings `x += k(T - x)`: use 1-(1-k)^f.
  - Cutscene cut ends clamped to (length - step), losing time per cut (AstralChain 6e716d9, B2recomp 68c2d08).
  - GUI speed (SavageWind d192206).
  - Physics or movement breaking above ~120 fps (SpartanPort, MacNativeGames issues).
  *reference*
- **Minimized window** is 0x0: skip presenting instead of failing (SpartanPort fa6391b, SavageWind 10e2d11). Keep the
  swapchain across fullscreen focus loss (SpartanPort d6d1aea). Keep the screen awake while a controller is used
  (B2recomp #38). *check*

## 11. Memory, long sessions, min-spec

- **Soak test for 2-3 h.** Every long-session failure seen elsewhere:
  - GPU memory growth past the budget after 2h43m (MacNativeGames #72).
  - Append-only hash sets of 24M entries (~1 GiB) rehashing in 185-234 ms frames after 2h52m (MacNativeGames
    serial-history).
  - Heap corruption at 14 min (SpartanPort).
  - Yellow and white textures after 2 h (SpartanPort #155).
  - Driver crash after 20-40 min (WindowSmash).
  - Fibers exhausted after 10 min (WindowSmash).
  - Memory-map region table full after 10 min (WindowSmash).
  - A 51 GB log after 6 h (dod3).
  *check*: our SNAP_TAB / frozen_tab / registry tables, a 3 h soak on dl_100.
- **Thread stacks**: winpthreads passes the stack size as a commit size, 256 MB committed per thread. Reserve instead
  (STACK_SIZE_PARAM_IS_A_RESERVATION): private bytes 7.3 -> 4.7 GB (letsgo 290e848, LASRecomp #107). *check*
  (important for 8 GB)
- **Up-front guest memory commit**: 12 GiB failed with error 1450 when the page file couldn't grow. Warn against the
  installed RAM (SpartanPort 752cda1). *check* on 8 GB
- **Commit-on-first-touch race**: two threads on the same 64 KB chunk (letsgo c06fc91). *done* (ported via LASRecomp
  2332e74)
- **Hybrid CPUs**: pinning every thread to P-cores froze a 2-P-core handheld for 5-6 s. Pin only with 6 or more P
  logical processors (B2recomp 4612e4b). Reserving a core for the command processor hurt below 20 logical CPUs
  (issn 8444be3). *check* (no pinning here yet; keep it that way for 4-core CPUs)
- **Contended mutex**: spin up to 40 us before sleeping, except below 4 logical CPUs: 12 -> 1.2 us per wait (letsgo
  d553617). Spinning before condvar waits measured no gain (letsgo 0145b46). *idea*
- **High-resolution waits**: std::condition_variable::wait_for rounds to whole milliseconds on Windows; use an event
  with a high-resolution timer (dod3 9013f97). libc++ atomic notify on Windows goes through a contention table
  (26% of a thread); use WaitOnAddress (issn 0211962). *check*
- **QPC on HPET machines** costs about 1 us; fall back to the invariant TSC (WindowSmash 5004359). *done* (T190). Raw
  rdtsc differs per core on some Xeons by 3.9 s (SpartanPort 2dea61f). *check* that our TSC path calibrates once and is
  invariant-only.

## 12. Windows platform pitfalls

- **NVIDIA driver worker threads have 64 KB stacks**, and its shader compiler overflowed on deep shaders: silent
  crashes. Hook CreateThread in DriverStore DLLs and write the crash report from another thread (WindowSmash 5cf1752).
  *check* (T191)
- **Silent exits**: abort, std::terminate, the UCRT invalid-parameter handler (0xC0000409) and pure calls fast-fail
  past the exception filter and lose the buffered log. Install handlers and flush first (issn a5cd829, dod3 4656b69).
  Write minidumps from a second process, because a self-dump deadlocks on locks held by suspended threads (WindowSmash
  247ee61). `_set_abort_behavior` stops the VC++ box (letsgo 91eb8da). *check*
- **Laptops**: export NvOptimusEnablement / AmdPowerXpressRequestHighPerformance (WindowSmash c370274).
  VK_LAYER_AMD_switchable_graphics hid the NVIDIA GPU on AMD iGPU + NVIDIA laptops (SpartanPort 4335b09). NVIDIA
  Optimus panel flicker (SpartanPort #391). *check* (T194)
- **Paths**: the manifest's activeCodePage UTF-8 makes accented install paths work (letsgo 6772ab8, PokeZ-A 552b2c4).
  Commas in paths broke `clang -Wl,` and cmd junctions (B2recomp d7ccbb0). Per-monitor DPI awareness v2 is needed
  before the first window (B2recomp 66ea6c0). *check*
- **Measurement**: a windowed game behind other windows is composed by DWM and runs 20-35% slower uncapped, so A/B
  runs came out bimodal; bring it to the front (letsgo 8654b48). *method*
- **Thread join** can throw system_error with libc++ on Win32 threads; never let exceptions unwind through guest code
  (SpartanPort edfe859). n/a (clang C)

## 13. Diagnostics and methods worth copying

- **A/B inside one run** with paired statistics: two runs of the same build differ by about 3 fps (dod3 3376743;
  SpartanPort's toggle file). Always A/B memo ideas: a key that cost more than it saved was reverted (SpartanPort
  413cd5c).
- **Native fast paths for hot lifted loops verified by a dual run**: both paths on the same state, every register and
  all memory compared, 0 mismatches over millions (dod3 c91f596, 3252f4e).
- **Hitch trace ring**: usleeps, drains, label writes and presents printed for the frame before each hitch. It found
  a lost frame at a ring buffer's last 4 KB (dod3 053ee74). *check* our cmd memory chunk boundaries.
- **Watchdog contents**:
  - The GPU thread state, the last fences written and the queues stuck in WAIT with their current values (issn 9183da8).
  - An F10 hotkey read by the watchdog thread itself, because the game may have stopped reading input (issn 0144cde).
  - Lock owners, compiles in flight and every thread's stack (WindowSmash 247ee61).
  - What the sound thread waited on and kernel lock waits over 30 ms (AstralChain b149c42).
  *partly done* (our stall watchdog). *idea*: hotkey stack dump.
- **Device lost**: VK_NV_device_diagnostic_checkpoints names the draws in flight (ssbu-recomp 938e66b, PokeZ-A
  00b4044); log the pipelines first used in the 10 s before (WindowSmash f1eea1a). *idea*
- **A FULL_BARRIERS debug mode** (a full barrier around every pass and dispatch) separates missing-barrier bugs
  (SpartanPort 268a2fd). Per-pass image dumps find the first pass with the artifact (SpartanPort 55e6603). A
  black-frame probe (each present shrunk to 32x18 and read back) catches black frames (PokeZ-A 302bd07). *idea*
- **CPU harness** that runs a translated vertex shader with a real draw's data from RenderDoc (letsgo e243230). The
  lesson: a passing test must exercise the failing case.
- **Deterministic game-state hash** over 1,200 frames between builds as a logic regression check (ssbu-recomp
  938e66b). *done* partially (XCDE_FRAME_HASH)
- **Log header**: CPU model, threads, ISA level, RAM, OS, GPU driver version, iGPU or dGPU, API version (PokeZ-A
  bba8108). Keep the previous run's log (letsgo 546a2cd, Metroid Dread cc0a507). A report button that zips the logs
  (several). *check*
- **Built-in sampling profiler** (1000 samples a second per thread, module + RVA, whole stacks; issn e2a5030, dod3
  51ae9f6). An observer effect to avoid: profiling slow frames made the next frames slow (AstralChain 58e193d).

## 14. Launcher, distribution, UX

- Window title or loading screen shows preparation progress, because a black window looked like a hang (ssbu-recomp
  4cc900c).
- Auto settings by detected hardware: iGPU by under 1 GB of dedicated VRAM or by APU name (Metroid Dread 8490650).
  *idea* for Vega 8
- Handheld mode: report operation mode 0 so the game renders its own 720p (AstralChain 683caa5). *idea for min-spec*:
  XC handheld mode
- Save backups before each launch (SpartanPort 5527b1d); save snapshots per save (AstralChain 7717825). *idea*
- Atomic settings writes, a CRLF-tolerant ini reader and visible save errors (SpartanPort 9677e4a, letsgo 022229e,
  SavageWind f3963fa). *check*
- In-place updater with SHA-256 checks and undo (Metroid Dread 9fcea9f). Unzip over the old folder and only changed
  files recompile (B2recomp 3558192).

## 15. Measured as no gain or reverted (don't repeat)

- PGO of the lifted code: 8% slower (dod3).
- A shader specialization memo cost more than it saved (SpartanPort 413cd5c).
- Async end-of-pipe fences: slower (SpartanPort a6fd94b).
- Hot pages left unprotected: GPU timeouts (SpartanPort b90a781).
- Spinning before condvar waits (letsgo 0145b46).
- Waiting on the previous frame's fence at queue-buffer: no gain, a spinner flickered (Metroid Dread 9468ed7).
- Frame interpolation by re-running frames with blended uniforms: too many artifacts, removed (letsgo d72ab33).
- Skipping draws while pipelines compile: missing effects for good (ACNH, AstralChain, PokeZ-A).
- A texture binding helper thread: neutral on 16 threads (SpartanPort efb428d).
- P-core affinity and an EcoQoS opt-out: no gain (dod3 1234628).

## 16. Repositories reviewed

| Repository | What it is | Base / API | What was read | Value for XCDE |
|---|---|---|---|---|
| peiikai/LASRecomp | Link's Awakening (Switch) static recomp | own; Vulkan, Metal | 5,655 lines of commits, 726 of issues | our base; high |
| ly05010419/MacNativeGames | TotK / BotW running natively on Apple silicon | NVN on Metal | 3,937 commits, 1,383 issues, docs | high: pipeline prediction, long sessions |
| FelipePrado0/SpartanPort | Bloodborne then God of War III (PS4 -> PC) | shadPS4 video core | 2,795 commits, 1,918 issues | medium: sync, AMD/Intel, iGPU memory |
| Liondarkz/issn_pc | inFAMOUS Second Son (PS4), fork of SpartanPort | shadPS4 | 126 own commits, issues | medium: seed design, Windows perf, crash reporting |
| axylpup/shadPS4 (second-son) | inFAMOUS SS shadPS4 build | shadPS4 | last 100 commits (API) | medium: VRAM budget, half-refresh vsync |
| soyjxck/dod3-recomp | Drakengard 3 (PS3) static recomp | ps3recomp; D3D12 / Metal / Vulkan | 2,377 commits, issues | medium: methods, Windows timing, logging |
| SNO2207/WindowSmash | Smash Ultimate (Switch) static recomp | D3D11 / DXVK / Metal, own Maxwell translator | 2,054 commits, 176 issues | high: write watch, alpha test, SSY/PBK, driver stacks |
| Denkishi/ssbu-recomp (OpenSmash) | Smash Ultimate (Switch) | NVN -> Vulkan | 1,424 commits, 180 issues | high: same architecture as ours |
| Hexveil404/PokeZ-ARecomp | Pokémon Legends Z-A (Switch), LASRecomp fork | NVN -> Vulkan (same files as ours) | 1,149 commits, 34 issues | very high |
| shatter9652/uDPR | Pokémon BDSP rebuilt as a Unity project | decompilation | 1,105 commits | low (SDIV note) |
| raulzrrs/letsgo-recomp | Pokémon Let's Go (Switch), LASRecomp fork | NVN -> Vulkan | 782 commits, 62 issues, docs/HISTORICO | very high |
| Puddz/AstralChain-PC | Astral Chain (Switch), LASRecomp base | NVN -> Vulkan | 508 commits, 12 issues | very high |
| Revivedx/SavageWindRecomp | BotW (Switch), LASRecomp base | NVN -> Vulkan | 343 commits, 170 issues | very high |
| Nycolazs/ACNHRecomp | Animal Crossing NH (Switch) | SuperMarioWonderRecomp framework, Vulkan | 306 commits, 12 issues | high |
| Metroid-Dread-Recomp | Metroid Dread (Switch) | SwitchRecomp + ScarletNX Vulkan, OpenGL | 263 commits, 38 issues | medium: audio EOS |
| swaymun/AC-Recomp | Astral Chain on macOS | SuperMarioWonderRecomp | commits, docs/ (NVN contracts) | high: NVN semantics |
| K0NL/B2recomp | Bayonetta 2 (Switch) | ssbu-recomp runtime, NVN -> Vulkan | 36 commits, 57 issues (cloned today) | high: AMD fixes, pacing |
| SkyRecomp / EoWRecomp | Skyward Sword / Echoes of Wisdom (LAS forks) | LAS | earlier session (lessons_astral_ssbu.md) | low-medium |
| SuperMarioWonderRecomp | Mario Wonder (Switch) | own | gone (404); DEBUG docs read earlier | (lessons_other_recomps.md) |
