#!/usr/bin/env python3
"""
tools/repack_spirv.py: Recompresses an existing XC3Recomp cache/spirv.pack with Zstandard (Zstd).

Shrinks uncompressed SPIR-V pack files (~15 GB down to ~3 GB) without needing to
re-run RomFS shader precompilation. Also ingests and removes loose cache/spirv/*.spv files.

Usage:
    python3 tools/repack_spirv.py [cache_dir]
"""

import os
import sys
import struct
import shutil
import ctypes
import ctypes.util

PACK_MAGIC_RAW  = 0x56505358  # 'XSPV' (uncompressed)
PACK_MAGIC_ZSTD = 0x5650535A  # 'ZSPV' (Zstandard)


def get_zstd_compressor():
    """Try to obtain a zstd compression function via python-zstandard or ctypes libzstd."""
    try:
        import zstandard
        cctx = zstandard.ZstdCompressor(level=3)
        return lambda data: cctx.compress(data)
    except ImportError:
        pass

    # Fallback to ctypes
    lib_names = [
        ctypes.util.find_library("zstd"),
        "libzstd.dll",
        "libzstd-1.dll",
        "C:\\msys64\\ucrt64\\bin\\libzstd-1.dll",
        "libzstd.so.1",
        "libzstd.so",
        "libzstd.dylib",
        "/opt/homebrew/lib/libzstd.dylib",
        "/usr/local/lib/libzstd.dylib",
    ]
    lib = None
    for name in lib_names:
        if not name:
            continue
        try:
            lib = ctypes.CDLL(name)
            break
        except Exception:
            continue

    if lib and hasattr(lib, "ZSTD_compress"):
        lib.ZSTD_compress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
        lib.ZSTD_compress.restype = ctypes.c_size_t
        lib.ZSTD_compressBound.argtypes = [ctypes.c_size_t]
        lib.ZSTD_compressBound.restype = ctypes.c_size_t
        lib.ZSTD_isError.argtypes = [ctypes.c_size_t]
        lib.ZSTD_isError.restype = ctypes.c_uint

        def compress_ctypes(data: bytes) -> bytes:
            src_len = len(data)
            bound = lib.ZSTD_compressBound(src_len)
            dst = ctypes.create_string_buffer(bound)
            res = lib.ZSTD_compress(dst, bound, data, src_len, 3)
            if lib.ZSTD_isError(res):
                raise RuntimeError(f"ZSTD_compress error code {res}")
            return dst.raw[:res]

        return compress_ctypes

    return None


def pack_check(h: int, off: int, b: int) -> int:
    return (b ^ (h & 0xFFFFFFFF) ^ ((off >> 3) & 0xFFFFFFFF) ^ 0x5853) & 0xFFFFFFFF


def repack_cache(cache_dir: str):
    pack_path = os.path.join(cache_dir, "spirv.pack")
    idx_path = os.path.join(cache_dir, "spirv.idx")

    if not os.path.isfile(pack_path) or not os.path.isfile(idx_path):
        print(f"[repack] No spirv.pack or spirv.idx found in {cache_dir}")
        return 0

    compress_fn = get_zstd_compressor()
    if not compress_fn:
        print("[repack] ERROR: Zstandard library not found.")
        print("  Please install with: pip install zstandard (or run 'xc3.exe --repack-spirv' on Windows)")
        return 1

    idx_size = os.path.getsize(idx_path)
    entry_count = idx_size // 24
    print(f"[repack] Reading index ({entry_count} entries) from {idx_path}...")

    # Deduplicate entries by hash (latest record wins)
    entries = {}
    with open(idx_path, "rb") as fi:
        for _ in range(entry_count):
            buf = fi.read(24)
            if len(buf) < 24:
                break
            h, off, b, chk = struct.unpack("<QQII", buf)
            if h == 0 or chk != pack_check(h, off, b):
                continue
            entries[h] = (off, b)

    print(f"[repack] Found {len(entries)} unique shader entries. Recompressing into {pack_path}.tmp...")

    tmp_pack_path = pack_path + ".tmp"
    tmp_idx_path = idx_path + ".tmp"

    old_total = 0
    new_total = 0
    recompressed_count = 0
    processed_count = 0

    with open(pack_path, "rb") as f_in, open(tmp_pack_path, "wb") as f_pack_out, open(tmp_idx_path, "wb") as f_idx_out:
        for h, (off, b) in entries.items():
            if off < 16:
                continue
            f_in.seek(off - 16)
            rec = f_in.read(16 + b)
            if len(rec) != 16 + b:
                continue
            magic, uncompressed_size, h_lo, h_hi = struct.unpack("<IIII", rec[:16])
            rec_h = (h_hi << 32) | h_lo
            if rec_h != h:
                continue

            old_total += 16 + b
            payload = rec[16:]
            out_magic = magic
            out_raw_bytes = uncompressed_size
            out_payload = payload

            if magic == PACK_MAGIC_RAW:
                try:
                    c_data = compress_fn(payload)
                    if len(c_data) < len(payload):
                        out_magic = PACK_MAGIC_ZSTD
                        out_raw_bytes = len(payload)
                        out_payload = c_data
                        recompressed_count += 1
                except Exception as e:
                    pass

            cur_off = f_pack_out.tell()
            hdr = struct.pack("<IIII", out_magic, out_raw_bytes, h_lo, h_hi)
            f_pack_out.write(hdr)
            f_pack_out.write(out_payload)

            new_off = cur_off + 16
            new_bytes = len(out_payload)
            chk = pack_check(h, new_off, new_bytes)
            f_idx_out.write(struct.pack("<QQII", h, new_off, new_bytes, chk))

            new_total += 16 + new_bytes
            processed_count += 1

            if processed_count % 5000 == 0:
                print(f"[repack] Processed {processed_count}/{len(entries)} shaders...")

    # Replace files safely
    bak_pack = pack_path + ".bak"
    bak_idx = idx_path + ".bak"
    if os.path.exists(bak_pack):
        os.remove(bak_pack)
    if os.path.exists(bak_idx):
        os.remove(bak_idx)

    shutil.move(pack_path, bak_pack)
    shutil.move(idx_path, bak_idx)
    shutil.move(tmp_pack_path, pack_path)
    shutil.move(tmp_idx_path, idx_path)

    if os.path.exists(bak_pack):
        os.remove(bak_pack)
    if os.path.exists(bak_idx):
        os.remove(bak_idx)

    # Ingest / clean up loose files in cache/spirv
    loose_dir = os.path.join(cache_dir, "spirv")
    loose_removed = 0
    if os.path.isdir(loose_dir):
        for fname in os.listdir(loose_dir):
            if fname.endswith(".spv") and len(fname) == 20:
                try:
                    os.remove(os.path.join(loose_dir, fname))
                    loose_removed += 1
                except OSError:
                    pass
        try:
            os.rmdir(loose_dir)
        except OSError:
            pass

    old_mb = old_total / (1024 * 1024)
    new_mb = new_total / (1024 * 1024)
    saved_mb = old_mb - new_mb
    pct = (saved_mb / old_mb * 100.0) if old_mb > 0 else 0.0

    print(f"\n[repack] Successfully repacked {processed_count} shaders ({recompressed_count} newly compressed with Zstd).")
    print(f"[repack] Size: {old_mb:.1f} MB -> {new_mb:.1f} MB (Saved {saved_mb:.1f} MB, -{pct:.1f}%)")
    if loose_removed > 0:
        print(f"[repack] Removed {loose_removed} redundant loose .spv files.")
    return 0


def main():
    cache_dir = sys.argv[1] if len(sys.argv) > 1 else "cache"
    sys.exit(repack_cache(cache_dir))


if __name__ == "__main__":
    main()
