# M2 evidence (2026-10-17)

- **Jump tables:** main 18 → 732 resolved (93.4 %), sdk 43 → 492 (89.9 %) after fixing the function partition by the
  table-base `adr` (`gen.py: adr_targets`, 8 tests in `tests/unit/test_jumptables.py`). 52 (main) and 55 (sdk) remain.
- **Generated C:** main 142 MB, sdk 90 MB (145 + 91 before).
- **Full build** (zig cc 0.16 / clang 21.1, `-O1 -march=x86_64_v2`, 16 threads): **131 s**, 312 chunks, 0 errors,
  323 MB of objects. Meets NFR-005 (≤ 30 min) with a wide margin.
- **Differential against Unicorn** on real encodings from XCDE's `main`: 6,000 encodings / 17,970 cases and
  15,000 / 44,964 cases, **0 failures**. The only unsupported instruction in the sample: `trap` (udf).
- **Atomics:** LAS already uses `__atomic` with acquire / release and `__atomic_thread_fence`; XCDE holds no exclusive
  pairs and no LSE (CAS / LDADD / SWP), which the lifter doesn't support (0 `Unsupported` in the generation).
- **FRSQRTE / FRECPE:** already table-driven (`simd_rsqrt_tab`), no 500-step loops (T026).
