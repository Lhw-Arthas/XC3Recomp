# M3 evidence — diagnostics (2026-10-17)

- **Watchdog (T027):** `XCDE_TEST_HANG_AT=120` hangs the presentation thread; after 5 s the report comes out (threads
  with the guest function of their last SVC, e.g. `InternalConditionVariableImplByHorizon::Wait`) and
  `crash/stall_N.txt` is written. 10 normal boots without false alarms.
- **Minidump (T028):** `XCDE_TEST_CRASH_AT=150` → an access violation; `crash/crash_<date>.txt` (exception, host
  registers, guest threads) and `crash/crash_<date>.dmp` (≈ 1.2 MB, `MDMP` header, written by a second process).
- **Determinism (T029):** first version (clock derived from frames): 2.1 % of frames identical between two runs.
  Second version (cooperative scheduler + virtual time + virtual timers, `XCDE_DETERMINISTIC=1`): three title runs
  (35–60 s, 2,299 frames, 2,007 distinct images) with **an identical hash on 100 % of the frames**
  (`python tools/hash_diff.py a b`). With an input route (`XCDE_INPUT_REPLAY`, A at frame 600) two runs match on
  2,595/2,595 frames and diverge from the input-less run from frame 603.
  Causes that had to be closed: the wake-up order of host threads, vsync and the end of an audio buffer in real time,
  timeouts on the real clock, asynchronous shader builds (draws dropped until ready), GPU counters and the frame pacer
  on the host clock. A useful intermediate failure: with strict priorities the loader threads (prio 46/47) never ran;
  the scheduler uses FIFO.
  Limits: not "real time" (no pacing; the game sees a virtual 60 fps); a thread busy-waiting without SVCs would hold
  the baton; measured on the title only.
- **Strict mode (T033):** with `XCDE_STRICT=1` boot stops at the first unimplemented command
  (`[am] ISelfController cmd 91`) with the guest + host stack. 60 s coverage (`hle_coverage.tsv`): 9 unimplemented IPC
  commands (am, pctl); no unknown HLE import or SVC. `docs/hle_audit.md`: see the summary at its end.
- **Pending in M3 then:** T034–T037, T039–T043 (recording what the game asks for, missing SVCs / services, profiler,
  etc.) — most were done later (see `docs/dev/tasks.md`).
