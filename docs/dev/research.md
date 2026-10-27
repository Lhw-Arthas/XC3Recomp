# Research (phase 0): Monado

**For:** `spec.md` v1.0 · **Date:** 2026-10-17
Each entry follows the format **Decision / Reason / Alternatives considered / Evidence**.
The figures come from a 2.0.0 dump (`docs/inventory.md`, `docs/nso_stats.json`) and a research pass of LASRecomp's
generator over the modules (`build/research/`, not versioned).

---

## Measured facts

| Fact | Value | Source |
|---|---|---|
| Version | 2.0.0 (`v262144`), program `0x0100ff500e34a000` | the update's cnmt |
| SDK | NintendoSDK 9.3.1, kernel 9.1 | `nstool --listapi`, npdm |
| Modules | rtld, **main** (9.14 MB `.text`), **sdk** (5.50 MB), **subsdk0** (3.58 MB, `multimedia.nss`) | NSO |
| Instructions | ≈ 4.56 M (main 2.29 M, sdk 1.38 M, subsdk0 0.90 M) | `tools/analyze_nso.py` |
| Symbols | main 360 dynamic (no debug symbols), sdk 25,042, subsdk0 11,514 | `nso.py` |
| `main` imports | 337: **305 from sdk**, **28 from subsdk0** (`movie::`), 4 linker markers | `nso.py` |
| `nn::*` imported by `main` | 201 (os 66, hid 35, fs 26, audio 18, oe 17, mem 8, prepo 8, vi 7, account 5, time 4…) | `nstool --listsym` |
| NVN | `main` only imports `nvnBootstrapLoader`; the API goes through a pointer table | symbols |
| Declared services | 46 (npdm); 12 of them already exist in LAS | npdm, LAS `runtime/` |
| Declared SVCs | 50 (npdm); the `sdk` uses 61 distinct `svc` numbers | npdm, analysis |
| Audio | Wwise statically linked in `main` (`BKHD` v134 banks ≈ Wwise 2019.2), `AKPK` packages, `AK::OpusDecodingThread`, `hwopus` service | strings, romfs |
| Video | 14 WebM files; `main` uses `movie::Decoder/Buffer/MediaData/Extractor` from subsdk0 | romfs, imports |
| RomFS | 18,529 files, 13.61 GB (chr 4.1 GB, map 3.5 GB, sound 2.7 GB, cs 1.7 GB…) | extraction |
| LAS generator pass | **0 unsupported instructions** in the three modules; 9 s (main), 7 s (sdk), 4 s (subsdk0) | `build/research/*.log` |
| Functions found | main 39,930, sdk 40,751, subsdk0 18,280 | same |
| Indirect `br` jumps | main: 18 tables resolved, **1,083 unresolved tables** ("all labels" fallback), 1,796 dispatches; sdk: 43 / 849 / 10,184 | same |
| Generated C | **≈ 295 MB** (main 145 MB in 147 files, sdk 91 MB, subsdk0 59 MB) | same |

The `rt_udf` in the generated C (57 K in main) are padding between functions (zero / `udf` words), not unsupported
instructions: the generator raised no `Unsupported` exception.

---

## R1 — Project base
- **Decision:** start from **LASRecomp** (`upstream/lasrecomp`, commit `136f679`, MIT) for the lifter and runtime;
  **ssbu-recomp** (`938e66b`, GPL-3.0) as a design reference only, no code copied.
- **Reason:** LAS lifts the SDK and simulates SVC + IPC; it already implements through HLE **26 of the 28** `movie::`
  functions XCDE uses, `nvnBootstrapLoader`/`nvnDeviceGetProcAddress`, `nn::vi`, `nv::InitializeGraphics`, `nn::pl`
  (fonts), `nn::mem::StandardAllocator` and `nn::hid` (Npad / rumble): the same SDK of the same period. Its lifter
  decodes 100 % of XCDE's instructions. MIT licence; Windows / Linux / macOS.
- **Alternatives:** ssbu-recomp / B2recomp (HLE of ≈ 1,100 `nn::` functions, Windows only, GPL-3.0); SkyRecomp (a LAS
  fork without attribution, binaries in the repo); starting from zero (months of already solved work).
- **Evidence:** LAS's `HLE_FUNC`s compared with `main`'s imports.

## R2 — Which modules are lifted
- **Decision:** lift **main** and **sdk**; **do not lift subsdk0**: the 28 `movie::` functions `main` uses are
  implemented on the host (26 already in LAS + `movie::SetCoreMask` and `movie::MediaData::operator=`). `rtld` isn't
  lifted either (the host loader does its job).
- **Reason:** subsdk0 is the multimedia library (Stagefright + NvMM / nvdec), hardware-dependent; the game only uses it
  through that small API. Saves 59 MB of C and 18 K functions.
- **Alternatives:** lift subsdk0 and implement the nvdec services (much more work, fragile).
- **Evidence:** the import map (`main → subsdk0`: 28; `subsdk0 → sdk`: 643).

## R3 — Memory layout
- **Decision:** `main` at `0x7000000000` (image `0x12f9000`), `sdk` at `0x7004000000` (image `0x1296000`), like LAS's
  `MAIN_BASE`/`SDK_BASE`. Guest heap as in LAS (`HEAP_BASE 0x7240000000`, up to 3.25 GB).
- **Reason:** both fit without overlapping and LAS's constants are reused (the heap size was later confirmed by Q5).
- **Alternatives:** placing subsdk0 at `0x7002000000` if R2 changed.

## R4 — Jump tables
- **Decision:** improve LAS's table resolver for XCDE before compiling for real. Target: ≥ 95 % of table-type `br`
  resolved (18 of 1,101 in main at the start).
- **Reason:** each unresolved table becomes a `switch` with a label per instruction of the function: correct, but it
  bloats the C (most of main's 145 MB) and the build time, and slows the code.
- **Alternatives:** accept the fallback (very slow builds); dispatch through `rt_dispatch` (slow at run time).
- **Evidence:** the generator's `jumptables` / `br_all_labels` statistics.

**Result (2026-10-17, T020–T022):** the cause was not the table pattern but the **function partition**: the
`adr x10, <cases>` that gives the table base was taken as a function start and split the function right before its
cases, so the targets fell outside it. Fixed in `gen.py` (`adr_targets`, marked `[XCDE]`): an `adr` followed within
≤ 8 words by a `br xN` is not a function start. Tables resolved: **main 18 → 732 (93.4 %)**, **sdk 43 → 492
(89.9 %)**; main's functions 39,930 → 33,601. Only functions with an **unresolved** table still emit a label and a
`case` per instruction (main's C 152 → 142 MB, sdk 96 → 90 MB). The ≈ 50 tables left in main: a table base in a
register set outside the window, `tbz` instead of `cmp` + `b.hi`, and indices rewritten between the `cmp` and the
`ldrb`.

## R5 — Build scale
- **Decision:** compile in parallel chunks, resumable, `-O1` by default and `-O0` for huge units (like LAS), and
  measure.
- **Reason:** 236 MB of C (main + sdk) is several times LAS's; the bottleneck is the compiler, not the generator (9 s).
- **Alternatives:** generate less C (R4, dead-function removal), LTO off, distributed builds.

## R6 — Audio
- **Decision:** Wwise runs lifted inside `main`. The host provides `audren:u`/`audout:u` (from LAS) and the `hwopus`
  service with libopus.
- **Reason:** the engine and the banks (v134) are in the game; only the audio output and the I/O are needed.
- **Answered by Q4:** Wwise asks `hwopus` for Opus decoding; the output goes through `audout:u`.

## R7 — Video
- **Decision:** HLE of the `movie::` API with FFmpeg (VP9 from WebM), reusing LAS's `runtime/hle/movie.c` and its
  NV12→RGBA conversion on the GPU.
- **Reason:** LAS had solved the same API; the cutscenes are standard WebM.

## R8 — NVN and shaders
- **Decision:** reuse LAS's NVN→Vulkan and its Maxwell→SPIR-V translator; extend with what XCDE uses.
- **Reason:** the same SDK (NVN 9.3.1); LAS already reaches gameplay with that backend.

## R9 — Services and SVCs
- **Decision:** start from LAS's 21 services and ≈ 40 SVC cases; add what XCDE **really** uses (strict mode at boot),
  not what the npdm declares. Network / shop / friends answer "offline".
- **Evidence:** npdm (46 services, 50 SVCs); LAS `ipc.c`, `services/*.c`, `kernel.c`.

## R10 — Lessons from other recomps turned into requirements
| Lesson | Source | Requirement |
|---|---|---|
| Hang after ~1 h from a full exception table / a fiber on another thread | ssbu #17, #18, #43 | FR-022 |
| A condvar with a timeout takes the mutex again → self-deadlock | LAS #74, #88 | FR-021 |
| 9 GB at 26 min from shader modules and libraries | ssbu #29 | SC-005 |
| A texture list that never shrinks | ssbu #30, #45 | SC-005 |
| Compute writes into freed memory | ssbu #41, #42 | FR-034 |
| Wrong strides → `DEVICE_LOST` | ssbu #14, #31 | FR-033, FR-036 |
| Shaders built in the middle of action → stutter | ssbu #33, #34 | FR-032, SC-007 |
| Atomics as plain accesses break at `-O2` | ssbu #20 | FR-011 |
| `FRSQRTE` with a 500-step loop (8.7 % of the thread) | ssbu #44 | SC-009 |
| AMD / Linux: the heap imported as userptr → 20–30 fps | LAS #71 | NFR-004 |
| Frame rate oscillating 60↔30 | LAS #16, #70 | FR-044 |
| Unclosed handles → lost saves | LAS #80, #83 | FR-023, SC-006 |
| Video converted on the CPU | LAS #82 | FR-042 |
| Crashes on Intel iGPUs | LAS #8, #35 | NFR-004 |
| A home-made extractor with an invalid RomFS | Sky #3 | FR-004 |
| Non-ASCII paths | LAS #75, Sky #2, #7 | FR-006 |
| Attribution removed | Sky #4 | Constitution art. III |

## Open questions (what they block)
| # | Question | Blocks | How it is answered |
|---|---|---|---|
| Q1 | Why does LAS's table resolver fail on XCDE? | M2 | **Answered:** the function partition (R4). |
| Q2 | Which services / IPC commands and SVCs does XCDE use at boot? | M3 | **Answered (60 s of title, `docs/evidence/M3/usage.tsv`):** 23 distinct SVCs (0x01 04 05 06 08 09 0a 0b 0c 0f 13 15 16 17 18 1a 1b 1c 1d 1f 21 25 29), all implemented; 71 service / IPC command pairs over `sm: lm apm appletOE aoc:u pctl pctl:a/r/s acc:u0 time:u hid fsp-srv audren:u audout:u hwopus`; 172 HLE functions; no network / shop / friends services. Unimplemented IPC commands (return success, audited): `am` ISelfController 1/11/12/13/14/16/91, IWindowController 10, `pctl` 1. |
| Q3 | Which NVN functions and Maxwell opcodes does it use? | M4 | **Partly:** 516 NVN functions asked through `nvnDeviceGetProcAddress` on the title (list in `usage.tsv`, type `nvn`). |
| Q4 | Does Wwise use `hwopus`? | M5 | **Yes:** `hwopus` cmds 0 and 1 (open / create a decoder) and 2,953 calls to `IHardwareOpusDecoder` cmd 8 (DecodeInterleaved) in 60 s. The audio output goes through `audout:u` (3,290 appends), not `audren`. |
| Q5 | How much memory does the game ask for (heap, `MapPhysicalMemory`)? | M3 | **Answered:** a single `SetHeapSize 0xC9400000` (≈ 3.15 GB) at boot; `HEAP_MAX` = 3.25 GB fits with ≈ 0.1 GB to spare. No `MapPhysicalMemory`; 41 `MapMemory` / 1 `UnmapMemory` (thread stacks and buffers). |
| Q6 | Does the logic depend on the frame rate? What is the target rate per scene? | Story 5, SC-008 | **Answered later:** the game runs at any rate with frame pacing (see the HANDOFF: high-FPS work); cutscenes animate characters at 30. |
| Q7 | Does it use `nn::ro`? (`main` doesn't import it) | — | **No:** no `ldr:ro` command in 60 s of title and no `ldr:*` service asked of `sm:`. |
