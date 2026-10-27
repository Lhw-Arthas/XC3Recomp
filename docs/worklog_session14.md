# Session 14 work log (2026-10-21) - updated as work goes on

Read HANDOFF.md "session 14" first (tasks A/B/C for another account). This file is the live log of what the first
account is doing right now, so the next Claude can continue mid-task.

## User reports (video <local file>) 2026-10-21 00-38-25.mp4)
Frames extracted: <work dir>\vid1021\idx (2 fps, 480 px), \all (every frame, 640 px), \full (picked seconds).
The video is 30 fps (the recorder); the game log (build/last_game.log) shows a steady 60.0 fps, max 17 ms.
1. **Graphics bug in Colony 9 (night)** - not located yet in the frames. Next: ask the user for the second / spot, or
   scan <work dir>\vid1021\all for frame-to-frame anomalies (tools/video_flicker.py).
2. **"Feels laggy / slowdown" at a steady 60 fps, Afterburner frametime flat** (60 Hz monitor, windowed 3840x2160).
3. **Grass looks noisy** after turning off the game's TMAA / blur (T198 option) - expected: TMAA was the game's temporal
   AA. Mitigations: SMAA option (spatial, partial), FSR 3 native AA / DLAA (task A) = the real fix.

## 2. Frame pacing - findings and steps
- The game's own limiter (framepace.c comments, f_70005bcfe0) waits until 0.997 x 1/60 s: ~60.2 fps. On the Switch the
  display (vsync) holds each frame to a vblank. Our present mode was MAILBOX (device.c present_mode): nothing held it,
  so frames drift across the monitor's 59.998 Hz vblanks -> some frames shown twice, some never, while every counter
  reads 60.
- Tried: lock the emulated vsync (vi.c vsync_thread) to DWM vblanks -> the game does not use that path (the thread
  never starts in XCDE; its pacing is the limiter). Tried: lock the limiter (framepace.c xcde_limiter_spin) to DWM
  vblanks. Measured with a present-phase diagnostic (CPU present time vs DwmGetCompositionTimingInfo qpcVBlank) -> the
  metric is NOT reliable: it reported "doubled" frames even with FIFO, where that is impossible. All of that reverted.
- Kept (uncommitted, build/xcde_vs.exe): **V-Sync option** = FIFO present at FPS 30 / 60 (xcde.ini `vsync = 1`,
  default on; launcher "V-Sync (con 30 / 60 FPS)"; device.c present_mode logs "[vk] present mode fifo (V-Sync option)").
  Mailbox stays for FPS > 60 / unlimited (FIFO would cap it) and with LARECOMP_VK_PRESENT. FIFO at 60, 4K, meadow spin:
  steady 60.0 fps, max 17 ms (one 89 ms load hitch). Risk (old note in present_mode): a throttled / captured
  compositor slows the game with FIFO - the option can be turned off.
- Kept: **frame lag only above 60 fps** (objects.c SyncWait, "[nvn] frame lag on/off" in the log): at 60 the frame fits
  the period (~8 ms of 16.7 at 4K on the RTX GPU), the extra frame in flight only added a frame of input latency.
- Next steps: verify xcde_vs.exe (verify.sh no-regression: tests don't present; perf4k uses XCDE_FPS_PERIOD_SCALE ->
  mailbox, so the 166 fps measurement is unchanged), commit, copy to build/xcde.exe, set the user's xcde.ini vsync = 1,
  ask the user to feel it.

## 2026-10-21 afternoon (graphics session; parallel with the party-mod session - see HANDOFF.md top)
- T205 faces as vertical strips: fixed (exec.c xsh_retire_overlaps), in build/xcde.exe (012e562); a fresh load never
  showed it (needs scene changes that rebind the writers' scratch memory) - the user is to confirm in a long session.
- T207 cutscenes "feel 30": measured with XCDE_DUP_CHECK at 60 fps - a new image every frame; open until the user names
  a scene (d0ec7b4).
- Stutters (in progress): user's 15:09 session had no build wait > 8 ms; long frames = bursts of disk-cache pipeline
  loads (1,604 in 2 s at t=28: 109 ms of waits) and some with no builds (83 ms, ~100 MB uploads). Added "[hitch]" per
  frame > 25 ms (device.c backend_present + exec.c vk_hitch_counters: waits, cached / linked / whole pipeline counts and
  build-thread time, upload MB; on by default, 300 lines max). Running walk_far.txt on faces_1515 at 60 fps
  (build/hw1.log) to attribute each hitch; next: fix the biggest cause.
- Shader hitches (T209 / T211, ~17:40): fixed the 2-minute cache-save freeze (b9cc1ce), stale precompile -> re-run on
  every new build (da2af35), libraries prebuilt when the game registers programs + link first (b9ea0bd). Test setup for
  "a player who never visited the area": <work dir>/coldroot (junctions targets / tests -> the repo; own build/,
  cache/, save_cold/; precompile there, then walk_far.txt; NEVER delete the junctions with rm -r / Remove-Item
  -Recurse: use `cmd /c rmdir`). Plan left (user wants 0 hitches without visiting all 30 areas): wider variant
  guessing in precompile.c from the [variant-miss] log (exec.c compile_program), a shipped variant seed
  (cache/variants.bin union), background preparation while playing (paused in battle - OpenSmash lesson), a loading
  barrier, a fallback variant instead of a wait.
