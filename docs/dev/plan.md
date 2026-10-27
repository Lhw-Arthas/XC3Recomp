# Implementation plan: Monado

**Branch / ID:** `001-xcde-recomp` · **Date:** 2026-10-17 · **Version:** 1.0 (translated 2026-10-25)
**Specification:** [`spec.md`](spec.md) · **Rules:** [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) ·
**Research:** [`research.md`](research.md) · **Tasks:** [`tasks.md`](tasks.md) ·
**Game inventory:** [`../inventory.md`](../inventory.md)

> **How this project works (spec-driven development)**
>
> rules → `spec.md` (what and why: stories, FR, SC) → `research.md` (facts and decisions) → **`plan.md`** (how:
> architecture, milestones, gates) → `tasks.md` (executable, traced work) → code and evidence. A document only changes
> through the one before it. Every task cites requirements; every requirement has a test; every milestone closes with
> evidence in `docs/evidence/`.
>
> This plan reflects the project's start (sessions 1–4). What came after (gameplay, performance, upscalers, the
> launcher, memory work) is recorded in `HANDOFF.md` and the session sections of `tasks.md`.

---

## 1. Summary

A static recompilation of Xenoblade Chronicles: Definitive Edition 2.0.0 (Switch) to a native PC executable. The
AArch64 code of `main` and `sdk` is translated to C by LASRecomp's generator (which already decodes 100 % of the
game's instructions), compiled with clang and linked with a runtime derived from LASRecomp that simulates the Horizon
kernel and services and implements NVN on Vulkan. The multimedia library (`subsdk0`) is replaced by host
implementations of its `movie::` API. Everything derived from the game is generated on the user's machine.

## 2. Technical context

| Aspect | Value |
|---|---|
| Languages | C17 (runtime and generated code), C++17 (UI / ImGui, VMA), Python 3.12 (generator, tools) |
| Main dependencies | Capstone 5, Unicorn 2.1, lz4 (generator); SDL3, Vulkan 1.3 + VMA, shaderc, FFmpeg, libopus, Dear ImGui, SMAA, FSR (runtime) |
| Compiler | clang (Zig's `zig cc`), `-O1`, `-march=x86-64-v2` |
| Storage | Saves in a user folder with atomic writes; per-machine pipeline caches |
| Tests | Unit (C and Python, no game data) in CI; lifter differential tests against Unicorn; recorded routes, soak and pixel tests locally |
| Platforms | Windows 10/11 x64 (first), Linux x64, macOS arm64 (desirable) |
| Project type | Toolchain (generator) + native application (runtime + launcher) |
| Performance targets | SC-007, SC-008, SC-009 of `spec.md` |
| Constraints | Rules arts. I–III (legal); NFR-005 (build ≤ 30 min, a goal) |
| Scale | ≈ 3.67 M instructions to lift (main + sdk), ≈ 80 K functions, ≈ 236 MB of C (before R4); romfs 13.6 GB |

## 3. Rules check (gate before each milestone)

| Article | How the plan meets it | Status |
|---|---|---|
| I Zero content | `targets/`, `build/`, `generated/` in `.gitignore`; T006 packager test; CI without game data | ✅ |
| II Own dump | FR-001–004; the build reads extracted folders, never containers or keys | ✅ |
| III Attribution | T002 `LICENSE` / `NOTICE.md` with Peiikai's notice; ssbu only as a reference | ✅ |
| IV Traceability | `tasks.md` cites FR / SC; matrix §11 | ✅ |
| V Test first | Lifter differential (M2), runtime unit tests before each service | ✅ |
| VI Fail loudly | Strict mode + HLE audit from M3 | ✅ |
| VII Determinism / observability | Watchdog, minidump, per-frame hash in M1–M3, before gameplay | ✅ |
| VIII Measure | Evidence per milestone in `docs/evidence/` | ✅ |
| IX Common runtime | `runtime/` vs `games/xcde/`; game profile (M1) | ✅ (partly: some XCDE hooks live in `runtime/hle/`) |
| X Upstream first | LAS is adapted; rewrites need an ADR | ✅ |

## 4. Project structure

```
Monado/
├── README.md  LICENSE  NOTICE.md  CONTRIBUTING.md
├── docs/
│   ├── dev/                 spec.md plan.md research.md tasks.md HANDOFF.md (the development record)
│   ├── inventory.md  nso_stats.json            # dump facts (no game content)
│   ├── adr/NNNN-*.md                           # decisions (one per file)
│   ├── RECOMP_KNOWLEDGE.md  LESSONS_FOR_XC2.md # what we learnt, for any recomp / for the other Xenoblades
│   └── evidence/M*/                            # logs, metrics, captures without assets
├── tools/
│   ├── lifter/      gen.py lifter.py simd_c.py analyze.py nso.py sym.py (from LAS, adapted)
│   ├── extract/     check_dump.py (FR-001–004), the expected per-folder manifest
│   ├── launcher/    the launcher (SDL3 + Dear ImGui)
│   └── tests/       test_lift.py test_simd.py test_jumptables.py …
├── runtime/                                    # meant to be common to the 4 Xenoblades (from LAS)
│   ├── loader.c dispatch.c kernel.c ipc.c …
│   ├── services/    fs acc am audio hid time set misc hwopus …
│   ├── hle/         nvn_boot movie pl vi heaps input framepace party …
│   ├── nvn/         objects cmdbuf formats astc tegra maxwell/ vulkan/
│   ├── diag/        watchdog crashdump sampler diag
│   ├── platform/    windows linux
│   └── host/        main_boot settings_ini …
├── games/xcde/      profile.json, patches.py, hle_symbols.txt, hle_classes.tsv
├── tests/           unit/ (no game)  native/  routes/  tours/
├── data/            variants_seed.bin (pipeline variants to precompile; no game content)
├── targets/         exefs/ romfs/          (the user's dump, ignored)
├── generated/       generated C            (ignored)
└── build/                                  (ignored)
```

**Structure decision:** a monorepo; LAS's code was copied into `runtime/` and `tools/lifter/` with the changes marked
`[XCDE]` and listed in `docs/UPSTREAM.md` (B2recomp's pattern), so it can be synced with LAS.

## 5. Architecture

```
 targets/exefs + romfs (the user's dump)
        │  check_dump.py (FR-001–004)
        ▼
 tools/lifter/gen.py ──► generated/{main,sdk}/*.c ──clang──► build/obj/*.o
   Capstone + Unicorn (jump tables)                              │
   games/xcde/patches.py (patches with expected bytes)           ▼
                                    ┌─────────────────────────────────────────────┐
                                    │ runtime (build/xcde.exe)                    │
  guest memory = host memory        │ loader: main@0x7000000000  sdk@0x7004000000 │
  window 0x7000000000–0x7320000000  │ dispatch: guest address → function, hooks   │
                                    │ kernel: SVC (threads, sync, memory, IPC)    │
                                    │ services: fsp-srv hid audren/audout set …   │
                                    │ hle: movie:: (FFmpeg) nvn_boot pl vi mem    │
                                    │ nvn → Vulkan · Maxwell → SPIR-V · ASTC/BCn  │
                                    │ SDL3 · ImGui · diag (watchdog, hash, prof)  │
                                    └─────────────────────────────────────────────┘
```

Design points (details and alternatives in `research.md`):
- **Modules:** `main` and `sdk` are lifted; `subsdk0` isn't (R2). The loader replaces `rtld`.
- **HLE borders:** (a) functions by name (`HLE_FUNC`, e.g. `movie::`, `nvnBootstrapLoader`, `nn::vi`); (b) SVCs;
  (c) IPC services. All classified in the audit (Art. VI).
- **Memory:** LAS's constants (R3); the guest heap imported as driver memory.
- **Concurrency:** guest threads = host threads; **the game's fibers on host fibers (HLE of `nn::os::*Fiber`, T032b)**
  with `tpidr` / `tpidrro` / `thread` recomputed when resumed on another thread (FR-022); Horizon condvars (FR-021).
- **GPU:** a persistent pipeline cache, prewarming off the game thread, freeing unused pipelines and libraries
  (SC-005), live texture tracking, checking freed memory before writes (FR-034).
- **Diagnostics:** watchdog, out-of-process minidump, `VK_EXT_device_fault`, per-frame hash.

## 6. Design contracts (phase 1)

Short documents in `docs/contracts/` written before the code that uses them:

| Contract | Content | Used by |
|---|---|---|
| `game-profile.md` | What defines a game: bases, build-ids, modules to lift, heap, patches, hooks, options | M1, XC2/XC3/XCX |
| `hle-abi.md` | The `HostFn(Cpu*)` signature, registration by name, override by address, x0–x7 / v0–v7 rules and errors | M3+ |
| `patch-format.md` | The `patches.py` format: address, expected bytes, replacement C, linked requirement | M2 |
| `route-format.md` | Recorded input, checkpoints (frame, hash, capture) | M3+ |
| `audit-format.md` | The real / simplified / stub classes and how the audit is generated | M3+ |
| `evidence.md` | What is kept per milestone and how it is named | all |

## 7. Milestones and gates

Each milestone has a **deliverable**, an **exit gate** (all with evidence) and the **requirements** it covers. The
concrete tasks are in `tasks.md`.

| Milestone | Goal | Exit gate | Requirements |
|---|---|---|---|
| **M0 Foundations** | Repo, licences, dump check, basic CI | `check_dump.py` accepts 2.0.0 and refuses the rest; the packager refuses a derived file; CI green without game data | FR-001–007, NFR-001, SC-012 |
| **M1 Profile and generator** | Game profile, adapted generator, main+sdk generated | Reproducible `generated/` (the same hash twice); 0 `Unsupported`; coverage report | FR-010, FR-013, NFR-006 |
| **M2 A correct, compact lifter** | Jump tables (R4), atomics, wider differential, first full build | ≥ 95 % tables resolved; differential 100 %; the game compiles; build time measured | FR-011, NFR-005 |
| **M3 Boot** | XCDE loader, SVCs and services in strict mode, base diagnostics (watchdog, minidump, determinism) | The game reaches its first `Present` without unaudited stubs; Q2/Q4/Q5 answered | FR-020–024, FR-060–065 |
| **M4 Picture and sound** | NVN, shaders, textures, video, audio up to the title screen | Title identical to the reference; opening cutscene with audio; clean Vulkan validation | FR-030–042 |
| **M5 Gameplay** | Test route: intro → Colony 9 → battle → save → load | Route reproducible without a crash on A; atomic saves; controller and rumble | FR-023, FR-043–046, Story 2 |
| **M6 Whole game** | Base story + *Future Connected*, every language | SC-003 (two people, two machines) | Story 2 |
| **M7 Hardening** | 4 h soak, GPU matrix, R10 lessons one by one | SC-004, SC-005, SC-006 on A, B and C | Story 3 |
| **M8 Performance** | Profile, C optimisations, presentation | SC-007, SC-008, SC-009 | Story 4 |
| **M9 Release** | Dependency-free builder, launcher, Linux, documentation | SC-001; packages without derived files (SC-012) | FR-007, NFR-002 |
| M10 PC improvements | Resolution, aspect, filters, options; unlocked rate | Story 5 | FR-050–053 |

**Gate rule:** a milestone doesn't start before the previous gate closes, except research tasks marked `[P]`. If a
gate fails twice, the spec or the plan is reviewed before going on.

## 8. Test strategy

| Level | What | Where | When |
|---|---|---|---|
| Lifter units | Each instruction class against Unicorn | CI | Each commit |
| Jump tables | A synthetic pattern corpus + statistics on the dump | CI + local | Each generator change |
| Runtime units | Condvar, fibers, IPC, atomic saves, ASTC, video conversion | CI | Each commit |
| Smoke | Boot to the first `Present` / title | Local | Each runtime PR |
| Routes | Recorded input + per-frame hash + captures | Local | Before merging to `main` |
| Pixel | Captures at fixed points against a reference (threshold) | Local | Weekly / release |
| Soak | Hours of play + memory, VRAM, handles | Local | Before a release |
| Matrix | NVIDIA / AMD / Intel; Windows / Linux | Local + testers | Before a release |

Tests with game data never run in CI and never upload artefacts with assets.

## 9. Risks

| Risk | Prob. | Impact | Mitigation |
|---|---|---|---|
| Unresolved jump tables → huge, slow C (R4) | High | High | A dedicated M2; pattern corpus; ≥ 95 % target |
| Compiling ≈ 236 MB of C too slow for a player (R5) | High | Medium | R4, chunking, `-O1/-O0`, parallel builds |
| Services / SVCs LAS doesn't cover (34 new declared services) | Medium | Medium | Strict mode in M3; implement only what is used |
| Maxwell opcodes or NVN functions not covered | High | High | Shader tests; per-shader translation checks |
| Thread races in an open world with streaming | Medium | High | Determinism + watchdog from M3; soak in M7 |
| Logic tied to the frame rate (Q6) | High | Medium | Unlocked rate only with tests |
| `main` without symbols makes hooks and debugging hard | High | Medium | sdk symbols, signatures, `.eh_frame`, a generated function map |
| Derived content published by mistake | Low | Very high | Art. I, the packager test, CI without data |
| Divergence from LAS upstream | Medium | Low | `docs/UPSTREAM.md` + `[XCDE]` marks |

## 10. Complexity tracking

| Added complexity | Why it is needed | The simpler alternative was dropped because |
|---|---|---|
| `movie::` HLE instead of lifting subsdk0 | subsdk0 depends on nvdec / NvMM | Lifting it means simulating the video hardware |
| A wider jump-table resolver | 1,083 unresolved tables in main | The fallback multiplies the C and the build time |
| Full diagnostics before gameplay | Real hangs show after 30–60 min | Adding them later means reproducing hangs without tools |

## 11. Traceability matrix (summary)

| Requirement | Milestone | Tasks | Test / evidence |
|---|---|---|---|
| FR-001–007 | M0, M9 | T005–T008, T090 | `tests/unit/test_check_dump.py`, a clean-machine build |
| FR-010–013 | M1–M2 | T010–T024 | differential, coverage report |
| FR-020–024 | M3 | T030–T042 | runtime unit tests, strict mode |
| FR-030–037 | M4 | T050–T058 | Vulkan validation, title capture |
| FR-040–042 | M4 | T059–T063 | reference WAV, cutscene |
| FR-043–046 | M5 | T070–T075 | route + captures per language |
| FR-050–053 | M10 | T100–T104 | captures + equal hash |
| FR-060–065 | M1, M3 | T015, T027–T029, T033, T043 | hashes, forced reports |
| SC-001–012 | M5–M9 | T076–T095 | `docs/evidence/` |

## 12. Recorded decisions (ADR)

| ADR | Decision | Detail |
|---|---|---|
| 0001 | LASRecomp as the base; ssbu-recomp only as a reference | research R1 |
| 0002 | Version 2.0.0, `main` build-id `7e1df8e08d60544b` | research, inventory |
| 0003 | Lift main+sdk; `movie::` HLE; no subsdk0 or rtld | research R2 |
| 0004 | LAS's memory layout | research R3 |
| 0005 | Vulkan 1.3 first, Metal later | spec NFR-002 |
| 0006 | Common runtime + `games/xcde/` + game profile | rules IX |
| 0007 | clang (Zig), `-O1` by default, atomics with `__atomic` | research R5, FR-011 |
| 0008 | Wwise lifted; `audren/audout` + `hwopus` | research R6 |
| 0009 | Video through FFmpeg with GPU conversion | research R7 |
| 0010 | Diagnostics from M1 (watchdog, minidump, determinism, `device_fault`) | rules VII |

## 13. Extending to XC2, XC3 and XCX DE

Each new game is a new feature (`002-xc2-recomp`, …) with its own `spec.md`, reusing `runtime/` and defining its
`games/<game>/`. Before starting, the research is repeated (module inventory, SDK, services, middleware). Every runtime
change must keep XCDE's routes passing (cross regression). `docs/LESSONS_FOR_XC2.md` lists what carries over.

## 14. Early status (2026-10-17, end of session 1) — see `HANDOFF.md` for the current state

**Done and verified then**
- M0, M1 (reproducible generator, 0 unsupported instructions), M2 (jump tables 93.4 % main / 89.9 % sdk; a full `-O1`
  build of main+sdk in **131 s**; differential against Unicorn **≈ 107,000 cases, 0 failures**).
- M3 nearly closed: the recompiled game **boots, initialises the SDK and services, mounts a 14.6 GB virtual RomFS and
  presents stable frames at ~30 fps** on Vulkan, 0 crashes in 40 s runs. Fiber HLE (T032b), Horizon condvar semantics
  (T031), `hwopus` with libopus (command 8), thread watchdog (v1).
- M4 in progress: Maxwell→GLSL translator extended (`TLD4S`, `TLD4`, `SULD`, `SUST` with storage images), **0 shaders
  failing**; `STORAGE` images (`uint` views per texel size) and **rendering into slices of 3D textures**.

**Done in session 2 (2026-10-17)**
- Title right in the window: sky, red Monado, lit rocks, grass with flowers (like the reference).
- Real causes found and fixed: the 3D deswizzle (colour LUT), `SULD/SUST` (size D and image binding), stencil sampling
  (`usampler` + stencil aspect), **NVN textures over the same memory share an image** (deferred lighting compares
  `EQUAL` against material classes taken from the G-buffer's stencil), **geometry shaders** (point sprites: the dot
  grid), programs without a fragment shader (0 dropped draws, T064).

### Changelog
- 2026-10-18 — v1.16: T137/T139 — occlusion counters (samples passed) implemented with Vulkan occlusion queries: the party and enemies now render in battle (they were culled as hidden). T138 thread stacks reserved instead of committed (~10 GB less commit; fixed a deterministic hang). Route reaches "Battle Introduction 2".
- 2026-10-18 — v1.15: T134 — transform feedback and rasterizer discard implemented (emulated with heap stores from a vertex shader variant; layout from the NVN control section): grass no longer renders as black streaks. The battle field shows.
- 2026-10-18 — v1.14: T133 — `nvnCommandBufferBarrier` implemented (was dropped): GPU-computed skinning palettes no longer race their draws; cutscene characters render correctly. New `scripts/build_rt_gfx.sh` (all runtime objects + link).
- 2026-10-18 — v1.13: fixes from reviewing three other Switch recomp / port projects and upstream LASRecomp (`docs/lessons_other_recomps.md`): T125 program cache keyed by shader content, T126 zero-padded constant buffers, T127 LDC.64 address snapshot (test), T128 fence sequence + fatal GPU wait timeout.
- 2026-10-18 — v1.12: T122 closed — HLE mutexes held across guest calls no longer deadlock the deterministic scheduler; the New Game route reaches the first 3D scene. Open: T124 (image hashes split from the 3D scene on).
- 2026-10-18 — v1.11: T119 closed — deterministic mode reads vertices in place (the vertex cache gave run-to-run differences: T121); 3 runs through the intro movie hash-identical on 5245/5245 frames.
- 2026-10-18 — v1.10: T118 intro video fixed. The game builds a `movie::Buffer` over its own memory before `Decoder::GetOutputBuffer` and reads that memory; the HLE replaced the Buffer's pointer with its own slot, so the game's frame buffer kept the LCG "static" its uploader fills it with. Fix: copy the decoded output into the game's memory (`runtime/hle/movie_buf.h`, test `tests/native/test_movie_buf.c`).
- 2026-10-17 — v1.9: T029 closed for real — deterministic mode with a cooperative scheduler, virtual time and virtual timers for vsync / audio; 3 title runs with 100 % identical hashes on every frame (2.1 % before).
- 2026-10-17 — v1.8: M3 diagnostics — T027 watchdog (5 s), T028 out-of-process minidump, T029 deterministic mode + per-frame hash + input record / replay, T033 strict mode + generated HLE audit.
- 2026-10-17 — v1.7: T059 closed — the audio capture matches the reference recording of the title (chroma 0.92, the same notes and bands). Added `tools/wav_compare.py`.
- 2026-10-17 — v1.6: T059 partly — the game's audio goes through `audout:u`; a valid WAV dump, real-time pacing, `tools/wav_report.py` + a test.
- 2026-10-17 — v1.5: T067 (hang: an ETIMEDOUT / condvar race in the kernel) and T108 (close: the virtual RomFS fd cache without a lock) closed; 47/47 clean boots. New tools: `scripts/repro_stability.sh`, `XCDE_STALL`, `XCDE_CRASH_DUMP_REG`.
- 2026-10-17 — v1.4: title right (deferred lighting, points, depth-only draws); T064/T105/T106/T107 closed; new T108–T110.
- 2026-10-17 — v1.3: T068 solved (3D deswizzle); title right in the window; new T105–T106.
- 2026-10-17 — v1.2: status after session 1: M2 closed, M3 nearly closed, M4 in progress; new tasks T064–T068; `HANDOFF.md` added.
- 2026-10-17 — v1.1: the fixes from other recomps with their task and status; the fiber HLE gap found (T032b).
- 2026-10-17 — v1.0: restructured as spec-driven development (rules, spec, research, plan, tasks). Includes the generator pass (0 unsupported, 1,083 unresolved tables in main, 295 MB of C), the import map (main→subsdk0: 28 `movie::`) and LAS's HLE coverage.
- 2026-10-17 — v0.2/v0.2.1: analysis of the 2.0.0 update and RomFS extraction.
- 2026-10-17 — v0.1: first draft.
