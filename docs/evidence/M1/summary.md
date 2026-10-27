# M1 evidence (2026-10-17)

- `tools/gen_all.py` generates `main` (0x7000000000) and `sdk` (0x7004000000) from the profile `games/xcde/profile.json`.
- **Reproducible:** two independent runs give the same hash of the generated tree (`main` db2d12c0…, `sdk` edc36808…),
  11–12 s in all.
- **Coverage:** see `coverage.md` (0 unsupported instructions in both modules).
- **Patches:** a format with expected bytes (`tools/lifter/patchfmt.py`, 6 tests); `games/xcde/patches.py` empty.
- **Key finding:** only 18 of `main`'s 1,101 jump tables (1.6 %) were resolved by LAS's resolver → M2.
- Local function map: `build/maps/<module>.csv` (not versioned). `main` has symbols for only 21 functions.
