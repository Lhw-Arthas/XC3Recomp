# Ideas reviewed from a public SSBU static-recompilation project (WindowSmash)

Source read: its public README and `docs/TECHNICAL.md` / `docs/BUILDING.md` (2026-10-17). **Ideas only: no code is copied** (its license is
unknown and constitution Art. I–III apply). It targets another game (SSBU 11.0.0, Direct3D 11, XInput) with the same core technique as this
project (AArch64 -> C ahead of time, a Windows runtime with native replacements of OS/SDK functions, Maxwell shaders translated on first use).
It describes itself as experimental; nothing in the public material shows a "magic" method or how fast it was written (2 commits, no spec/prompt files).

## Already the same here
Per-function C with a `Cpu *` context; indirect calls through an address lookup; HLE replacement by symbol; unsupported things trap instead of
passing silently (our strict mode); demand-driven shader translation with a disk cache; reading RomFS in place; differential tests against Unicorn;
scripted input; a developer overlay/captures; developer scripts that drive the game.

## Adopted now
- Shader/pipeline build threads with **64 MB stacks** (`big_stack_thread` in `runtime/nvn/vulkan/exec.c`).
- **No floating-point contraction / fast-math** in the build flags (`-ffp-contract=off` in `scripts/build_boot.sh`); a full rebuild of the generated
  objects will pick it up. Matters as soon as we move to x86-64-v3 (FMA) so guest arithmetic rounds like the CPU.
- Static census of imports left as "unimplemented" at load time: `XCDE_LIST_IMPORTS=1` -> **0 unimplemented imports in `main` and `sdk`** (the 51
  "bound to host stubs" are all implemented HLE).
- Checked: the game has **no C++ exceptions** (`__cxa_throw`, `_Unwind_RaiseException`, personality routines: 0 occurrences in `main`), so the guest
  unwinder bridging they needed is not required here.
- Our SPIR-V cache is keyed by a hash of stage + generated source, so translator changes invalidate it by themselves (their cache adds an explicit
  translation-version marker; worth adding if we ever change shaderc options without changing the source).

## Candidate tasks (added to `tasks.md` as T111-T116)
Whole-function differential tests (their `functest`): run complete leaf functions in Unicorn and natively and compare registers + memory, on top of
our ~107 K single-instruction cases. Sampling profiler (their F6): sample thread instruction pointers and map them to `f_<addr>` (covers T043).
Function discovery from exception-frame tables (their `funcs.py`) as a cross-check of our table/symbol discovery. Tail-call helpers so tail
transfers do not grow the host stack. A static IPC reachability analysis as a *lower bound* of services/commands needed after the title. Frame
capture and draw-diagnostics hotkeys in the window (we have `XCDE_SHOTS` / F9 debug frame; a user-facing F3 capture would help playtests).

## Not applicable
Local Wireless relay/netplay; NVDEC/Host1x VP9 emulation (XCDE uses the `movie::` library instead, already decoded with FFmpeg); fighter NRO
extraction from `data.arc`; D3D11 backend.
