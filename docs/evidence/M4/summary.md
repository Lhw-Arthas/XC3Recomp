# M4 evidence (historical) — first image (2026-10-17)

- **T052 Maxwell → GLSL translator:** of 40 fragment shaders failing at the first boot, 39 were `TLD4S` and 1 `TLD4`.
  Both implemented (`emit_tld4s`, `emit_tld4` in `runtime/nvn/maxwell/translate.c`, `textureGather`; TLD4 with the
  none / AOFFI offset modes, PTP approximated without per-texel offsets, and depth compare).
  `tests/native/test_translate_tex.c` (10 tests, written first, red → green; words synthesised with field encoders, no
  game shaders). **1** shader with a surface instruction (`SULD`, family `0xeb1x`) was left then.
- **First recognisable image:** at ~30 s (frame 900) the window shows the title screen's **"Press Any Button"** text
  rendered by the game; the background still black. The render passes (`LARECOMP_DEBUG_FRAME`) showed more of the
  game's graphics (e.g. an emblem in the last pass) and a pass with green / red noise (a badly decoded texture).
- **Cause of the earlier black screen:** the `widescreen_present_crop` stub didn't initialise the presenter's UV crop.
- **hwopus:** the game uses command 8 (`DecodeInterleaved`); with the 6 that was implemented it crashed at ~18 s.
  After the fix, 3 runs of 40 s without crashes (≈ 1,100 frames each, 30 fps).
- **Open risk then:** an intermittent hang (≈ 2 of ~15 runs stop at 4–8 s without a crash) — found and fixed as
  T067 / T108 below.

## Stability (2026-10-17, T067/T108)
- The `scripts/repro_stability.sh` loop (25 s boots with a hidden window): ≈ 13 % failures before (3 crashes at frame
  ≈ 240 + 1 hang in 30 boots). Causes: (1) an `ETIMEDOUT` ↔ condvar signal race in `block_current` (`kernel.c`) → a
  thread waiting on its own mutex; (2) the virtual RomFS descriptor cache without a lock (`romfs_virtual.c`) → reads of
  zeros. After the fixes: 53 of 53 clean.

## Audio (T059, partly, 2026-10-17)
- The game (Wwise) doesn't use `audren` (it opens `audren:u` only to query the device and closes it); all output goes
  through **`audout:u`**: stereo PCM16 48 kHz, 0x1000-byte buffers (1,024 frames), `Start`, `AppendAudioOutBuffer`,
  `GetReleasedAudioOutBuffers`.
- Dump: `LARECOMP_AUDOUT_WAV=<path>` (a valid PCM16 WAV; one file per `IAudioOut`) and
  `python tools/wav_report.py <wav>`. A 65 s capture in real time (≈ 0.7× before: `nanosleep` rounded to the 15.6 ms
  tick; absolute deadlines now): silence 0–12 s (loading), then a tonal signal (peaks ≈ 349 Hz, 469/936 Hz),
  0 clipped samples, no DC. WAVs are not versioned (`build/` is ignored).

### Audio against a reference (T059, 2026-10-17)
Reference: a recording of the title music (not versioned). `python tools/wav_compare.py build/audout.wav ref.wav`:
- The same dominant notes (A#, D, F, D#/G) and a mean chroma cosine of **0.92**; with the best time alignment the
  per-second cosine rises from 0.50 to 0.81 over the last 20 s.
- Almost the same energy split by band (300 Hz–1 kHz ≈ 58 % in both). The reference's mean level is ≈ −40 dBFS: the
  title music is soft, so the game's low level (−45 dBFS) is consistent.
- Not compared: sample-by-sample waveform (the reference is a re-compressed recording) or listening on speakers.

### Intro video (T118, 2026-10-18)
Route `tests/routes/new_game_a.txt`, deterministic mode, captures at frames 1800/2400/3200. Noise score (mean absolute
difference of horizontal neighbours, 320x180 gray): before 20.9 / 21.1 / 20.9 (static), after 0.03 / 1.16 / 1.18.
Intro audio (`LARECOMP_AUDOUT_WAV`, 110 s): 83 % active seconds, 0 clipped, same as the pre-fix baseline.
