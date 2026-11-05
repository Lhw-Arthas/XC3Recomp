import unittest
import re
import os

class TestNvnCommands(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def test_cmd_enum_values(self):
        nvn_h_path = os.path.join(self.root_dir, "runtime", "nvn", "nvn.h")
        with open(nvn_h_path, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.search(r"enum\s*\{(.*?CMD_COUNT\s*)\};", content, re.DOTALL)
        self.assertIsNotNone(match, "enum CMD_* not found in runtime/nvn/nvn.h")

        enum_body = match.group(1)
        # Remove comments
        enum_body = re.sub(r"//.*", "", enum_body)
        enum_body = re.sub(r"/\*.*?\*/", "", enum_body, flags=re.DOTALL)

        tokens = [t.strip() for t in enum_body.split(",") if t.strip()]
        enum_map = {}
        cur_val = 0
        for token in tokens:
            if "=" in token:
                name, val_str = token.split("=", 1)
                name = name.strip()
                cur_val = int(val_str.strip())
            else:
                name = token.strip()
            enum_map[name] = cur_val
            cur_val += 1

        self.assertIn("CMD_WAIT_SYNC", enum_map)
        self.assertEqual(enum_map["CMD_WAIT_SYNC"], 50, "CMD_WAIT_SYNC must be opcode 50")
        self.assertIn("CMD_DRAW_TRANSFORM_FEEDBACK", enum_map)

    def test_exec_c_handlers(self):
        exec_c_path = os.path.join(self.root_dir, "runtime", "nvn", "vulkan", "exec.c")
        with open(exec_c_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("case CMD_WAIT_SYNC:", content, "exec.c must handle CMD_WAIT_SYNC (command 50)")
        self.assertIn("case CMD_DRAW_TRANSFORM_FEEDBACK:", content, "exec.c must handle CMD_DRAW_TRANSFORM_FEEDBACK")

    def test_cmdbuf_c_draw_xfb(self):
        cmdbuf_c_path = os.path.join(self.root_dir, "runtime", "nvn", "cmdbuf.c")
        with open(cmdbuf_c_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("nvnCommandBufferDrawTransformFeedback", content)
        self.assertIn("record(c, CMD_DRAW_TRANSFORM_FEEDBACK, 0, &s);", content)

if __name__ == "__main__":
    unittest.main()
