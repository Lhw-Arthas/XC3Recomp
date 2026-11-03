"""XC3 instruction patches (contract: docs/contracts/patch-format.md).

Every XCDE patch targets XCDE addresses; XC3's sites are found again one by one.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools", "lifter"))
from patchfmt import Patch  # noqa: E402,F401


def _hook_x21_then_original(fn):
    """Call a runtime hook with x21, then the original instruction (which must lift to plain C)."""
    def emit(gen, addr):
        ins = gen.lift(addr)
        if ins.kind != 'op':
            raise ValueError(f'{addr:#x}: hook patch needs a plain instruction, got {ins.kind}')
        return f'{{ extern void {fn}(uint64_t); {fn}(c->x[21]); }} {ins.code}'
    return emit


def _original_then_w22_hook(fn):
    """The original instruction (which must lift to plain C), then w22 = a runtime hook of w22."""
    def emit(gen, addr):
        ins = gen.lift(addr)
        if ins.kind != 'op':
            raise ValueError(f'{addr:#x}: hook patch needs a plain instruction, got {ins.kind}')
        return f'{ins.code} {{ extern uint32_t {fn}(uint32_t); c->x[22] = {fn}((uint32_t)c->x[22]); }}'
    return emit


def _original_then_s0_hook(fn):
    """The original instruction (which must lift to plain C), then s0 = a runtime hook of s0's bits."""
    def emit(gen, addr):
        ins = gen.lift(addr)
        if ins.kind != 'op':
            raise ValueError(f'{addr:#x}: hook patch needs a plain instruction, got {ins.kind}')
        return f'{ins.code} {{ extern uint32_t {fn}(uint32_t); c->v[0] = {fn}((uint32_t)c->v[0]); }}'
    return emit


PATCHES = {
    # 60 / 120 fps: the frame duration getter (f_7001249b08: display period * interval, 0 reads as 2) - what the
    # game's movement and animations step by. Interval 1 is 1/60 s, so at 120 fps they ran twice as fast;
    # runtime/hle/framepace.c xc3_frame_dur scales it to the measured frame time in 60 / 120 fps gameplay.
    0x7001249b60: Patch(0x1e210800, _original_then_s0_hook('xc3_frame_dur'), '120fps',
                        'fmul s0, s0, s1 - frame duration = period * interval'),
    # 120 fps: the frame limiter (f_700124fa34) waits until the frame took display period * interval * 0.997, with
    # interval a whole number (main+0x1B42DB0, 1 = 60 fps). The 0.997 is built in w22 here (movz #0x3b64 + this movk);
    # runtime/hle/framepace.c xc3_limiter_k halves it at 120 fps outside cutscenes.
    0x700124fad0: Patch(0x72a7eff6, _original_then_w22_hook('xc3_limiter_k'), '120fps',
                        'movk w22, #0x3f7f, lsl #16 - frame limiter factor 0.997'),
    # 60 fps: the community cheat's "UI Speed Fix" (github.com/ChanseyIsTheBest/NX-60FPS-RES-GFX-Cheats, build
    # 0AE74B263D8AC3CF; the same code in 2.2.0). In the UI layout update, x21 = the layout: its frame step
    # [x21 + 0x214] stays 1/30 at 60 fps (runtime/hle/framepace.c xc3_ui_step). The cheat branched to a code cave over
    # an import stub instead; here the hook runs before the original `mov x0, x21`.
    0x7000067370: Patch(0xaa1503e0, _hook_x21_then_original('xc3_ui_step'), '60fps',
                        'mov x0, x21 - UI layout update (x21 = layout)'),
}
