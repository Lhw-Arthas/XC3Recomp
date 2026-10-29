// [XC3] TLD4S with AOFFI (texture gather with a register offset; a post effect of XC3's shd_post.wishp failed to
// translate on it) and TLD4's AOFFI offset: coordinates in Ra / Ra+1, the offset in Rb as signed 6-bit x / y at bits
// 0 / 8 (yuzu shader_recompiler texture_gather*.cpp). The depth-compare TLD4S form must still fail, not be guessed.
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

// the program translates and its source holds every one of the given pieces
static void expect(uint64_t instr, const char *const *pieces) {
    ShaderInfo *s = translate(instr);
    CHECK(s && s->msl);
    if (s && s->msl) {
        for (int i = 0; pieces[i]; i++) {
            bool has = strstr(s->msl, pieces[i]) != NULL;
            CHECK(has);
            if (!has) printf("  %016llx: no \"%s\"\n", (unsigned long long)instr, pieces[i]);
        }
    } else if (s) printf("  %016llx: %s\n", (unsigned long long)instr, s->error);
    if (s) maxwell_free(s);
}

int main(void) {
    // TLD4S.AOFFI R26, R30, R8, R26 (shd_post.wishp): coordinates r8 / r9, offset from r26 (6-bit fields)
    static const char *const p1[] = {"textureGather(", "as_f(r8)", "as_f(r9)", "r26 << 26) >> 26",
                                     "r26 << 18) >> 26", "tsize", NULL};
    expect(0xdf0a00a1e1a7081aull, p1);
    static const char *const p2[] = {"textureGather(", "as_f(r8)", "as_f(r9)", "r35 << 26) >> 26", NULL};
    expect(0xdf0a00a102370818ull, p2);
    static const char *const p3[] = {"textureGather(", "r18 << 26) >> 26", "r18 << 18) >> 26", NULL};
    expect(0xdf0a00a121270814ull, p3);
    static const char *const p4[] = {"textureGather(", "r10 << 26) >> 26", NULL};
    expect(0xdf0a00a0a0a7080cull, p4);
    // without AOFFI: coordinates r8 / r9 (Ra / Rb), as before
    static const char *const p5[] = {"textureGather(", "as_f(r8)", "as_f(r9)", NULL};
    expect(0xdf0200a16097080eull, p5);
    // the depth-compare form: not translated
    ShaderInfo *s = translate(0xdf0a00a1e1a7081aull | (1ull << 50));
    CHECK(s && !s->msl && strstr(s->error, "tld4s dc"));
    if (s) maxwell_free(s);
    printf(fails ? "test_translate_tld4: %d failures\n" : "test_translate_tld4: OK\n", fails);
    return fails != 0;
}
