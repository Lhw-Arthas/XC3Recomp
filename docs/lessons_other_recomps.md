# Lessons from three public Switch recomp/port projects (2026-10-18)

Read for ideas only: no code was copied (Art. I–III). Each item says what we checked in XCDE and which task tracks it.

| Project | Base | Useful part |
|---|---|---|
| raulzrrs/letsgo-recomp (Pokémon Let's Go) | LASRecomp (MIT), Windows, Vulkan | `docs/HISTORICO.md`: 66 problem → cause → fix entries |
| BelmanteGu/SuperMarioWonderRecomp | own "SwitchGamesRecomp" runtime, Vulkan/MoltenVK, Ryujinx translator offline | `docs/nvn/DEBUG.md`: rendering bugs with symptom / cause / fix |
| ly05010419/MacNativeGames (Zelda TotK) | runs ARM64 natively on Apple silicon (not a recomp), NVN on Metal 4 | packaging, shader seed + prewarm, hash-checked RomFS |

## Confirmed by our own work
- **Movie output buffer** (Let's Go #12): the game hands the decoder a Buffer over its own memory and reads that memory. Same bug and fix as our T118.
- **Condvar timeout race** (Let's Go #5, #15): our T067.
- **Programs without a fragment stage** (Let's Go #19): our T064.
- **Textures over the same memory share one image** (Wonder #36): our T107/T110.

## To check or adopt (tasks)
- **T125** Program cache keyed by code address only (Let's Go #66: wrong shaders after streaming). Done 2026-10-18: content hash per stage at `nvnProgramSetShaders`.
- **T126** Constant reads past the bound bank must return 0 (Wonder #21: garbage gave loop counts in the billions and GPU hangs). Zero-pad the copied range to what the shader reads.
- **T127** `LDC.64` with the address register also a destination (Let's Go #21: exploded meshes). Check `maxwell/translate.c`.
- **T128** Upstream LAS fixes listed by Let's Go #62: fence sequence, null colour slots, duplicate pipeline keys, IPA multiply, I2I / SHF / HSETP2 semantics. Compare with our `upstream/lasrecomp@136f679`.
- **T129** Textures / pool slots re-initialised between recording and execution (Wonder #55–57: intermittent bands, exploded meshes; Let's Go #60: stale host pointer in the pool after a streamed texture is re-initialised). Candidate cause for T124.
- **T130** Movie decoder output slots: rotate instead of reusing the slot just freed (Let's Go #13: robotic movie audio); extractor end-of-stream code `0x2000` (Let's Go #16: video never ends).
- **T131** Shader semantics to audit: integer vertex inputs (Wonder #25), sRGB view formats on views/attachments (Wonder #29), FMZ (Wonder #49), NaN in `.SAT`/FMNMX (Wonder #54), `TMML` (Let's Go #24), RGB5A1/RGBA4 bit layout (Let's Go #22).
- Performance ideas for M8: render thread with fence tickets (Let's Go #59), VRAM ring for vertex/index streams (#58; ours is the vertex cache, see T121), spin before sleeping on contended locks (#57), shader translation on worker threads (#30), pipeline cache saved in the background (#25), shader seed + prewarm (TotK).

## Mario Wonder `docs/nvn/DEBUG-2.md` (read 2026-10-18)
- **T132** Upload ring wrapping over data the GPU has not copied yet (Wonder #72: black/green character textures after large scene loads). Check that `vk_transient` never reuses ring space of an unfinished submission for big uploads.
- **T124/T129 candidates:** pipelined submits racing the game's next frame (Wonder #76: exploded meshes, made submits synchronous by default); re-initialised pool slots resolving to new targets (#92); replay snapshot/sampler history (#63, #64).
- Barrier after every render pass (#71): ours already does a full barrier at each `begin_pass`.
- Pipeline cache read while being written (#86): check our pipeline-cache save thread when T113-style caching lands.
