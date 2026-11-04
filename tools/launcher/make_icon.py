"""[XC3] Draws the launcher's icon (tools/launcher/icon.ico): our own generic emblem - a cyan ring and a diagonal
blade of light on a dark rounded tile, in the launcher's palette. No game art. Pure Python (zlib only): each size is
rendered with 4x4 supersampling and stored as a PNG inside the ICO.
    python tools/launcher/make_icon.py        (then tools/launcher/build.sh links it into the exe)
"""
import math
import os
import struct
import zlib

SIZES = (16, 24, 32, 48, 64, 128, 256)
SS = 4


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(4))


def over(dst, src):  # premultiplied-free "src over dst", rgba floats 0..1
    a = src[3] + dst[3] * (1 - src[3])
    if a <= 0:
        return (0, 0, 0, 0)
    return tuple((src[i] * src[3] + dst[i] * dst[3] * (1 - src[3])) / a for i in range(3)) + (a,)


def sample(x, y):
    """Colour at (x, y) in [-1, 1]^2, y down."""
    # rounded tile (superellipse), dark navy, lighter at the top
    se = abs(x) ** 5 + abs(y) ** 5
    if se > 0.92 ** 5:
        return (0, 0, 0, 0)
    edge = min(1.0, (0.92 ** 5 - se) * 40)  # (soft rim)
    c = mix((0.07, 0.12, 0.24, 1), (0.02, 0.04, 0.10, 1), (y + 1) / 2)
    c = (c[0], c[1], c[2], edge)
    r = math.hypot(x, y)
    # glow behind the ring
    g = math.exp(-((r - 0.56) / 0.16) ** 2) * 0.35
    c = over(c, (0.25, 0.83, 0.96, g * edge))
    # the ring
    ring = 1.0 - min(1.0, abs(r - 0.56) / 0.06)
    if ring > 0:
        c = over(c, (0.30, 0.86, 0.98, min(1.0, ring * 2.2) * edge))
    # a diagonal blade of light (a long thin diamond), rotated 35 degrees
    a = math.radians(35)
    u = x * math.cos(a) + y * math.sin(a)
    v = -x * math.sin(a) + y * math.cos(a)
    half = 0.80
    if abs(v) < half:
        w = 0.085 * (1 - abs(v) / half) ** 0.8
        d = abs(u)
        if d < w * 2.2:
            core = 1.0 - min(1.0, d / max(w, 1e-4))
            halo = math.exp(-(d / max(w * 1.4, 1e-4)) ** 2) * 0.5
            col = mix((0.40, 0.88, 1.0, 1), (0.92, 0.98, 1.0, 1), core)
            c = over(c, (col[0], col[1], col[2], min(1.0, max(core * 1.8, halo)) * edge))
    # a spark at the centre
    s = math.exp(-(r / 0.07) ** 2)
    c = over(c, (1, 1, 1, s * 0.9 * edge))
    return c


def render(n):
    rows = []
    for py in range(n):
        row = bytearray(b'\0')
        for px in range(n):
            acc = [0.0, 0.0, 0.0, 0.0]
            for sy in range(SS):
                for sx in range(SS):
                    x = ((px + (sx + 0.5) / SS) / n) * 2 - 1
                    y = ((py + (sy + 0.5) / SS) / n) * 2 - 1
                    c = sample(x, y)
                    for i in range(3):
                        acc[i] += c[i] * c[3]
                    acc[3] += c[3]
            a = acc[3] / (SS * SS)
            rgb = [acc[i] / acc[3] if acc[3] > 0 else 0 for i in range(3)]
            row += bytes(int(max(0, min(1, v)) * 255 + 0.5) for v in rgb + [a])
        rows.append(bytes(row))
    raw = b''.join(rows)

    def chunk(t, c):
        return struct.pack('>I', len(c)) + t + c + struct.pack('>I', zlib.crc32(t + c) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', n, n, 8, 6, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    pngs = [render(n) for n in SIZES]
    head = struct.pack('<HHH', 0, 1, len(SIZES))
    off = 6 + 16 * len(SIZES)
    dirs, data = b'', b''
    for n, p in zip(SIZES, pngs):
        dirs += struct.pack('<BBBBHHII', n % 256, n % 256, 0, 0, 1, 32, len(p), off + len(data))
        data += p
    with open(os.path.join(here, 'icon.ico'), 'wb') as f:
        f.write(head + dirs + data)
    prev = os.path.join(here, '..', '..', 'build', 'launcher')
    os.makedirs(prev, exist_ok=True)
    with open(os.path.join(prev, 'icon_256.png'), 'wb') as f:  # (a preview, not committed)
        f.write(pngs[-1])
    print('icon.ico:', ', '.join(map(str, SIZES)))


if __name__ == '__main__':
    main()
