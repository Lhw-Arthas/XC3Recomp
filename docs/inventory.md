# F1 inventory — Xenoblade Chronicles: Definitive Edition 2.0.0

Source: the 2.0.0 update of a legally owned copy (Patch `0x0100ff500e34a800`, version 262144 = **2.0.0**), program
`0x0100ff500e34a000`. The update's exefs is complete, so the base game isn't needed for this part.
Analysis made on 2026-10-17 with `nstool 1.9.2` + `tools/analyze_nso.py`. It only holds counts and API names; nothing
of the game's content.

## 1. Package

| Fact | Value |
|---|---|
| Update | 55 MB; 3 useful NCAs: Program (52 MB), Control, LegalInformation (+ Meta) |
| Base game | 14.66 GB; 3 NCAs + Meta |
| Program NCA of the update | partition 0 (exefs) is complete; partition 1 (the patched RomFS) needs the base NCA |
| Program SDK | **NintendoSDK 9.3.1** (`nnSdk-9_3_1-Release`), kernel 9.1 |
| Internal project code | `BF1` (`bfsw`), built with `mm_lib`, `anmlib`, `rapidjson` |

## 2. NSO modules (exefs)

| Module | Size on disk | `.text` | `.ro` | `.data` | Instructions | Symbols | Build-id (8 B) |
|---|---|---|---|---|---|---|---|
| rtld | 6.6 KB | 5.7 KB | 3.2 KB | 0.6 KB | 1,432 | — | `31a2773ea6928ffe` |
| **main** | 6.3 MB | **9.14 MB** | 2.61 MB | 0.40 MB | **2,285,526** | 376 (no symbols; dynamic only) | `7e1df8e08d60544b` |
| **sdk** | 5.1 MB | 5.50 MB | 6.60 MB | 6.68 MB | 1,375,856 | 25,058 | `ad3fdfbd62a5f4b0` |
| **subsdk0** | 3.4 MB | 3.58 MB | 2.45 MB | 0.20 MB | 895,664 | 11,530 | `5a7ada8dd7447c10` |
| **Total** | | **18.2 MB** | | | **≈ 4.56 M** | | |

- 4 modules → fits LASRecomp's `g_modules[4]` (rtld, main, sdk, subsdk0).
- `main` is a **stripped** binary: function discovery depends on `.eh_frame`.
- `sdk` holds `nn::*`, the NVN loader and Nintendo's libraries; `subsdk0` holds the `movie::` library (Stagefright,
  VP9 / H.264).
- Process: 64-bit, `AddressSpace64Bit`, main thread priority 44, 1 MiB stack, handle table 0x200, `EnableDebug`.

## 3. Instructions (approximate counts by bit pattern)

| | main | sdk | subsdk0 |
|---|---|---|---|
| `bl` | 150,685 | 66,227 | 54,047 |
| `blr` (indirect call) | 23,405 | 11,053 | 3,952 |
| `br` to a register (jump tables / tail calls) | 2,522 | 9,399 | 4,306 |
| FP / SIMD (whole class) | ≈ 461 K (20 %) | ≈ 294 K | ≈ 191 K |
| Exclusive / acquire-release | 10,389 | 3,253 | 66 |
| of which **pairs** (`ldxp/stxp`) | 0 | 0 | 0 |
| AES | 0 | 532 | 0 |
| CRC32 | 0 | 18 | 0 |

Implications: ≈ 2,500 candidate jump tables in `main` (≈ 16,200 in all); 23 K indirect calls → the dispatch table
must be fast; atomics are plentiful (the atomic semantics are critical); AES / CRC32 only in the SDK.

## 4. SVCs

Only the `sdk` module holds `svc` instructions (61 distinct numbers, one per wrapper); `main` and `subsdk0` call the
SDK. `main.npdm` declares 50 allowed SVCs (memory, threads, `ArbitrateLock/Unlock`, `WaitProcessWideKeyAtomic`,
`SignalProcessWideKey`, `WaitForAddress`, `SignalToAddress`, `SendSyncRequest*`, `MapPhysicalMemory`,
`GetThreadContext3`, `FlushProcessDataCache`, …).

## 5. Services (from `main.npdm`, 46)

`acc:u0, aoc:u, apm, appletOE, audin:u, audout:u, audren:u, banana, bcat:u, bsd:u, bsdcfg, caps:su, caps:u, csrng,
friend:u, fsp-srv, hid, htc, htc:tenv, htcs, hwopus, irs, ldn:u, ldr:ro, lm, mii:u, mm:u, nfc:mf:u, nfc:user,
nfp:user, ngct:u, nifm:u, nim:eca, notif:a, nsd:u, ntc, nvdrv, pcm, pctl, pl:u, prepo:u, set, sfdnsres, ssl,
time:u, vi:u`

Declaring a service doesn't mean using it. Real use is in §6 and in `docs/dev/research.md` (Q2).

## 6. `main`'s real surface towards the SDK

- **324** functions imported by `main` (UNDEF), **201 of them `nn::*`**: `os`=66, `hid`=35, `fs`=26, `audio`=18,
  `oe`=17, `mem`=8, `prepo`=8, `vi`=7, `account`=5, `time`=4, `settings`=2, `codec`=1, `diag`=1, `util`=1, `aoc`=1.
- NVN: `main` only imports **`nvnBootstrapLoader`**; the whole NVN API is obtained through the function table it
  returns (not through symbols). All of NVN has to be implemented behind that loader.
- `nn::ro` is in the SDK (33 symbols) but **not** among `main`'s imports (confirmed unused at run time: Q7).
- libc imports: `memcpy`, `strlen`, `rand`, `sinf/cosf`, `vsnprintf`, `strtol`, `__cxa_guard_*`… (the sdk provides them).

## 7. Middleware found

| Component | Where | Evidence | Consequence |
|---|---|---|---|
| **Wwise** (Audiokinetic, © 2006–2020) | `main` (static) | strings `AK::BankManager/Voice/Bus/EventManager`, `AK::OpusDecodingThread`, `AK::IOThread`; legal notice | the audio engine **is lifted**; the host provides `audren`/`audout`, threads and I/O |
| **Opus** | `main`, `sdk` (283 strings), `subsdk0` | `AK::OpusDecodingThread`; the `hwopus` service in the npdm | HLE of `hwopus` with libopus |
| **nn::movie** (Stagefright, VP9 / H.264) | `subsdk0` | `movie::Player::Create`, `NvMMVP9Support`, 355 H.264 strings | **HLE** of `movie::` with FFmpeg (not lifted; depends on NvMM / nvdec) |
| Simplygon | data | legal notice | content tool only |
| Immersion (rumble), DynaFont / Fontworks | legal notice | | rumble through SDL; fonts through `pl:u` |
| rapidjson, `mm_lib`, `anmlib` | `main` | internal source paths | compiled into `main`, nothing to do |
| Lua / CRI / FMOD / Havok | — | ≤ 7 matches, no evidence | not considered |

## 8. Conclusions that changed the plan

1. **A small `nn::` surface (201 imports)** against ≈ 1,100 in ssbu: direct HLE would be viable, but LAS's approach
   (lift the SDK and simulate SVC / IPC) stays the lowest-risk path (ADR 0001).
2. **18.2 MB of `.text` to recompile (≈ 4.56 M instructions)**: big; LAS's chunking and selective `-O0/-O1` are
   required, and the build-time target becomes a goal, not a guarantee.
3. **Audio = lifted Wwise + `audout`/`hwopus`** (ADR 0008).
4. **Video = `movie::` in `subsdk0`**: HLE with FFmpeg (ADR 0009).
5. `main` without symbols → function discovery and hooks depend on `.eh_frame` and signatures; the `sdk` and
   `subsdk0` symbols help (25 K and 11.5 K).

## 9. RomFS (2.0.0, base + patch) — in `targets/romfs/`

Extracted from a legally owned copy (base + 2.0.0 patch).

| Folder | Files | Size |
|---|---|---|
| `chr` | 7,782 | 4.12 GB |
| `map` | 168 | 3.51 GB |
| `sound` | 41 | 2.71 GB |
| `cs` | 432 | 1.69 GB |
| `menu` | 5,612 | 0.87 GB |
| `eff` | 2,798 | 0.35 GB |
| `movie` | 14 | 0.24 GB |
| `bdat` | 627 | 0.06 GB |
| `script` | 974 | 0.04 GB |
| `monolib`, `config`, `param` | 65 + 4 + 12 | < 0.03 GB |
| **Total** | **18,529** | **13.61 GB** |

Format findings:
- **Audio:** Wwise `BKHD` banks with **bank version 134** (Wwise 2019.2.x) and `AKPK` packages (`BGM.pck`, `en.pck`,
  `jp.pck`, `se.pck`, `Default.pck`). The Wwise engine in `main` matches that version: nothing to convert.
- **Video:** the 14 cutscenes are **WebM** (EBML header `1A 45 DF A3`), i.e. VP9 with Vorbis or Opus → FFmpeg decodes
  them directly.
- **Data:** `bdat/` (627 files of game tables) and `script/`.
- The game loads about 18.5 K files through the RomFS → `fsp-srv` must be fast with big directories (listing cache,
  `OpenFile` without copies).
