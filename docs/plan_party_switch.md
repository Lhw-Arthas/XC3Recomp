# Plan (draft): Xenoblade 3-style character switching in XCDE (2026-10-21)

User's request: switch the controlled character mid-battle and in the overworld "exactly like Xenoblade 3", keeping all
of the game's logic: equipment, arts, art cooldowns (recharge), talent gauge, party gauge, position, HP, buffs /
debuffs, aggro, AI. This file is the plan to research and build it; nothing is implemented yet.

## What Xenoblade 3 does (the target)
- In battle, the d-pad / a shortcut changes which of the active party members the player controls, instantly, without
  a menu. The previous one is handed to the AI with its whole state (arts recharging, position, target, aggro).
- The new one keeps its own state: arts palette with each art's recharge, talent art gauge, auto-attack timer, current
  target, position (the camera moves to it), buffs / debuffs, HP.
- In the overworld, the same shortcut changes the leader (the field model / camera follows).
- Nothing about stats or equipment changes: it is only who receives the player's input.

## XCDE (XC1 DE) facts to start from
- XC1 DE already has: a party of 3 active + reserve; the leader is chosen in the Party menu outside battle; in battle
  the leader is fixed (other two are AI, with "Chain Attack" / "Visions" / "Party Gauge" shared).
- Our recomp gives full access to the game code: every guest function is a C function `f_<addr>` (games/xcde,
  build/obj); HLE hooks (runtime/hle/*.c, `HLE_FUNC`), code patches routed to the runtime (games/xcde/patches.py,
  e.g. FRAME_STEPS_SITE, the limiter hooks xcde_limiter_done / xcde_limiter_spin), and guest memory is plain host
  memory (read / write any game structure).
- Only ~360 symbols in main (`loaded main ... syms 360`): game structures must be found by tracing.
- Data: romfs/bdat/*.bdat (96 tables: characters, arts, battle params). The virtual romfs can serve edited files
  (romfs_virtual.c maybe_edit / File.mem) if a table needs a change.
- Input: runtime/hle/input.c + bindings.c (the game reads the pad through HID; a mod key can be a new binding).
- Test tools: input replay routes (tests/routes/*.txt, battle_a / battle_b reach a fight from the Colony 9 save),
  deterministic captures (scripts/drive_env.sh), the function profiler (runtime/fnprof.c), XCDE_TRACE_* logs, saves on
  <work dir>\saves.

## Phases
1. **Research (no gameplay change):**
   - Find the party / leader structures: start from the Party menu's "set leader" action (it exists outside battle).
     Trace which functions run when the leader changes in the menu (fnprof diff of a route that changes leader vs one
     that doesn't), find the party manager object and the "leader index / controlled actor" field.
   - Find per-character battle state: arts palette (art ids + recharge timers), talent gauge, auto-attack, target,
     aggro table, buffs. Method: memory diff snapshots during a fight (an art used -> which floats start counting).
   - Find how input reaches the leader in battle (the controller -> actor binding) and how AI drives the other two
     (an "is player controlled" flag or a controller object per actor).
   - Write findings to docs/party_switch_research.md (addresses, struct layouts, call graph).
2. **Overworld leader switch (smallest useful step):** a key / d-pad binding calls the game's own leader-change
   routine (the one the Party menu uses), outside battle and outside menus / cutscenes. Check: model, camera, party
   following, map icon, save / load keep the new leader.
3. **In-battle control switch among the 3 active members:** swap the "controlled" binding to another actor without
   touching its state; the previous leader gets the AI controller. UI: the arts palette / talent gauge / HP bar must show
   the new actor (find what the HUD reads: probably "leader" pointers that need the same swap). Camera retarget.
   Keep: each art's recharge, talent gauge, auto-attack timer, target lock, position, buffs, aggro (aggro stays on the
   actor - only control moves). Edge cases: switching during an art animation / chain attack / vision / topple-daze
   combo, a downed member (can't switch to it), battle end, cutscene triggers.
4. **(Optional, beyond XC3) reserve member swap in battle:** spawn the reserve actor at the leaver's position with
   its saved state; much riskier (actor creation mid-battle). Only after 3 works.
5. **Options:** launcher toggle ("Cambiar de personaje en combate (estilo Xenoblade 3)"), bindings in the Controls tab,
   off by default; xcde.ini key. Never changes saves unless the leader really changed (phase 2 writes what the menu
   would).

## Verification
- Routes that switch at fixed frames (battle_b + switch keys), deterministic captures before / after, and a check that
  without the option every capture is identical to the current build (no regression).
- Logic checks from memory: arts recharge values continue (not reset), HP / gauge unchanged across a switch, aggro
  target unchanged.
- Real-time battles with the flicker detector; a long fight (the T185 soak route idea) for crashes.
