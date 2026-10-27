# Party switch research (Task C, phase 1) - findings

Plan: docs/plan_party_switch.md. This file collects what is known; addresses are from deterministic runs
(scripts/drive_env.sh) and the saves in <work dir>\saves.

## 2026-10-21 (session 15)

### The save-data block in memory
- The game keeps its save data (the whole bfsgame*.sav image, 1,392,432 bytes = 0x153F30) at guest address
  **0x726e3d3040** in deterministic runs from both the user's Colony 9 save and the Reyn meadow save. Found with
  `XCDE_FIND` (two 32-byte chunks of the loaded save file, offsets 0x46940 and 0x149c00, both point to that base).
  Other partial copies (0x728d...) are save serialization buffers.
- It is not plain storage: many fields change every few frames (`XCDE_HASH_MEM` over the block). But the party and
  the player position in it (+0x149c10: three floats x, y, z) do not change while walking: they are written when the
  game saves, and read when it loads.

### Party order (the leader)
- **+0x1526d8: u16 member ids**, in party order (slot 0 = leader); **+0x1526f0: u32 member count**. Ids: 1 Shulk,
  2 Reyn (others to confirm: probably 3 Fiora, 4 Dunban, 5 Sharla, 6 Riki, 7 Melia, 8 Fiora-Mechon). Found by diffing
  the Shulk-only save (1, 0 / count 1) and the Reyn save (1, 2 / count 2): the only u16 / u32 / u8 location with that
  pattern in the block.
- Writing it in memory while playing (`XCDE_POKE`) changes nothing (the menu still shows Shulk as leader): the game
  builds a runtime party from it at load.
- **Editing the save file works**: bfsgame00.sav with 02 00 01 00 at 0x1526d8 loads with **Reyn as the leader** -
  controlled in the field (camera behind Reyn, Shulk following) and "Leader" on Reyn in the main menu - in a save where
  the game itself doesn't offer a Party menu yet (it unlocks later in the story). No checksum on the file.
  (<work dir>\saves\reyn_leader_test; captures build/pl1_3680.png, pl1_3800.png.)

### Tools added for this (runtime/diag/diag.c, runtime/platform/windows.c)
- `XCDE_FIND="<frame>:<hex bytes>[,<hex bytes>...]"`: guest addresses of byte patterns (committed pages of the main
  image and heap, up to 64 each).
- `XCDE_POKE="<frame>:<hex addr>:<hex bytes>[;...]"`: write bytes at a frame.
- Existing: `XCDE_DUMP_MEM`, `XCDE_HASH_MEM`, `XCDE_WATCH` (data watchpoint - **reported nothing** on the save block
  between frames 700 and 3800, including the load, and nothing on a known-changing range either: check it works before
  relying on it; the save file may be read straight into the block by the host fs code, which a page protection
  doesn't attribute to a guest function).

### Next steps
1. Fix / verify `XCDE_WATCH` (e.g. on a range a guest function surely writes every frame), then watch +0x1526d8 from
   just before the load (A at frame 1800 of load_a / load_spin) to find the function that reads the party at load:
   its destination is the runtime party object.
2. Or find the runtime party by search: after loading the Reyn-leader save vs the normal one, `XCDE_FIND` for
   pointer pairs / ids in a different order (the runtime list probably holds actor pointers; the leader's actor is the
   one the camera and the pad drive).
3. Overworld leader switch prototype (phase 2) without the runtime structure: write the new order into the block and
   make the game reload the party (find a game routine that does it: a map change or the Party menu's commit -
   the menu appears later in the story; a save that far would help - ask the user for one).

### Runtime party (same session, later)
- Heap dumps of the same frame (XCDE_DUMP_HEAP, 3.2 GB each, <work dir>\party) from the normal Reyn save and the
  Reyn-first edit, diffed for swapped id / pointer pairs: **the live party list is at 0x726e526f70** (right after the
  save-data block; same layout: u16 ids, u32 count at +0x18). Other hits were save buffers or heap-layout noise.
- Poking it while playing (02 00 01 00): **the main menu shows Reyn as leader at once**, but the field keeps Shulk
  controlled - the field actors are bound to the party when they spawn. A skip travel (Area Maps -> Mechon Wreckage
  Site) does not re-bind them either (arrival identical with / without the poke).
- `XCDE_WATCH` does work (it reported nothing earlier because guest code doesn't touch those ranges; the save file is
  read into the block by host code). On the live list from frame 700 (load): read by f_70004c55b0 (+0, +2, +0x18; 18
  callers), f_7000536ab0, f_70000a74c0, f_70005419e0, f_7000149910, f_7000149ad0, f_70004c83e0 (+0x18 = count).
- Next: find which of these (or their callers) creates the field player actor from slot 0 and which object holds
  "the controlled actor" (camera target / pad input) - then a switch = re-run the game's own respawn for the new
  order, or move the control binding (XC3-style) without respawning. A save where the game's Party menu exists would
  let a function trace show the game's own leader-change path.

### Field actors (faces_1515: party [3 Fiora, 1 Shulk], Fiora leads) - frame 2700 of load_walk
- Each party member has a field character object of class **vtable 0x7000b5e368** (exactly two instances):
  Fiora 0x726eb40d50, Shulk 0x726eb4de50. Fields: +0x08 party manager (0x726b027fa0), +0x34 u32 entity handle
  (Fiora 0x54, Shulk 0x57), **+0xac u32 character id** (3 / 1), +0xc8 (2 / 1), +0xd0 a name string ("wp3101" /
  "wp1501"), +0x3d0 position (x, y, z floats; the leader's is the walking one).
- Global entity table at ~0x726e5ab150: (object pointer, u64 handle) pairs; Fiora at 0x726e5ab1e0 (0x54), Shulk at
  0x726e5ab210 (0x57). References between objects go through these handles.
- Movement components (class vtable 0x7000b57c78, 14 instances: party + NPCs): Fiora 0x726eb44060 (+0x40 position),
  Shulk 0x726ebe4b80; updated on the job thread by f_70003e8960 / f_70003e7550 (f_7000040ea0 job system).
- **f_70004c2080 = the follower ("follow the leader") logic**, run per frame for Shulk's object only, and only while the
  leader moves (fnprof walk vs still, 60-frame windows: walk-only, 60 calls). Called from f_7000432190+0x97f
  (<- f_7000431620 <- f_7000410a90 <- f_7000411320, the per-frame character update); just before, a virtual
  call (vtable +0x60) must return 3, and f_700049fa80(...)->+0x38 gives the object it gets.
- The party manager 0x726b027fa0 is x0 of the list readers f_70004c55b0, f_70004c83e0, f_70004c9290.
- Tools: XCDE_WATCH_BT=1 prints the guest call chain of each watch hit (runtime/dispatch.c); LARECOMP_FNPROF_BT
  gives x0 at entry (the object); XCDE_DUMP_HEAP + tools in this doc's scripts (diff / vtable search / object dump).

### Plan from here
1. Find where the leader is chosen for the field: who decides the vtable+0x60 == 3 path / which object is "the
   player" - a field in the party manager or a per-character flag. Compare Fiora's and Shulk's character objects
   (done: +0xc8 2 vs 1 and +0xc0 differ) and test by poking one of them while walking.
2. The input side: the game reads the pad via nn::hid (runtime/hle/input.c logs the caller lr 0x70005be69c); follow
   the pad state into the object that moves the leader.
3. Then the switch: make the chosen character the player (pad + camera), the old leader a follower (f_70004c2080 path).
- Ruled out (field leader flag / rebuild): swapping the character objects' +0xc8 (2 / 1) while walking (control stays
  on Fiora); swapping BOTH party lists (save block + live) then a skip travel (arrival identical: the field party is not
  respawned by a skip travel). LARECOMP_WATCH_PAD watches a stack buffer (noise). The game's own copy of the stick was
  not found as floats / ints in the heap at frame 2700 (route values 9421, 24233).

## 2026-10-21 later: the game's own leader change found, field switching works (T206)
- faces_1515 HAS the main menu's "Party" entry: swapping Fiora / Shulk there and closing the menu makes Shulk the
  controlled leader at once (camera, pad), Fiora follows (captures build/psx_*). fnprof swap vs no-swap (frames
  3190-3320 of build/route_sw2.txt / route_ns2.txt): 283 swap-only functions; the chain is f_70000e6d50 ->
  f_7000542a50 -> f_700054a390 -> f_700054a660 -> f_7000524d00 -> f_70005419e0 -> f_7000541e10, which calls
  **f_70000507e0(party manager, new leader's entity handle)** then **f_70004c5710(party manager, new leader's id)**
  (set leader: rebuilds the player's action handlers on the new leader's components).
- Player control path (for reference): f_70000417e0 (party manager, per frame) -> f_70000261a0 (pad sampling into
  the input object 0x726e189590, buffer at +0x10) and f_70000e6d50 (player object 0x726e3ce1e0, vtable 0x7000b3c740)
  -> f_70000e8eb0 -> f_70000276f0 / f_7000027180 (stick -> movement) -> handlers pointing at the leader's components
  (e.g. its jump component, vtable 0x7000b59890).
- Getting there from the runtime (runtime/hle/party.c): the party manager = the one object of vtable 0x7000b35210 +
  0x20; the live list = f_70000b6790(party manager); a member's entity handle = +0x34 of its character object
  (vtable 0x7000b5e368, id at +0xac). Called on the game's main thread from the pad read, registers restored.
- Results: field (faces_1515, load_walk, switch at 2550): Shulk becomes the controlled character, camera on him,
  Fiora follows. Battle (colony9_20261019_1235, battle_b, switch at 3300): no crash, camera and auto-attacks move to
  Reyn, Shulk keeps fighting under the AI - but the HUD keeps Shulk's portrait first and Shulk's arts palette: the
  battle UI / arts binding is not rebuilt by this call (next step: find what the battle HUD reads for "the player").
- Keys: F2, or L3 + R3 on a pad (runtime/hle/input.c). XCDE_PARTY_SWITCH_AT=<frame>,...: switch at those frames.

## Battle, guards, options (same day)
- **Battle arts palette**: the battle HUD (one object, vtable 0x7000b63248, also present in the field) has a battle
  sub-object at +0x2c0 (zero outside battles): +0x10 the entity handle of the character it shows (set at the battle's
  start to the leader's), +0x70 bit 1 = "rebuild": its per-frame update f_7000550b00 then calls f_700054fbe0, which
  fills the arts palette (one object, vtable 0x7000b63a00: entries of 0x10 bytes, art id first - Shulk 2 / 0xc / 0xd,
  Reyn 0x13 / 0x14 / 0x15 / 0x1f). A switch in battle writes the new leader's handle and sets the bit: the palette
  shows the new leader's arts at once. Found by a heap diff of two battles that differ only by one d-pad press
  (the palette's selected index, 4 -> 5) and by watching the palette's writers.
- Portraits keep their order (built at the battle's start) - as in Xenoblade 3, where they don't reorder either.
- **Cooldowns / positions**: they live on each character: switching away and back keeps the art recharge (same
  palette as a run without switches); nobody is moved, only control and camera.
- **Guard** (player_in_control): the player object (one, vtable 0x7000b3c740): +0xc 1.0 and +0x10 0, and the lock
  counters at +0x136 +0x13a +0x13e +0x142 +0x146 +0x14a +0x14e +0x156 +0x15a +0x15e +0x176 +0x17a +0x19e all 0 -
  measured 0 in field and battle, non-zero with the main menu open or in a cutscene. Tests: a Colony 9 cutscene (4
  presses: all refused), the main menu (refused), loading (refused), field and battle (accepted).
- **Downed members**: battle HP gauges (vtable 0x7000b44b08, one per fighter: -0x38 entity handle, -0x10 current HP);
  a member at 0 HP is skipped (XCDE_PARTY_TEST_DOWN=<id> to test: Reyn "down" -> Fiora chosen, her 222 HP read right).
- **Three members** (a copy of the battle save with [1, 2, 3]): Shulk -> Reyn -> Fiora -> Shulk in battle and field.
- **No-use equivalence**: deterministic captures without a switch match runs of older exes (only the known run-to-run
  noise at the top of frame 2700).
- Option: off by default; launcher Controls "Switch characters like in Xenoblade 3 (F2 / L3 + R3 together)",
  xcde.ini party_switch = 0/1 (g_party_switch in settings_ini.c; F2 / L3+R3 ignored when off).
- Lookups: a scanner thread (party_scanner) finds the objects ahead of time; a switch never scans (a scan on the game's
  thread was a visible hitch: 0.17 - 0.6 s on the first switches).

## Bigger party, followers, lock, 60 fps (same day, the user's 7-member Fallen Arm save)
- **Only the deployed members rotate**: the live list holds the whole roster (deployed = the first 3, the Party
  menu's slots 1-2-3, then the reserve). Rotating the whole list pulled reserve members in (not spawned: invisible
  followers, wrong models, empty portraits).
- **Entity handles**: the character objects' +0xac is NOT stable across leader changes (a change rebinds them; the
  second switch got Sharla's entity for Shulk). The game's own lookup is f_70004c5490(party manager, character id)
  (the entity whose arts control's +0x8 is that id; the Party menu uses it through f_7000541c00).
- **Followers follow the field group, not the list**: group = f_7000593120(&party manager)->+0x40 - 8 (vtable
  0x7000b5f250: +0x18 count, +0x20 clear, +0x28 add(handle) = f_70004cf9a0, +0x40 entry(i); entries of 0x30 at +0x6a0:
  handle, +0x10 formation target; count at +0x730). Slot 0 is the leader the others follow. The Party menu's close
  (f_70005419e0) clears it and adds the 3 members in the new order before its leader change; the mod does the same.
- **Lock after a switch while running** (~0.7 s still): the new leader keeps the "follow the leader" move it was doing
  as a follower - a pending per-frame callback of its movement component (party character object, vtable 0x7000b5de38,
  + 0x1a38: +0x198 bound call, +0x1a0 invoker f_700042d3d0, run by f_700042a280). Clearing the invoker at the switch
  hands the movement to the pad at once (the game clears it itself when the move ends).
- **Followers behind at 60 fps (not the mod; T210)**: a follower restarts its "follow while running" state (AI state 3,
  vtable 0x7000b5c4b8) when a message reaches its handler f_7000456f70 and f_70004439f0 finds the movement component's
  +0x200 frame counter > 9 - a 30 fps threshold that trips every ~11 frames at 60 (the movement restarts from a walk).
  Patched (games/xcde/patches.py) to the same time at any frame rate. Found by: positions (entity + 0x110, entity =
  f_700049f8c0(&tmp, party manager, handle) -> vtable +0x38) at 30 vs 60 fps, the AI state stack (character object +
  0x19a8: states linked at +0x8 / +0x10, +0xc requested transition), fnprof of single frames, XCDE_WATCH on the state.
- Verified by the user: the art used after a switch is the new leader's (damage, animations), Chain Attack and
  Visions with switching (100% save).
