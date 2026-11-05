import os
import sys
import shutil
import struct
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from tools.repack_spirv import repack_cache, pack_check, PACK_MAGIC_RAW, PACK_MAGIC_ZSTD


class TestSpirvRepack(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.test_dir, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pack_check_algorithm(self):
        # Test pack_check parity with C: e->bytes ^ (uint32_t)e->hash ^ (uint32_t)(e->off >> 3) ^ 0x5853u
        h = 0x123456789ABCDEF0
        off = 0x1000
        b = 512
        expected = (512 ^ (h & 0xFFFFFFFF) ^ ((off >> 3) & 0xFFFFFFFF) ^ 0x5853) & 0xFFFFFFFF
        self.assertEqual(pack_check(h, off, b), expected)

    def test_repack_compresses_raw_entries(self):
        pack_path = os.path.join(self.cache_dir, "spirv.pack")
        idx_path = os.path.join(self.cache_dir, "spirv.idx")

        # Create dummy shaders with SPIR-V magic word (0x07230203) and repeated redundant words
        shaders = []
        for i in range(10):
            h = 0xCAFE0000 + i
            # 1024 words (4096 bytes) of redundant SPIR-V-like pattern
            spv_words = [0x07230203] + [0x00050011, i, 0x0004002B, 0x00000006] * 255
            data = struct.pack(f"<{len(spv_words)}I", *spv_words)
            shaders.append((h, data))

        # Write raw uncompressed pack file and index
        with open(pack_path, "wb") as f_pack, open(idx_path, "wb") as f_idx:
            for h, data in shaders:
                cur_off = f_pack.tell()
                h_lo = h & 0xFFFFFFFF
                h_hi = (h >> 32) & 0xFFFFFFFF
                hdr = struct.pack("<IIII", PACK_MAGIC_RAW, len(data), h_lo, h_hi)
                f_pack.write(hdr)
                f_pack.write(data)

                new_off = cur_off + 16
                b = len(data)
                chk = pack_check(h, new_off, b)
                f_idx.write(struct.pack("<QQII", h, new_off, b, chk))

        raw_size = os.path.getsize(pack_path)
        self.assertGreater(raw_size, 40000)

        # Also create a dummy loose file
        loose_dir = os.path.join(self.cache_dir, "spirv")
        os.makedirs(loose_dir, exist_ok=True)
        dummy_loose = os.path.join(loose_dir, f"{0xCAFE0000:016x}.spv")
        with open(dummy_loose, "wb") as f:
            f.write(b"\x03\x02\x23\x07" + b"\x00" * 100)

        # Run repack
        ret = repack_cache(self.cache_dir)
        self.assertEqual(ret, 0)

        # Verify repack shrunk the pack file
        repacked_size = os.path.getsize(pack_path)
        self.assertLess(repacked_size, raw_size // 2)

        # Verify loose file directory was cleaned up
        self.assertFalse(os.path.exists(dummy_loose))

        # Verify index and magic in repacked file
        with open(idx_path, "rb") as fi, open(pack_path, "rb") as fp:
            for _ in range(len(shaders)):
                buf = fi.read(24)
                h, off, b, chk = struct.unpack("<QQII", buf)
                self.assertEqual(chk, pack_check(h, off, b))
                fp.seek(off - 16)
                rec = fp.read(16 + b)
                magic, raw_len, h_lo, h_hi = struct.unpack("<IIII", rec[:16])
                self.assertEqual(magic, PACK_MAGIC_ZSTD)
                self.assertEqual(raw_len, len(shaders[0][1]))
                self.assertEqual((h_hi << 32) | h_lo, h)


if __name__ == "__main__":
    unittest.main()
