// [XC3] VMNMX (video min / max): d = op(mx ? max(A, B) : min(A, B), C), op MIN / MAX (yuzu shader_recompiler
// video_minimum_maximum.cpp). XC3's lighting shaders (shd_lgt.wishp) failed to translate on it and characters were drawn
// black. The three forms below are words from those shaders; the merge op and .SAT must fail, not be guessed.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../../runtime/nvn/maxwell/shader.h"

ShaderInfo *maxwell_translate(const uint8_t *blob, size_t max_size, size_t const_size, int stage, const ShaderKey *key);
void maxwell_free(ShaderInfo *s);

static int fails;
#define CHECK(cond) do { if (!(cond)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); fails++; } } while (0)

#define EXIT_W 0xe30000000007000full
#define NOP_W 0x50b0000000070f00ull

static ShaderInfo *translate(uint64_t instr) {
    uint8_t blob[0x80 + 8 * 16];
    memset(blob, 0, sizeof blob);
    uint64_t *code = (uint64_t *)(blob + 0x80);
    code[0] = 0; code[1] = instr; code[2] = EXIT_W; code[3] = NOP_W;
    ShaderKey key; memset(&key, 0, sizeof key);
    key.glsl = 1;
    return maxwell_translate(blob, sizeof blob, 0, STAGE_FRAGMENT, &key);
}

// the statement that assigns register r (the last one in the program)
static const char *assign_of(const char *src, int r, char *out, size_t n) {
    char pat[16];
    snprintf(pat, sizeof pat, " r%d = ", r);
    const char *p = NULL, *q = src;
    while ((q = strstr(q, pat))) p = q++;
    if (!p) return NULL;
    const char *e = strchr(p, ';');
    size_t len = e ? (size_t)(e - p) : strlen(p);
    if (len >= n) len = n - 1;
    memcpy(out, p, len);
    out[len] = 0;
    return out;
}

// instr assigns register d an expression containing want (in order: the outer op, then the inner one)
static void expect(uint64_t instr, int d, const char *outer, const char *inner) {
    ShaderInfo *s = translate(instr);
    CHECK(s && s->msl);
    if (s && s->msl) {
        char a[1024];
        const char *st = assign_of(s->msl, d, a, sizeof a);
        CHECK(st != NULL);
        if (st) {
            const char *o = strstr(st, outer), *i = o ? strstr(o + strlen(outer), inner) : NULL;
            CHECK(o && i);
            if (!o || !i) printf("  %016llx: %s\n", (unsigned long long)instr, st);
        }
    } else if (s) printf("  %016llx: %s\n", (unsigned long long)instr, s->error);
    if (s) maxwell_free(s);
}

static void expect_fail(uint64_t instr) {
    ShaderInfo *s = translate(instr);
    CHECK(s && !s->msl && strstr(s->error, "vmnmx"));
    if (s && s->msl) printf("  %016llx translated, expected a failure\n", (unsigned long long)instr);
    if (s) maxwell_free(s);
}

int main(void) {
    // d4 = max(min(r6, r7), r8): mx 0, op MAX, unsigned whole registers (shd_lgt.wishp)
    expect(0x3a34046060770604ull, 4, "max(min(", "r6, r7), r8)");
    // d10 = min(min(r10, r11), r5): op MIN
    expect(0x3a2c02e060b70a0aull, 10, "min(min(", "r10, r11), r5)");
    // d3 = max(max(r11, r12), r13): mx 1
    expect(0x3b3406e060c70b03ull, 3, "max(max(", "r11, r12), r13)");
    // signed (B sign bit 49, result sign bit 54): compared as int
    expect(0x3a34046060770604ull | (1ull << 49) | (1ull << 54), 4, "uint(max(int(uint(min(int(", "r6), int(r7)))), int(r8)))");
    // the merge op (0) and .SAT: not implemented, so not translated
    expect_fail(0x3a34046060770604ull & ~(7ull << 51));
    expect_fail(0x3a34046060770604ull | (1ull << 55));
    printf(fails ? "test_translate_vmnmx: %d failures\n" : "test_translate_vmnmx: OK\n", fails);
    return fails != 0;
}
