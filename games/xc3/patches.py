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


def _hook_cpu_then_original(fn):  # (fn(Cpu *) runs, then the original instruction)
    def emit(gen, addr):
        ins = gen.lift(addr)
        if ins.kind != 'op':
            raise ValueError(f'{addr:#x}: hook patch needs a plain instruction, got {ins.kind}')
        return f'{{ extern void {fn}(void *); {fn}(c); }} {ins.code}'
    return emit


PATCHES = {
    # XC3 tour (runtime/hle/party.c xc3_tour): f_7000d31ec0(manager, task) registers a task; the map change task's
    # manager (it lives in an object, +0x60 - no global) is remembered from here. Before `mov x29, sp`
    0x7000d31ec8: Patch(0x910003fd, _hook_cpu_then_original('xc3_jump_mgr_seen'), 'tour', 'XC3 tour: map change manager'),
    # 60 fps: the community cheat's "UI Speed Fix" (github.com/ChanseyIsTheBest/NX-60FPS-RES-GFX-Cheats, build
    # 0AE74B263D8AC3CF; the same code in 2.2.0). In the UI layout update, x21 = the layout: its frame step
    # [x21 + 0x214] stays 1/30 at 60 fps (runtime/hle/framepace.c xc3_ui_step). The cheat branched to a code cave over
    # an import stub instead; here the hook runs before the original `mov x0, x21`.
    0x7000067370: Patch(0xaa1503e0, _hook_x21_then_original('xc3_ui_step'), '60fps',
                        'mov x0, x21 - UI layout update (x21 = layout)'),
}
