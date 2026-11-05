#!/usr/bin/env python3
"""Generates runtime/nvn/vulkan/astc_cs.inc containing the GLSL compute shader for ASTC LDR decoding."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASTC_C = os.path.join(ROOT, "runtime", "nvn", "astc.c")
OUT_INC = os.path.join(ROOT, "runtime", "nvn", "vulkan", "astc_cs.inc")

with open(ASTC_C, "r", encoding="utf-8") as f:
    c = f.read()

w_str = re.sub(r'/\*.*?\*/', '', re.search(r'wunq_data\[\] = \{([^}]+)\};', c, re.DOTALL).group(1))
c_str = re.sub(r'/\*.*?\*/', '', re.search(r'cunq_data\[\] = \{([^}]+)\};', c, re.DOTALL).group(1))
wunq = [int(x.strip()) for x in w_str.split(',') if x.strip()]
cunq = [int(x.strip()) for x in c_str.split(',') if x.strip()]

def pack_u32(arr):
    out = []
    for i in range(0, len(arr), 4):
        chunk = arr[i:i+4]
        while len(chunk) < 4:
            chunk.append(0)
        v = chunk[0] | (chunk[1] << 8) | (chunk[2] << 16) | (chunk[3] << 24)
        out.append(f'0x{v:08X}u')
    return out

w_u32 = pack_u32(wunq)
c_u32 = pack_u32(cunq)

def fmt_array(u32_list, per_line=6):
    lines = []
    for i in range(0, len(u32_list), per_line):
        lines.append('    ' + ', '.join(u32_list[i:i+per_line]))
    return ',\n'.join(lines)

w_tab_code = fmt_array(w_u32)
c_tab_code = fmt_array(c_u32)

glsl_source = f"""#version 450
layout(local_size_x = 64) in;

layout(std430, set = 0, binding = 0) buffer R {{ uint w[]; }};

layout(push_constant) uniform ASTCParams {{
    uint src;
    uint dst;
    uint width;
    uint height;
    uint bw;
    uint bh;
    uint srgb;
    uint num_blocks_x;
    uint total_blocks;
}} p;

const uint q_bits[21]   = uint[](1, 0, 2, 0, 1, 3, 1, 2, 4, 2, 3, 5, 3, 4, 6, 4, 5, 7, 5, 6, 8);
const uint q_trits[21]  = uint[](0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0);
const uint q_quints[21] = uint[](0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0);

const uint wunq_off[12] = uint[](0, 2, 5, 9, 14, 20, 28, 38, 50, 66, 86, 110);
const uint cunq_off[16] = uint[](0, 6, 14, 24, 36, 52, 72, 96, 128, 168, 216, 280, 360, 456, 584, 744);

const uint wunq_tab[36] = uint[](
{w_tab_code}
);

const uint cunq_tab[234] = uint[](
{c_tab_code}
);

uint get_wunq(uint idx) {{
    return (wunq_tab[idx >> 2u] >> ((idx & 3u) * 8u)) & 0xFFu;
}}

uint get_cunq(uint idx) {{
    return (cunq_tab[idx >> 2u] >> ((idx & 3u) * 8u)) & 0xFFu;
}}

uint rbits(uvec4 b, uint pos, uint n) {{
    if (n == 0u || pos >= 128u) return 0u;
    uint word = pos >> 5u;
    uint bit = pos & 31u;
    uint v0 = (word == 0u) ? b.x : (word == 1u) ? b.y : (word == 2u) ? b.z : b.w;
    uint v1 = (word < 3u) ? ((word == 0u) ? b.y : (word == 1u) ? b.z : b.w) : 0u;
    uint val = (bit == 0u) ? v0 : ((v0 >> bit) | (v1 << (32u - bit)));
    uint mask = (n == 32u) ? 0xFFFFFFFFu : ((1u << n) - 1u);
    return val & mask;
}}

uint ise_bitcount(uint count, uint q) {{
    uint n = count * q_bits[q];
    if (q_trits[q] != 0u) n += (8u * count + 4u) / 5u;
    if (q_quints[q] != 0u) n += (7u * count + 2u) / 3u;
    return n;
}}

void trits_of(uint T, out int t[5]) {{
    uint C;
    if (((T >> 2u) & 7u) == 7u) {{
        C = ((T >> 5u) & 7u) << 2u | (T & 3u);
        t[4] = 2; t[3] = 2;
    }} else {{
        C = T & 0x1Fu;
        if (((T >> 5u) & 3u) == 3u) {{ t[4] = 2; t[3] = int((T >> 7u) & 1u); }}
        else {{ t[4] = int((T >> 7u) & 1u); t[3] = int((T >> 5u) & 3u); }}
    }}
    if ((C & 3u) == 3u) {{
        t[2] = 2; t[1] = int((C >> 4u) & 1u);
        t[0] = int(((C >> 3u) & 1u) << 1u | (((C >> 2u) & 1u) & ~((C >> 3u) & 1u) & 1u));
    }} else if (((C >> 2u) & 3u) == 3u) {{
        t[2] = 2; t[1] = 2; t[0] = int(C & 3u);
    }} else {{
        t[2] = int((C >> 4u) & 1u); t[1] = int((C >> 2u) & 3u);
        t[0] = int(((C >> 1u) & 1u) << 1u | ((C & 1u) & ~((C >> 1u) & 1u) & 1u));
    }}
}}

void quints_of(uint Q, out int q[3]) {{
    if (((Q >> 1u) & 3u) == 3u && ((Q >> 5u) & 3u) == 0u) {{
        uint q0 = Q & 1u;
        q[2] = int(q0 << 2u | (((Q >> 4u) & 1u) & ~q0 & 1u) << 1u | (((Q >> 3u) & 1u) & ~q0 & 1u));
        q[1] = 4; q[0] = 4;
        return;
    }}
    uint C = Q & 7u;
    q[2] = int((Q >> 5u) & 3u);
    q[1] = int((Q >> 3u) & 3u);
    if (((Q >> 1u) & 3u) == 3u) {{
        q[2] = 4;
        C = ((Q >> 3u) & 3u) << 1u | (Q & 1u);
        q[1] = int((Q >> 5u) & 3u);
    }}
    if ((C & 3u) == 3u) {{
        q[1] = 4;
        q[0] = int((C >> 2u) & 1u);
    }} else {{
        q[0] = int(C);
    }}
}}

void ise_decode_weights(uvec4 b, uint pos, uint count, uint q, out uint out_w[64]) {{
    uint nb = q_bits[q];
    if (q_trits[q] != 0u) {{
        const uint tb[5] = uint[](2, 2, 1, 1, 1);
        const uint ts[5] = uint[](0, 2, 4, 5, 6);
        for (uint i = 0u; i < count; i += 5u) {{
            uint m[5], T = 0u;
            uint k = 0u;
            int t[5];
            for (; k < 5u && i + k < count; k++) {{
                m[k] = rbits(b, pos, nb); pos += nb;
                T |= rbits(b, pos, tb[k]) << ts[k]; pos += tb[k];
            }}
            trits_of(T, t);
            for (uint j = 0u; j < k; j++) out_w[i + j] = (uint(t[j]) << nb) | m[j];
        }}
    }} else if (q_quints[q] != 0u) {{
        const uint qb[3] = uint[](3, 2, 2);
        const uint qs[3] = uint[](0, 3, 5);
        for (uint i = 0u; i < count; i += 3u) {{
            uint m[3], Q = 0u;
            uint k = 0u;
            int v[3];
            for (; k < 3u && i + k < count; k++) {{
                m[k] = rbits(b, pos, nb); pos += nb;
                Q |= rbits(b, pos, qb[k]) << qs[k]; pos += qb[k];
            }}
            quints_of(Q, v);
            for (uint j = 0u; j < k; j++) out_w[i + j] = (uint(v[j]) << nb) | m[j];
        }}
    }} else {{
        for (uint i = 0u; i < count; i++, pos += nb) out_w[i] = rbits(b, pos, nb);
    }}
}}

void ise_decode_colors(uvec4 b, uint pos, uint count, uint q, out uint out_c[18]) {{
    uint nb = q_bits[q];
    if (q_trits[q] != 0u) {{
        const uint tb[5] = uint[](2, 2, 1, 1, 1);
        const uint ts[5] = uint[](0, 2, 4, 5, 6);
        for (uint i = 0u; i < count; i += 5u) {{
            uint m[5], T = 0u;
            uint k = 0u;
            int t[5];
            for (; k < 5u && i + k < count; k++) {{
                m[k] = rbits(b, pos, nb); pos += nb;
                T |= rbits(b, pos, tb[k]) << ts[k]; pos += tb[k];
            }}
            trits_of(T, t);
            for (uint j = 0u; j < k; j++) out_c[i + j] = (uint(t[j]) << nb) | m[j];
        }}
    }} else if (q_quints[q] != 0u) {{
        const uint qb[3] = uint[](3, 2, 2);
        const uint qs[3] = uint[](0, 3, 5);
        for (uint i = 0u; i < count; i += 3u) {{
            uint m[3], Q = 0u;
            uint k = 0u;
            int v[3];
            for (; k < 3u && i + k < count; k++) {{
                m[k] = rbits(b, pos, nb); pos += nb;
                Q |= rbits(b, pos, qb[k]) << qs[k]; pos += qb[k];
            }}
            quints_of(Q, v);
            for (uint j = 0u; j < k; j++) out_c[i + j] = (uint(v[j]) << nb) | m[j];
        }}
    }} else {{
        for (uint i = 0u; i < count; i++, pos += nb) out_c[i] = rbits(b, pos, nb);
    }}
}}

struct BlockMode {{
    int wx, wy, dual, quant, wbits;
}};

bool block_mode_2d(uint m, uint bw, uint bh, out BlockMode bm) {{
    uint r = (m >> 4u) & 1u;
    uint h = (m >> 9u) & 1u;
    uint d = (m >> 10u) & 1u;
    uint a = (m >> 5u) & 3u;
    int wx, wy;
    if ((m & 3u) != 0u) {{
        r |= (m & 3u) << 1u;
        uint b = (m >> 7u) & 3u;
        uint sel = (m >> 2u) & 3u;
        if (sel == 0u) {{ wx = int(b + 4u); wy = int(a + 2u); }}
        else if (sel == 1u) {{ wx = int(b + 8u); wy = int(a + 2u); }}
        else if (sel == 2u) {{ wx = int(a + 2u); wy = int(b + 8u); }}
        else {{
            b &= 1u;
            if ((m & 0x100u) != 0u) {{ wx = int(b + 2u); wy = int(a + 2u); }}
            else {{ wx = int(a + 2u); wy = int(b + 6u); }}
        }}
    }} else {{
        r |= ((m >> 2u) & 3u) << 1u;
        if (((m >> 2u) & 3u) == 0u) return false;
        uint b = (m >> 9u) & 3u;
        uint sel = (m >> 7u) & 3u;
        if (sel == 0u) {{ wx = 12; wy = int(a + 2u); }}
        else if (sel == 1u) {{ wx = int(a + 2u); wy = 12; }}
        else if (sel == 2u) {{ wx = int(a + 6u); wy = int(b + 6u); d = 0u; h = 0u; }}
        else {{
            if (a == 0u) {{ wx = 6; wy = 10; }}
            else if (a == 1u) {{ wx = 10; wy = 6; }}
            else return false;
        }}
    }}
    int count = wx * wy * int(d + 1u);
    bm.wx = wx; bm.wy = wy; bm.dual = int(d);
    bm.quant = int(r - 2u + 6u * h);
    bm.wbits = int(ise_bitcount(uint(count), uint(bm.quant)));
    return (count <= 64 && bm.wbits >= 24 && bm.wbits <= 96 && wx <= int(bw) && wy <= int(bh));
}}

uint hash52(uint p) {{
    p ^= p >> 15u; p -= p << 17u; p += p << 7u; p += p << 4u;
    p ^= p >> 5u;  p += p << 16u; p ^= p >> 7u; p ^= p >> 3u;
    p ^= p << 6u;  p ^= p >> 17u;
    return p;
}}

struct PartSel {{
    int s[8];
    uint r[4];
    int count;
}};

void part_init(out PartSel ps, int seed, int count) {{
    seed += (count - 1) * 1024;
    uint rnum = hash52(uint(seed));
    int s[8];
    for (int i = 0; i < 8; i++) {{
        int v = int((rnum >> (4u * uint(i))) & 0xFu);
        s[i] = v * v;
    }}
    int sh1, sh2;
    if ((seed & 1) != 0) {{
        sh1 = ((seed & 2) != 0) ? 4 : 5;
        sh2 = (count == 3) ? 6 : 5;
    }} else {{
        sh1 = (count == 3) ? 6 : 5;
        sh2 = ((seed & 2) != 0) ? 4 : 5;
    }}
    for (int i = 0; i < 8; i++) {{
        ps.s[i] = s[i] >> (((i & 1) != 0) ? sh2 : sh1);
    }}
    ps.r[0] = rnum >> 14u;
    ps.r[1] = rnum >> 10u;
    ps.r[2] = rnum >> 6u;
    ps.r[3] = rnum >> 2u;
    ps.count = count;
}}

int part_of(in PartSel ps, int x, int y) {{
    int a = int((uint(ps.s[0] * x + ps.s[1] * y) + ps.r[0]) & 0x3Fu);
    int b = int((uint(ps.s[2] * x + ps.s[3] * y) + ps.r[1]) & 0x3Fu);
    int c = (ps.count >= 3) ? int((uint(ps.s[4] * x + ps.s[5] * y) + ps.r[2]) & 0x3Fu) : 0;
    int d = (ps.count >= 4) ? int((uint(ps.s[6] * x + ps.s[7] * y) + ps.r[3]) & 0x3Fu) : 0;
    if (a >= b && a >= c && a >= d) return 0;
    if (b >= c && b >= d) return 1;
    if (c >= d) return 2;
    return 3;
}}

int clamp255(int v) {{ return clamp(v, 0, 255); }}

bool unpack_endpoints(int cem, uint v[18], uint v_off, out int e0[4], out int e1[4]) {{
    if (cem == 0) {{
        e0[0] = int(v[v_off]); e0[1] = int(v[v_off]); e0[2] = int(v[v_off]);
        e1[0] = int(v[v_off + 1u]); e1[1] = int(v[v_off + 1u]); e1[2] = int(v[v_off + 1u]);
        e0[3] = 255; e1[3] = 255;
        return true;
    }} else if (cem == 1) {{
        int l0 = int((v[v_off] >> 2u) | (v[v_off + 1u] & 0xC0u));
        int l1 = l0 + int(v[v_off + 1u] & 0x3Fu);
        if (l1 > 255) l1 = 255;
        e0[0] = l0; e0[1] = l0; e0[2] = l0;
        e1[0] = l1; e1[1] = l1; e1[2] = l1;
        e0[3] = 255; e1[3] = 255;
        return true;
    }} else if (cem == 4) {{
        e0[0] = int(v[v_off]); e0[1] = int(v[v_off]); e0[2] = int(v[v_off]);
        e1[0] = int(v[v_off + 1u]); e1[1] = int(v[v_off + 1u]); e1[2] = int(v[v_off + 1u]);
        e0[3] = int(v[v_off + 2u]); e1[3] = int(v[v_off + 3u]);
        return true;
    }} else if (cem == 5) {{
        int l0 = int(v[v_off]), l1 = int(v[v_off + 1u]);
        int a0 = int(v[v_off + 2u]), a1 = int(v[v_off + 3u]);
        l0 |= (l1 & 0x80) << 1; a0 |= (a1 & 0x80) << 1;
        l1 &= 0x7F; a1 &= 0x7F;
        if ((l1 & 0x40) != 0) l1 -= 0x80;
        if ((a1 & 0x40) != 0) a1 -= 0x80;
        l0 >>= 1; a0 >>= 1; l1 >>= 1; a1 >>= 1;
        l1 = clamp255(l1 + l0); a1 = clamp255(a1 + a0);
        e0[0] = l0; e0[1] = l0; e0[2] = l0;
        e1[0] = l1; e1[1] = l1; e1[2] = l1;
        e0[3] = a0; e1[3] = a1;
        return true;
    }} else if (cem == 6 || cem == 10) {{
        int s = int(v[v_off + 3u]);
        for (int c = 0; c < 3; c++) {{
            e1[c] = int(v[v_off + uint(c)]);
            e0[c] = (e1[c] * s) >> 8;
        }}
        if (cem == 6) {{ e0[3] = 255; e1[3] = 255; }}
        else {{ e0[3] = int(v[v_off + 4u]); e1[3] = int(v[v_off + 5u]); }}
        return true;
    }} else if (cem == 8 || cem == 12) {{
        int a[4] = int[](int(v[v_off]), int(v[v_off + 2u]), int(v[v_off + 4u]), cem == 12 ? int(v[v_off + 6u]) : 0);
        int b[4] = int[](int(v[v_off + 1u]), int(v[v_off + 3u]), int(v[v_off + 5u]), cem == 12 ? int(v[v_off + 7u]) : 0);
        if (a[0] + a[1] + a[2] > b[0] + b[1] + b[2]) {{
            for (int c = 0; c < 4; c++) {{ e0[c] = b[c]; e1[c] = a[c]; }}
            e0[0] = (e0[0] + e0[2]) >> 1; e0[1] = (e0[1] + e0[2]) >> 1;
            e1[0] = (e1[0] + e1[2]) >> 1; e1[1] = (e1[1] + e1[2]) >> 1;
        }} else {{
            for (int c = 0; c < 4; c++) {{ e0[c] = a[c]; e1[c] = b[c]; }}
        }}
        if (cem == 8) e0[3] = 255;
        return true;
    }} else if (cem == 9 || cem == 13) {{
        int n = (cem == 13) ? 4 : 3;
        int a[4] = int[](0, 0, 0, 0), b[4] = int[](0, 0, 0, 0);
        for (int c = 0; c < n; c++) {{
            int base = int(v[v_off + uint(2 * c)]);
            int delta = int(v[v_off + uint(2 * c + 1)]);
            a[c] = (base >> 1) | (delta & 0x80);
            b[c] = (delta >> 1) & 0x3F;
            if ((b[c] & 0x20) != 0) b[c] -= 0x40;
        }}
        int sum = b[0] + b[1] + b[2];
        for (int c = 0; c < 4; c++) b[c] += a[c];
        if (sum < 0) {{
            for (int c = 0; c < 4; c++) {{ e0[c] = b[c]; e1[c] = a[c]; }}
            e0[0] = (e0[0] + e0[2]) >> 1; e0[1] = (e0[1] + e0[2]) >> 1;
            e1[0] = (e1[0] + e1[2]) >> 1; e1[1] = (e1[1] + e1[2]) >> 1;
        }} else {{
            for (int c = 0; c < 4; c++) {{ e0[c] = a[c]; e1[c] = b[c]; }}
        }}
        for (int c = 0; c < 4; c++) {{ e0[c] = clamp255(e0[c]); e1[c] = clamp255(e1[c]); }}
        if (cem == 9) e0[3] = 255;
        return true;
    }}
    return false;
}}

void main() {{
    uint bi = gl_GlobalInvocationID.x;
    if (bi >= p.total_blocks) return;

    uint bx = bi % p.num_blocks_x;
    uint by = bi / p.num_blocks_x;

    uint b_off = p.src + bi * 4u;
    uvec4 b = uvec4(w[b_off], w[b_off + 1u], w[b_off + 2u], w[b_off + 3u]);

    uint mode = b.x & 0x7FFu;
    if ((mode & 0x1FFu) == 0x1FCu) {{
        if ((mode & 0x200u) != 0u || ((b.x >> 10u) & 3u) != 3u) {{
            for (uint y = 0u; y < p.bh; y++) {{
                uint py = by * p.bh + y;
                if (py >= p.height) continue;
                for (uint x = 0u; x < p.bw; x++) {{
                    uint px = bx * p.bw + x;
                    if (px < p.width) w[p.dst + py * p.width + px] = 0xFFFF00FFu;
                }}
            }}
            return;
        }}
        uint s0 = rbits(b, 12u, 13u), s1 = rbits(b, 25u, 13u);
        uint t0 = rbits(b, 38u, 13u), t1 = rbits(b, 51u, 13u);
        bool all_ones = (s0 == 0x1FFFu && s1 == 0x1FFFu && t0 == 0x1FFFu && t1 == 0x1FFFu);
        if ((s0 >= s1 || t0 >= t1) && !all_ones) {{
            for (uint y = 0u; y < p.bh; y++) {{
                uint py = by * p.bh + y;
                if (py >= p.height) continue;
                for (uint x = 0u; x < p.bw; x++) {{
                    uint px = bx * p.bw + x;
                    if (px < p.width) w[p.dst + py * p.width + px] = 0xFFFF00FFu;
                }}
            }}
            return;
        }}
        uint c0 = (b.z >> 8u) & 0xFFu;
        uint c1 = (b.z >> 24u) & 0xFFu;
        uint c2 = (b.w >> 8u) & 0xFFu;
        uint c3 = (b.w >> 24u) & 0xFFu;
        uint const_color = c0 | (c1 << 8u) | (c2 << 16u) | (c3 << 24u);
        for (uint y = 0u; y < p.bh; y++) {{
            uint py = by * p.bh + y;
            if (py >= p.height) continue;
            for (uint x = 0u; x < p.bw; x++) {{
                uint px = bx * p.bw + x;
                if (px < p.width) w[p.dst + py * p.width + px] = const_color;
            }}
        }}
        return;
    }}

    BlockMode bm;
    if (!block_mode_2d(mode, p.bw, p.bh, bm)) {{
        for (uint y = 0u; y < p.bh; y++) {{
            uint py = by * p.bh + y;
            if (py >= p.height) continue;
            for (uint x = 0u; x < p.bw; x++) {{
                uint px = bx * p.bw + x;
                if (px < p.width) w[p.dst + py * p.width + px] = 0xFFFF00FFu;
            }}
        }}
        return;
    }}

    int pcount = int((b.x >> 11u) & 3u) + 1;
    int wcount = bm.wx * bm.wy;
    if (bm.dual != 0 && pcount == 4) {{
        for (uint y = 0u; y < p.bh; y++) {{
            uint py = by * p.bh + y;
            if (py >= p.height) continue;
            for (uint x = 0u; x < p.bw; x++) {{
                uint px = bx * p.bw + x;
                if (px < p.width) w[p.dst + py * p.width + px] = 0xFFFF00FFu;
            }}
        }}
        return;
    }}

    uint raw_w[64];
    uvec4 rev = uvec4(bitfieldReverse(b.w), bitfieldReverse(b.z), bitfieldReverse(b.y), bitfieldReverse(b.x));
    ise_decode_weights(rev, 0u, uint(wcount << bm.dual), uint(bm.quant), raw_w);

    uint w_base = wunq_off[bm.quant];
    uint grid[160];
    for (int i = 0; i < 160; i++) grid[i] = 0u;
    if (bm.dual != 0) {{
        for (int i = 0; i < wcount; i++) {{
            grid[i] = get_wunq(w_base + raw_w[2 * i]);
            grid[80 + i] = get_wunq(w_base + raw_w[2 * i + 1]);
        }}
    }} else {{
        for (int i = 0; i < wcount; i++) {{
            grid[i] = get_wunq(w_base + raw_w[i]);
        }}
    }}

    int cem[4];
    int below = 128 - bm.wbits;
    int high = 0;
    if (pcount == 1) {{
        cem[0] = int((b.x >> 13u) & 0xFu);
    }} else {{
        high = 3 * pcount - 4;
        below -= high;
        uint enc = ((b.x >> 23u) & 0x3Fu) | (rbits(b, uint(below), uint(high)) << 6u);
        uint base = enc & 3u;
        if (base == 0u) {{
            for (int i = 0; i < pcount; i++) cem[i] = int((enc >> 2u) & 0xFu);
            below += high;
            high = 0;
        }} else {{
            base--;
            for (int i = 0; i < pcount; i++) cem[i] = int((((enc >> (2 + i)) & 1u) + base) << 2u);
            for (int i = 0; i < pcount; i++) cem[i] |= int((enc >> (2 + pcount + 2 * i)) & 3u);
        }}
    }}

    int ccount = 0;
    for (int i = 0; i < pcount; i++) ccount += ((cem[i] >> 2) + 1) * 2;
    if (ccount > 18) {{
        for (uint y = 0u; y < p.bh; y++) {{
            uint py = by * p.bh + y;
            if (py >= p.height) continue;
            for (uint x = 0u; x < p.bw; x++) {{
                uint px = bx * p.bw + x;
                if (px < p.width) w[p.dst + py * p.width + px] = 0xFFFF00FFu;
            }}
        }}
        return;
    }}

    int cbits = (pcount == 1 ? 111 : 99) - bm.wbits - high - (bm.dual != 0 ? 2 : 0);
    if (cbits < 0) cbits = 0;
    int cq = -1;
    for (int q = 20; q >= 0; q--) {{
        if (int(ise_bitcount(uint(ccount), uint(q))) <= cbits) {{ cq = q; break; }}
    }}
    if (cq < 4) {{
        for (uint y = 0u; y < p.bh; y++) {{
            uint py = by * p.bh + y;
            if (py >= p.height) continue;
            for (uint x = 0u; x < p.bw; x++) {{
                uint px = bx * p.bw + x;
                if (px < p.width) w[p.dst + py * p.width + px] = 0xFFFF00FFu;
            }}
        }}
        return;
    }}

    uint cv[18];
    ise_decode_colors(b, pcount == 1 ? 17u : 29u, uint(ccount), uint(cq), cv);
    if (cq != 20) {{
        uint c_base = cunq_off[cq - 4];
        for (int i = 0; i < ccount; i++) cv[i] = get_cunq(c_base + cv[i]);
    }}

    int ccs = (bm.dual != 0) ? int(rbits(b, uint(below - 2), 2u)) : -1;

    int ep[32];
    uint k_off = 0u;
    for (int p_idx = 0; p_idx < pcount; p_idx++) {{
        int e0[4], e1[4];
        if (!unpack_endpoints(cem[p_idx], cv, k_off, e0, e1)) {{
            e0[0] = 0xFF; e0[1] = 0x00; e0[2] = 0xFF; e0[3] = 0xFF;
            e1[0] = 0xFF; e1[1] = 0x00; e1[2] = 0xFF; e1[3] = 0xFF;
        }}
        k_off += uint(((cem[p_idx] >> 2) + 1) * 2);
        for (int c = 0; c < 4; c++) {{
            int v0 = (p.srgb != 0u) ? ((e0[c] << 8) | 0x80) : (e0[c] * 257);
            int v1 = (p.srgb != 0u) ? ((e1[c] << 8) | 0x80) : (e1[c] * 257);
            ep[p_idx * 8 + 0 * 4 + c] = v0;
            ep[p_idx * 8 + 1 * 4 + c] = v1;
        }}
    }}

    int xi[12], xf[12], yi[12], yf[12];
    for (uint x = 0u; x < p.bw; x++) {{
        int v = int((((1024u + p.bw / 2u) / (p.bw - 1u)) * x * uint(bm.wx - 1) + 32u) >> 6u);
        xi[x] = v >> 4; xf[x] = v & 0xF;
    }}
    for (uint y = 0u; y < p.bh; y++) {{
        int v = int((((1024u + p.bh / 2u) / (p.bh - 1u)) * y * uint(bm.wy - 1) + 32u) >> 6u);
        yi[y] = (v >> 4) * bm.wx; yf[y] = v & 0xF;
    }}

    PartSel ps;
    if (pcount > 1) part_init(ps, int((b.x >> 13u) & 0x3FFu), pcount);
    bool small_tex = (p.bw * p.bh < 32u);

    for (uint y = 0u; y < p.bh; y++) {{
        uint py = by * p.bh + y;
        if (py >= p.height) continue;
        for (uint x = 0u; x < p.bw; x++) {{
            uint px = bx * p.bw + x;
            if (px >= p.width) continue;

            int fs = xf[x], ft = yf[y];
            int w11 = (fs * ft + 8) >> 4;
            int w10 = fs - w11;
            int w01 = ft - w11;
            int w00 = 16 - fs - ft + w11;
            int i0 = yi[y] + xi[x];

            int w_res[2];
            for (int pl = 0; pl <= bm.dual; pl++) {{
                uint g_off = uint(pl * 80);
                uint g00 = grid[g_off + uint(i0)];
                uint g10 = grid[g_off + uint(i0 + 1)];
                uint g01 = grid[g_off + uint(i0 + bm.wx)];
                uint g11 = grid[g_off + uint(i0 + bm.wx + 1)];
                w_res[pl] = int((g00 * uint(w00) + g10 * uint(w10) + g01 * uint(w01) + g11 * uint(w11) + 8u) >> 4u);
            }}

            int p_sel = (pcount > 1) ? part_of(ps, small_tex ? int(x << 1u) : int(x), small_tex ? int(y << 1u) : int(y)) : 0;
            int ep_base = p_sel * 8;

            uint out_rgba = 0u;
            for (int c = 0; c < 4; c++) {{
                int wc = (c == ccs) ? w_res[1] : w_res[0];
                int e0_val = ep[ep_base + 0 * 4 + c];
                int e1_val = ep[ep_base + 1 * 4 + c];
                int chan = (e0_val * (64 - wc) + e1_val * wc + 32) >> 14;
                out_rgba |= (uint(clamp255(chan)) << uint(c * 8));
            }}
            w[p.dst + py * p.width + px] = out_rgba;
        }}
    }}
}}
"""

# Format as C raw string literal or escaped string
c_code = '// Auto-generated by tools/gen_astc_cs.py - do not edit\n'
c_code += '#ifndef ASTC_CS_INC\n#define ASTC_CS_INC\n\n'
c_code += 'static const char astc_glsl[] =\n'
for line in glsl_source.strip().split('\n'):
    escaped = line.replace('\\', '\\\\').replace('"', '\\"')
    c_code += f'    "{escaped}\\n"\n'
c_code += ';\n\n#endif // ASTC_CS_INC\n'

with open(OUT_INC, 'w', encoding='utf-8') as f:
    f.write(c_code)

print(f"Generated {OUT_INC} ({len(c_code)} bytes)")
