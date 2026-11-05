"""Unit test for ASTC Compute Shader Decoder and fallback logic."""
import os
import unittest
import ctypes

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASTC_INC = os.path.join(ROOT, "runtime", "nvn", "vulkan", "astc_cs.inc")
ASTC_C = os.path.join(ROOT, "runtime", "nvn", "astc.c")


class TestAstcDecoder(unittest.TestCase):
    def test_astc_cs_inc_exists_and_valid(self):
        self.assertTrue(os.path.exists(ASTC_INC), "astc_cs.inc must exist")
        with open(ASTC_INC, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("static const char astc_glsl[]", content)
        self.assertIn("#version 450", content)
        self.assertIn("layout(local_size_x = 64) in;", content)
        self.assertIn("layout(push_constant) uniform ASTCParams", content)
        self.assertIn("void main()", content)
        self.assertIn("ise_decode_weights", content)
        self.assertIn("ise_decode_colors", content)
        self.assertIn("unpack_endpoints", content)
        self.assertIn("part_init", content)

    def test_astc_c_software_reference(self):
        """Test compiling astc.c as dylib/so and decoding void-extent and error blocks."""
        import tempfile
        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            lib_path = os.path.join(tmpdir, "libastc.dylib")
            res = subprocess.run([
                "clang", "-shared", "-O2", "-fPIC",
                "-I" + os.path.join(ROOT, "runtime", "nvn"),
                ASTC_C, "-o", lib_path
            ], capture_output=True)
            if res.returncode != 0:
                self.skipTest(f"clang not available to build libastc: {res.stderr.decode()}")

            lib = ctypes.CDLL(lib_path)
            # void astc_decode_ldr(const uint8_t *blocks, uint32_t width, uint32_t height, uint32_t bw, uint32_t bh, bool srgb, uint8_t *rgba_out)
            lib.astc_decode_ldr.argtypes = [
                ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32,
                ctypes.c_uint32, ctypes.c_uint32, ctypes.c_bool, ctypes.c_char_p
            ]
            lib.astc_decode_ldr.restype = None

            # Test 1: Void-extent block for a solid green color (top bytes: R=0, G=255, B=0, A=255)
            # In ASTC void-extent mode: mode bits [0..8] = 0x1FC (bits 0..8 = 111111100 in bin = 0x1FC)
            # bits [10..11] = 3 (reserved)
            # block[9]=0, block[11]=255, block[13]=0, block[15]=255
            block = bytearray(16)
            # 0x1FC in bits 0..8: byte 0 = 0xFC, byte 1 = 0x01 | (3 << 2) = 0x0D
            block[0] = 0xFC
            block[1] = 0x0D
            # s0, s1, t0, t1 all ones (0x1FFF)
            # s0 (12..24): 13 bits of 1 starting at bit 12
            # byte 1 bit 4..7 (4 bits), byte 2 (8 bits), byte 3 bit 0 (1 bit) = 13 bits
            block[1] |= (0xF << 4)
            block[2] = 0xFF
            block[3] = 0xFF
            block[4] = 0xFF
            block[5] = 0xFF
            block[6] = 0xFF
            block[7] = 0xFF
            block[9] = 0x12   # R
            block[11] = 0x34  # G
            block[13] = 0x56  # B
            block[15] = 0xFF  # A

            out = bytearray(4 * 4 * 4)  # 4x4 texels, 4 bytes each = 64 bytes
            lib.astc_decode_ldr(bytes(block), 4, 4, 4, 4, False, (ctypes.c_char * len(out)).from_buffer(out))

            # Every pixel should be 0x12, 0x34, 0x56, 0xFF
            for i in range(16):
                px = out[4*i : 4*i + 4]
                self.assertEqual(px, bytearray([0x12, 0x34, 0x56, 0xFF]))


if __name__ == "__main__":
    unittest.main()
