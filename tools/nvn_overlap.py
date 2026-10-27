"""[XC3] Find NVN structs the HLE writes past the end of, in a game's main module.

Usage: nvn_overlap.py [--exefs targets/exefs] [--json out.json]

1. Maps the game's NVN proc-pointer slots to names: main's loader resolves every nvnXxx by name (the strings are in its
   rodata) and stores the result through a GOT slot; draws call `adrp; ldr [slot]; ldr; blr`.
2. For every call of a function of struct type T with x0 = base + imm, looks for game accesses to [base, #o] with
   imm < o < imm + size(T) in the same function (base-register adds tracked, scan stops where base is redefined):
   the game keeps its own data inside the bytes the HLE assumes are T's.

The sizes below are what the runtime writes into the game's struct (runtime/nvn/objects.c, nvn.h GuestTextureView /
GuestSamplerDesc for XC3). A hit is a candidate to check by hand: a stack slot the compiler reused for another local
before the struct's SetDefaults is a false positive (seen for BufferBuilder). No hit is not proof of a size.
"""
import argparse
import collections
import json
import os
import re
import sys

import capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'lifter'))
from nso import Nso  # noqa: E402

B = 0x7000000000
RT = {'TextureView': 0x10, 'TextureBuilder': 0x60, 'SamplerBuilder': 0x30, 'BufferBuilder': 0x20,
      'MemoryPoolBuilder': 0x20, 'Buffer': 0x28, 'WindowBuilder': 0x28, 'QueueBuilder': 0x30, 'MultisampleState': 0x18,
      'Event': 0x18, 'EventBuilder': 0x10, 'BlendState': 8, 'VertexStreamState': 8, 'Texture': 8, 'Sampler': 8,
      'MemoryPool': 8, 'Sync': 8, 'Program': 8}
MEM = re.compile(r'\[(x\d+|sp), #(-?0x[0-9a-f]+)\]')
NAME = re.compile(rb'nvn[A-Z][A-Za-z0-9]+')


def disasm(n):
    md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
    md.skipdata = True
    off, size = n.text
    return list(md.disasm(bytes(n.image[off:off + size]), B + off))


def map_slots(n, ins):
    img = bytes(n.image)

    def cstr(a):
        o = a - B
        if not 0 <= o < len(img):
            return None
        s = img[o:img.find(b'\0', o)]
        return s.decode() if NAME.fullmatch(s) else None

    pages, slots = {}, {}
    for k, i in enumerate(ins):
        if i.mnemonic == 'adrp':
            r, v = i.op_str.split(', #')
            pages[r] = int(v, 16)
            continue
        p = i.op_str.split(', ')
        if i.mnemonic != 'add' or len(p) != 3 or p[1] not in pages or not p[2].startswith('#'):
            continue
        name = cstr(pages[p[1]] + int(p[2][1:], 16))
        if not name:
            continue
        pg = {}
        for j in range(k + 1, min(k + 14, len(ins))):  # adrp/ldr the slot, then str x0 through it
            q = ins[j]
            if q.mnemonic == 'adrp':
                r, v = q.op_str.split(', #')
                pg[r] = int(v, 16)
            elif q.mnemonic == 'ldr':
                m = re.match(r'(x\d+), \[(x\d+), #(0x[0-9a-f]+)\]', q.op_str)
                if m and m.group(2) in pg and j + 1 < len(ins) and \
                        ins[j + 1].mnemonic == 'str' and ins[j + 1].op_str.startswith('x0, [' + m.group(1) + ']'):
                    slots[pg[m.group(2)] + int(m.group(3), 16)] = name
                    break
    return slots


def type_of(name):
    for t in sorted(RT, key=len, reverse=True):
        if name.startswith('nvn' + t) and not name.startswith('nvn' + t + 'Pool'):
            return t
    return None


def scan(ins, slots):
    hits, calls = collections.defaultdict(list), collections.Counter()
    for k, i in enumerate(ins):
        if i.mnemonic != 'blr':
            continue
        slot, pg = None, {}
        for j in range(max(0, k - 12), k):
            q = ins[j]
            if q.mnemonic == 'adrp':
                r, v = q.op_str.split(', #')
                pg[r] = int(v, 16)
            elif q.mnemonic == 'ldr':
                m = MEM.search(q.op_str)
                if m and m.group(1) in pg:
                    slot = pg[m.group(1)] + int(m.group(2), 16)
        name = slots.get(slot)
        t = type_of(name) if name else None
        if not t:
            continue
        base = imm = defpos = None
        for j in range(k - 1, max(0, k - 16), -1):  # x0 = base + imm, the closest definition
            q = ins[j]
            p = q.op_str.split(', ')
            if p[0] != 'x0':
                continue
            if q.mnemonic == 'add' and len(p) == 3 and p[2].startswith('#'):
                base, imm = p[1], int(p[2][1:], 16)
            elif q.mnemonic == 'mov' and len(p) == 2 and re.fullmatch(r'x\d+|sp', p[1]):
                base, imm = p[1], 0
            defpos = j
            break
        if base in (None, 'x0', 'x29'):
            continue
        calls[t] += 1
        size = RT[t]

        def redefines(q):
            if q.mnemonic.startswith(('str', 'stp', 'stur', 'cmp', 'cmn', 'tst', 'b', 'cb', 'tb', 'ret')):
                return False
            ds = q.op_str.split(', ')
            return base in ds[:2] if q.mnemonic in ('ldp', 'ldnp') else ds[0] == base

        def walk(rng, back):
            rel = imm  # struct start relative to the base register's value at q
            for j in rng:
                q = ins[j]
                if q.mnemonic == 'ret' or (q.mnemonic == 'stp' and q.op_str.startswith('x29, x30') and '!' in q.op_str):
                    return
                p = q.op_str.split(', ')
                if q.mnemonic in ('add', 'sub') and len(p) == 3 and p[0] == base == p[1] and p[2].startswith('#'):
                    c = int(p[2][1:], 16) * (1 if q.mnemonic == 'add' else -1)
                    rel = rel + c if back else rel - c
                    continue
                if q.mnemonic in ('str', 'stp', 'stur', 'strb', 'strh', 'ldr', 'ldp', 'ldur', 'ldrb', 'ldrh'):
                    m = MEM.search(q.op_str)
                    if m and m.group(1) == base and rel < int(m.group(2), 16) < rel + size:
                        hits[t].append((int(m.group(2), 16) - rel, hex(q.address), f'{q.mnemonic} {q.op_str}', name,
                                        hex(i.address)))
                if redefines(q):
                    return

        walk(range(defpos - 1, max(0, defpos - 200), -1), True)
        if not re.fullmatch(r'x(9|1[0-8]|[0-8])', base):  # (caller-saved registers do not survive the call)
            walk(range(k + 1, min(len(ins), k + 200)), False)
    return hits, calls


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--exefs', default=os.path.join(ROOT, 'targets', 'exefs'))
    ap.add_argument('--json', help='write every hit (offset, address, instruction, NVN function, call) here')
    a = ap.parse_args(argv)
    n = Nso(os.path.join(a.exefs, 'main'))
    ins = disasm(n)
    slots = map_slots(n, ins)
    print(f'{len(slots)} NVN proc slots mapped')
    hits, calls = scan(ins, slots)
    for t in sorted(RT):
        h = hits.get(t, [])
        offs = sorted(collections.Counter(x[0] for x in h).items())[:8]
        print(f'{t:18} size {RT[t]:#5x}  calls {calls[t]:5}  overlapping accesses {len(h):4}  offsets {offs}')
    if a.json:
        with open(a.json, 'w') as f:
            json.dump(hits, f, indent=0)
    return 0


if __name__ == '__main__':
    sys.exit(main())
