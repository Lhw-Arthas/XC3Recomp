# Feature specification: Monado

**ID:** `001-xcde-recomp` · **Created:** 2026-10-17 · **Status:** reviewed draft (v1.0)
**Input:** "A definitive static recompilation of Xenoblade Chronicles: Definitive Edition (Switch) to native PC, as a
base for the other three Xenoblade games."

> This document describes **what** and **why**, without deciding **how** (that is `plan.md`). Every requirement is
> testable; open points are marked `[NEEDS CLARIFICATION]` and block the phase that depends on them.
> Rules: `CONTRIBUTING.md`. Real game facts: `research.md` and `docs/inventory.md`.
> (Status as of 2026-10-25: most stories are met; see the README and `HANDOFF.md` for what is done and what is open.)

---

## 1. User scenarios and tests *(mandatory)*

The stories are prioritised. Each can be developed, tested and shown on its own (an MVP in itself).

### Story 1 — Build the game from your own dump (priority P1)

A player who owns XCDE on their Switch extracts the exefs and romfs, selects them and gets a native executable without
installing tools by hand.

**Why this priority:** without it nothing exists; it is also the project's legal boundary.

**Independent test:** with a 2.0.0 dump on a clean machine the builder finishes and leaves a game that boots; with a
wrong dump, the message explains the problem.

**Acceptance scenarios:**
1. **Given** a folder with the 2.0.0 `exefs/` and `romfs/`, **when** the user presses *Build*, **then** the process
   finishes without errors, shows step-by-step progress and the launcher moves to *Play*.
2. **Given** an `.nsp`, `.xci`, `.nca` or `.nsz`, **when** it is selected, **then** it is refused, explaining that
   extracted content is needed, without reading the file.
3. **Given** an exefs of another version, **when** it is validated, **then** the detected and expected (2.0.0)
   versions are shown.
4. **Given** an incomplete romfs, **when** it is validated, **then** the folders with missing (or differently sized)
   files are named before building. (The manifest is aggregated per folder + a hash, so the game's file list is not
   published: Art. I.)
5. **Given** an interrupted build, **when** it is started again, **then** it continues from the last verified step.

---

### Story 2 — Play the whole story (priority P1)

The player plays XCDE from start to end, *Future Connected* included, with correct picture, sound, cutscenes,
controls and saving.

**Why this priority:** it is the product.

**Independent test:** the recorded test route (intro → Colony 9 → first battle → save → load) replays without
failures, and two people finish the game on different machines.

**Acceptance scenarios:**
1. **Given** the built game, **when** it starts, **then** the logos, the opening cutscene with synchronised audio and
   the title screen show.
2. **Given** a new game, **when** the intro is played up to Colony 9, **then** battle, menus, HUD and real-time
   cutscenes look and sound like on the console (no visible artefacts).
3. **Given** a game in progress, **when** the player saves and force-closes the game during another save, **then** the
   previous save is intact and loads.
4. **Given** any game language, **when** it is selected, **then** all text shows without boxes.
5. **Given** an Xbox, PlayStation or Pro Controller, **when** it is connected, **then** it works with nothing to set
   up, with rumble.

---

### Story 3 — Long sessions without hangs or leaks (priority P2)

The player plays 4 hours in a row without the game hanging, closing or getting worse over time.

**Why this priority:** other recomps fail right here (hangs after an hour, 9 GB of memory at 26 min).

**Independent test:** a 4 h soak (route + idling + menus) with memory, VRAM and handle metrics.

**Acceptance scenarios:**
1. **Given** a 4 h session, **when** it ends, **then** there were no hangs or crashes and private memory, VRAM and
   handles are flat after the first hour.
2. **Given** a hang (forced in tests), **when** 5 s pass without a frame, **then** a report with every thread, lock
   and queue is written.
3. **Given** a crash, **when** it happens, **then** a readable minidump and a report with the guest and host stacks are
   written.

---

### Story 4 — Stable performance on normal PCs (priority P2)

The game holds its target frame rate without port-caused stutter on a mid-range PC, a laptop with an integrated GPU
and a Steam Deck.

**Independent test:** a timed test route on reference machines A, B and C.

**Acceptance scenarios:**
1. **Given** the second run (warm caches), **when** the route is played, **then** there are no frames over 100 ms.
2. **Given** a machine right at the limit, **when** performance fluctuates, **then** the pacing doesn't keep
   oscillating between the target rate and half of it.
3. **Given** a cutscene, **when** it plays, **then** it runs at its native rate on a mid-range GPU.

---

### Story 5 — PC improvements (priority P3)

Higher internal resolution, free aspect ratio (ultrawide), output filters, control remapping and options in an
overlay menu, without changing the game's logic.

**Independent test:** comparison captures per option, and a deterministic route with identical hashes with and
without visual options.

**Acceptance scenarios:**
1. **Given** a resolution scale of 2.0, **when** playing, **then** the image is sharper and the game state hash equals
   the one at 1.0.
2. **Given** a 21:9 window, **when** playing, **then** the 3D scene widens and the interface isn't stretched.
3. **Given** an unlocked frame rate, **when** it is enabled, **then** it is only offered if the determinism test showed
   the logic doesn't depend on it. (Answered later: high frame rates work with frame pacing, see `HANDOFF.md`.)

---

### Story 6 — Development tools (priority P3, but built early)

The developer can record and replay input, compare builds frame by frame, profile and audit the HLE.

**Independent test:** two runs with the same input produce the same hash over 10,000 frames.

**Acceptance scenarios:**
1. **Given** deterministic mode, **when** the same route runs twice, **then** the hashes match.
2. **Given** strict mode, **when** the game calls something unimplemented, **then** it stops with a report.
3. **Given** the profiler, **when** it is on, **then** it lists the most expensive guest / host functions per thread.

---

### Edge cases
- Paths with spaces and non-ASCII characters (`C:\Users\José Ñ\Games (copy)\`).
- Minimising, restoring, changing monitor and full screen in the middle of a game.
- A full disk while saving; a read-only save folder.
- A controller unplugged in the middle of a battle.
- A GPU without an optional Vulkan extension; an old Intel iGPU.
- Closing the game during shader compilation or saving.
- A user updating the port with caches from an older version.
- A session of hours in a menu (no game activity).

## 2. Requirements *(mandatory)*

### 2.1 Functional requirements

**Input and build**
- **FR-001**: The system MUST accept a folder with extracted `exefs/` and `romfs/`, or their contents.
- **FR-002**: The system MUST refuse encrypted containers (`.nsp`, `.xci`, `.nca`, `.nsz`, `.xcz`) without reading them.
- **FR-003**: The system MUST verify version 2.0.0 by the modules' build-id (`main` `7e1df8e08d60544b…`).
- **FR-004**: The system MUST verify the romfs is complete (expected counts and sizes per folder and a hash of the list
  of paths and sizes).
- **FR-005**: The build MUST be resumable step by step and keep a log per step.
- **FR-006**: The build MUST work in paths with spaces and non-ASCII characters.
- **FR-007**: The build MUST NOT require the player to install Python, compilers or SDKs by hand. (Not met yet: the
  build needs MSYS2, Python and zig, see the README.)

**Running the game's code**
- **FR-010**: The system MUST run the code of `main` and the SDK as native code, with no interpreter or JIT.
- **FR-011**: The system MUST reproduce the AArch64 semantics the game uses, including atomics with their memory
  order, NEON / FP with the guest's rounding modes and C++ exceptions crossing recompiled code.
- **FR-012**: The system MUST allow replacing any game function from the port (hooks) without regenerating everything.
- **FR-013**: Per-instruction patches MUST be declared as data and check the expected original bytes.

**The console's operating system**
- **FR-020**: The system MUST provide the system services the game really uses, with their observable semantics
  (threads, memory, synchronisation, files, time, accounts, settings, applets).
- **FR-021**: Waits with a timeout on condition variables MUST return without the mutex (Horizon semantics).
- **FR-022**: Per-thread state MUST be right even when a fiber resumes on another host thread; per-context resources
  (e.g. exception state) MUST be freed when they end.
- **FR-023**: Saving MUST be atomic (all or nothing) and file handles MUST close with their object.
- **FR-024**: Network, shop and friends services MUST answer like an offline console, with no endless waits.

**Graphics**
- **FR-030**: The system MUST implement the NVN API the game obtains through `nvnBootstrapLoader` on Vulkan 1.3.
- **FR-031**: The system MUST translate every Maxwell shader of the game, compute stages included.
- **FR-032**: Pipelines MUST be cached on disk and prewarmed without blocking the game thread.
- **FR-033**: Copies between buffers and textures MUST follow their own command buffer's strides and never overrun.
- **FR-034**: The system MUST NOT write GPU results into memory the game already freed.
- **FR-035**: The system MUST detect CPU writes to GPU memory (Windows and Linux).
- **FR-036**: On a device loss, the system MUST report the last command executed.
- **FR-037**: The system MUST decode ASTC and BCn textures correctly.

**Audio, video, input, presentation**
- **FR-040**: The system MUST output the audio Wwise produces through the system audio services, without gaps or drift.
- **FR-041**: The system MUST decode Opus when the game asks the `hwopus` service.
- **FR-042**: The system MUST play the 14 WebM cutscenes through the game's `movie::` API, converting colour on the GPU.
- **FR-043**: The system MUST support controllers (SDL3), keyboard and mouse, with remapping and non-blocking rumble.
- **FR-044**: Frame pacing MUST have hysteresis so it doesn't oscillate between the target rate and half of it.
- **FR-045**: Window, borderless full screen, minimise and restore MUST NOT cause crashes.
- **FR-046**: Every game language MUST show without boxes, with free fonts by default and the user's fonts optional.

**PC improvements**
- **FR-050**: Internal resolution scale 0.5–4.0.
- **FR-051**: Free aspect ratio with the 3D scene widened and the UI not stretched.
- **FR-052**: Output filters: bilinear, FSR 1 and SMAA.
- **FR-053**: An overlay options menu (ImGui) usable with keyboard and controller.

**Tools**
- **FR-060**: Deterministic mode with a per-frame state hash.
- **FR-061**: Watchdog: a full report after 5 s without a frame.
- **FR-062**: Crash report with a minidump written by a separate process.
- **FR-063**: Input recording and replay; routes in `tests/routes/`.
- **FR-064**: A profiler per guest and host function and per thread.
- **FR-065**: A generated HLE audit and a strict mode.

### 2.2 Non-functional requirements

- **NFR-001 (legal)**: Meet articles I–III of the rules (`CONTRIBUTING.md`); checked by a packager test.
- **NFR-002 (platforms)**: Windows 10/11 x64 required; Linux x64 required before a 1.0 release; macOS arm64 desirable.
- **NFR-003 (CPU)**: Run on x86-64-v2; use x86-64-v3 (AVX2) when available.
- **NFR-004 (GPU)**: Vulkan 1.3; NVIDIA, AMD and Intel (iGPU included).
- **NFR-005 (build)**: Generation + compilation from scratch on 16 threads in ≤ 30 min (the generated C is ≈ 295 MB,
  see `research.md` R5).
- **NFR-006 (reproducibility)**: The same dump + the same port version → the same hash of the game library.
- **NFR-007 (privacy)**: No telemetry; logs contain no keys and no system user names.

### 2.3 Key entities
- **Dump**: `exefs/` (rtld, main, sdk, subsdk0, main.npdm) + `romfs/` (18,529 files, 13.61 GB).
- **Guest module**: an NSO loaded at a fixed address; it has functions, imports and exports.
- **Recompiled function**: a C function equivalent to a guest function; it has a guest address and may have a hook.
- **HLE implementation**: host code replacing a function or a service; it has an audit class.
- **Game profile**: base addresses, version, patches, hooks and options of one game (`games/xcde/`).
- **Test route**: recorded input + reproducible checkpoints (hash, capture).
- **Cache**: pipelines and translated shaders, specific to the user's machine.

## 3. Success criteria *(mandatory)*

Measurable and implementation-free. Reference machines: **A** a mid-range desktop (e.g. Ryzen 5 + RTX 3060), **B** a
laptop with an iGPU (Radeon 780M or Intel Xe), **C** Steam Deck (Linux).

- **SC-001**: A new user goes from "I have the dump" to "I'm playing" in ≤ 45 min on machine A, following only the README.
- **SC-002**: The whole test route replays without a crash on A, B and C.
- **SC-003**: At least two people finish the base story and *Future Connected* without hangs.
- **SC-004**: A 4 h soak on A, B and C: 0 hangs, 0 crashes, 0 Vulkan validation errors.
- **SC-005**: Private memory and VRAM grow < 5 % per hour after the soak's first hour.
- **SC-006**: OS handles stable (± 2 %) during the soak.
- **SC-007**: With warm caches, 0 frames > 100 ms on the test route on A and C.
- **SC-008**: The game's target rate held on A at 1080p, with the p99 frame time ≤ 1.5× the target.
- **SC-009**: No runtime component takes over 5 % of the game thread's time in the route's profile.
- **SC-010**: Two deterministic runs of the same route give identical hashes for 10,000 frames.
- **SC-011**: Strict mode goes through the route with 0 calls to unaudited stubs.
- **SC-012**: Zero game-derived files in the repository and in published packages (checked in CI).

## 4. Assumptions
- The supported version is **2.0.0** (update `v262144`); other versions are new work.
- The player owns a legal copy and extracts it themselves; the project doesn't explain how.
- System fonts are replaced by free fonts unless the user provides theirs.

## 5. Out of scope
- Online play and Nintendo services.
- Matching decompilation.
- Distributing generated game binaries.
- Other XCDE versions and the other Xenoblade games (they come later, reusing the runtime).

## 6. Dependencies
- LASRecomp (MIT) as the base of the lifter and the runtime (commit `136f679`).
- ssbu-recomp (GPL-3.0) only as a design reference (commit `938e66b`).
- SDL3, FFmpeg, Vulkan, shaderc, Dear ImGui, SMAA, FSR (licences in `NOTICE.md`).

### Changelog
- 2026-10-17 — v1.0: first version, split from plan v0.2.
- 2026-10-25 — translated to English for the public repository; status notes added in brackets.
