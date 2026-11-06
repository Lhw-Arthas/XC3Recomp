// Frame pacing for XC3's FPS option (30 / 60): the community 60 FPS cheat's writes each presented frame (xc3_fps_frame),
// cutscenes held at 30, and the UI layout's frame step. XCDE's frame limiter hooks, its frame-step timer and the T224
// memory research tools (XCDE_MEMWATCH / _STATESNAP / _DELTAFIND / _FLOATFIND / _FPOKE / _FTRACE / _FVALFIND) were
// tied to XCDE's patches and were removed with the XCDE profile.
#include <math.h>
#include <stdlib.h>
#include <string.h>

#include "../diag/diag.h"
#include "../hle.h"
#include "../platform.h"
#include "../settings.h"

// The option (launcher "Cutscenes") holds a cutscene at 30 fps: the game's poses there change at 30, and with the
// camera at 60 over them the motion looks uneven (the user: cutscenes feel like 30, Dickson's ponytail shakes).
// cutscenes = 30fg (launcher "Frame generation in cutscenes only"): the same, plus frame generation only there -
// gameplay keeps its FPS without it (the user plays locked at 60; generated frames there would look laggy).
static bool g_cut30;
bool xcde_cutscene_30(void) { return g_cut30; }
// the frame rate the window is presented at (device.c repeat presents): 30 while a cutscene is held at 30
int xcde_present_fps(void) { return g_cut30 ? 30 : g_settings.fps; }

// [XC3] 60 fps (FPS option 60): what the community cheat "60 FPS Gameplay + 30 FPS Cutscene + UI Speed Fix"
// (github.com/ChanseyIsTheBest/NX-60FPS-RES-GFX-Cheats, build 0AE74B263D8AC3CF) writes. Its addresses hold the same
// things in 2.2.0 (82D187FE9EF9BE92), read in a running game on 2026-10-29: main+0x1B42DB0 the frame interval (two
// u32, 2 = 30 fps), *(main+0x1BA1A90) + 0x80 the frame time the game steps its world by (1/30), main+0x1BA1A98 a
// cutscene flag (1 in a cutscene). Outside cutscenes interval 1 and 1/60; in cutscenes the game's 2 and 1/30 (held at
// 30 fps, presented at 30 - xcde_present_fps). Written each presented frame (device.c), as the cheat engine does.
// Above 60: not supported by these (the option is 30 / 60 for XC3).
static bool xc3_60;  // (this frame: 60 fps gameplay - xc3_ui_step)
void xc3_fps_frame(void) {
    static int on = -1;
    if (on < 0) on = g_settings.fps != 30 && !ENV("XC3_FPS_OFF");
    if (!on) return;
    volatile uint32_t *iv = (volatile uint32_t *)(uintptr_t)0x7001B42DB0ull;
    volatile uint8_t *cut = (volatile uint8_t *)(uintptr_t)0x7001BA1A98ull;
    uint64_t ft = *(volatile uint64_t *)(uintptr_t)0x7001BA1A90ull;
    if (ft < GUEST_LO || ft >= HEAP_BASE + HEAP_MAX) return;  // (not made yet: boot)
    volatile float *step = (volatile float *)(uintptr_t)(ft + 0x80);
    bool in_cut = *cut != 0;
    xc3_60 = !in_cut;
    g_cut30 = in_cut;
    iv[0] = iv[1] = in_cut ? 2 : 1;
    // the world steps by this each frame: the cheat writes 1/60, which is slow motion when a frame takes longer (40 fps:
    // 0.67x). The measured frame time instead (average of the last 8 presents, 1/60 .. 1/30): the world keeps its
    // speed between 30 and 60 fps. XC3_FPS_FIXED_STEP=1: the cheat's fixed 1/60.
    static uint64_t last, hist[8];
    static int nh, fixed = -1;
    if (fixed < 0) fixed = ENV("XC3_FPS_FIXED_STEP") != NULL || diag_deterministic();
    uint64_t now = plat_now_ns();
    if (last && now - last < 200000000ull) hist[nh++ % 8] = now - last;  // (a stall: not a frame time)
    last = now;
    float dt = 1.0f / 60.0f;
    if (!fixed && nh >= 8) {
        uint64_t s = 0;
        for (int i = 0; i < 8; i++) s += hist[i];
        dt = (float)(s / 8) * 1e-9f;
        dt = dt < 1.0f / 60.0f ? 1.0f / 60.0f : dt > 1.0f / 30.0f ? 1.0f / 30.0f : dt;
    }
    *step = in_cut ? 1.0f / 30.0f : dt;
    {   // XC3_FPS_LOG=1: the step written, every 300 presents
        static int lg = -1;
        static uint64_t n;
        if (lg < 0) lg = ENV("XC3_FPS_LOG") != NULL;
        if (lg && ++n % 300 == 0) LOG("[fps] XC3 step %.2f ms (%s), interval %u\n", *step * 1e3, in_cut ? "cutscene" : "gameplay", iv[0]);
    }
    static int logged;
    if (!logged) { logged = 1; LOG("[fps] XC3 60 fps: interval and frame time written (cutscenes at 30)\n"); }
}
// [XC3] the cheat's "UI Speed Fix" (games/xc3/patches.py, main+0x67370): at 60 fps the UI layout's frame step
// ([layout + 0x214]) stays 1/30 - its 2D animations otherwise ran twice as fast
void xc3_ui_step(uint64_t layout) {
    if (xc3_60 && layout) *(volatile float *)(uintptr_t)(layout + 0x214) = 1.0f / 30.0f;
}
