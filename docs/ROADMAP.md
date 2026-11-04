# XC3Recomp roadmap

The plan for the native Windows port of *Xenoblade Chronicles 3* (version 2.2.0, build ID `82D187FE9EF9BE92`).
Each phase lists what is done and what is open; update it when an item lands (commit hash) or a new one is found.
Status as of 2026-11-04.

## Phase 1: Native Windows development

Status: **in progress**.

Done:
- Static recompilation of `main` / `sdk` into C (`generated/`), linked into `build/xcde.exe` (`scripts/build_all.sh`).
- Kernel / HLE services, the alias region backed by a physical memory pool imported into Vulkan.
- Vulkan renderer: Maxwell shaders translated to SPIR-V, precompiled shader cache, pipeline cache.
- FSR 3.1 / FSR 4 in place of the game's own temporal upscale (DLSS path present, untested: AMD GPU).
- Input (pad, keyboard, mouse), audio, movies, saves (with a backup per launch).

Open:
- Black / red box by the Colony 9 waterfall: one draw (vs `61e0c6ed00`, fs `61e0c6f400`, G-buffer albedo pure red).
  Not caused by the alias-region pool reads (checked with `XC3_PMM_MIRROR=1`, deterministic replay). Cause open.
- `nvnCommandBufferDrawTransformFeedback` not emulated (called in Colony 9).
- Vulkan executor: command 50 unimplemented.
- About 17 fragment shaders failed to translate (older note, to be rechecked).

## Phase 2: Gameplay compatibility and optimization

Status: **partially underway**.

Done:
- FPS option 30 / 60 (60 = the community 60 FPS patch, ported; cutscenes stay at 30). 120 was tried and dropped:
  movement ran too fast.
- Alias-region streams read from the pool in place (`59be42a`): Colony 9 at the 30 option 18 -> 29 fps (capped),
  GPU 37 -> 12 ms per frame.
- Session recording without capture freezes (`3e8e0ca`).
- Shader stutter at first use: the SPIR-V cache (`cache/spirv.pack`) is read through a handle per build thread, not
  one shared handle (Windows ran those reads one at a time): program builds over 3 ms 1095 -> 84 per Colony 9 replay,
  pack reads 5.7 -> 0.2 s. Shadow-pass programs are not waited for either (a model's shadow comes a few frames late).
  Still open: pipeline libraries built by AMD's driver at first use (8-70 ms); loading-frame holds (frames of 0-45
  draws held for the build work: 62 holds / 5.5 s in a 6.5 min session - loading screens, maybe menus: to confirm).
- Frame lag at the 60 option (launcher / F1 "Frame lag (60 FPS)", `xc3.ini frame_lag`, default on): one frame in
  flight instead of CPU and GPU taking turns; Colony 9 replay 52 -> 60 fps, ~10 min of live play without issues.

Open:
- Test beyond the title screen, opening and Colony 9: Everblight canyon, battles, long cutscenes, other regions.
- Render-thread CPU cost (~2.7 us per draw), ~800 pass splits per frame (writer draws + game barriers), ~75 hitches
  per replay (mostly loading).
- Validate save loading and story progression; stability across areas.

How it is tested: the user records a session from the launcher ("Record the session" -> `play/<timestamp>`, a save
backup in `save/backup/`); it is replayed hidden on a scratch copy of the save (`LARECOMP_SAVE_DIR`). Replays are not
deterministic: A/B comparisons of images use `XCDE_DETERMINISTIC=1` (+ `XCDE_TMP_DETERMINISTIC=1` to keep FSR on);
performance is measured without it (it changes the timing).

## Phase 3: Launcher and installation

Status: **planned, early work done** (lower priority than phases 1 and 2).

Done:
- `tools/launcher`: graphics, upscaler, FPS, controls, button prompts, language, session recording, reports.
- Launcher named "Xenoblade Chronicles 3" (`build/xenoblade3_launcher.exe`, `bf9de01`), dark theme, our own icon,
  optional background `mods/launcher/background.png` (`c15a3c7`).
- In game: cursor hidden while the window has the focus (`658faa1`); SMAA skipped while FSR / DLSS runs (`f0ad94e`).
- `scripts/build_all.sh`: dump check, recompilation, build; shader precompilation.

- Launcher tab "Install & build": the game files (folder picker, version check, `targets\` junctions) and the build
  (`build_all.sh` with a step bar, Stop, log), the launcher swapping its own exe (renamed, not overwritten). The tools
  are installed by `Build XC3.bat` (first time only).

Open:
- Choosing an install folder other than the repository.
- Extraction from the user's own game packages (today: already extracted `exefs` / `romfs` folders only).
- Updates and DLC: everything (patches, hooks, addresses) is tied to 2.2.0; another version means finding every
  address again.
- Installation management.

## Phase 4: Public source and testing

Status: **planned**.

Before publishing:
- Audit the repository **and its git history** for anything derived from the game: `dump/`, `targets/`,
  `generated/`, caches, saves, `play/` recordings, screenshots (`.gitignore` covers them today; history must be checked
  too - a file once committed stays in it).
- Check the licences of third-party code and SDKs for redistribution (`LICENSE`, `NOTICE.md`): LASRecomp / Monado,
  FidelityFX SDK, Streamline / DLSS, SDL.
- No Nintendo / Monolith Soft assets or branding in the repository or test builds.
- README for XC3 (today's README describes Monado / XCDE).

Then:
- Build and installation documentation; test builds; issue reporting and contribution guidelines
  (`CONTRIBUTING.md` exists, written for Monado).
