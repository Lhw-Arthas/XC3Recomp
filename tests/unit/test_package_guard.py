"""T006 (tests first): the packaging guard refuses derived/game files (Constitution art. I, SC-012)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))
import package_guard as pg  # noqa: E402


def wb(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


class TestGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        wb(os.path.join(self.root, 'README.md'), b'# hello')
        wb(os.path.join(self.root, 'runtime', 'main.c'), b'#include <stdio.h>\nint main(void){return 0;}\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_tree_passes(self):
        self.assertEqual(pg.scan(self.root), [])

    def test_nso_by_magic_even_with_innocent_name(self):
        wb(os.path.join(self.root, 'data', 'readme.txt'), b'NSO0' + bytes(100))
        self.assertTrue(any('NSO' in v for v in pg.scan(self.root)))

    def test_container_and_nca_extensions(self):
        for ext in ('.nsp', '.xci', '.nca', '.nsz', '.xcz', '.nso', '.nro', '.bfttf'):
            wb(os.path.join(self.root, 'x' + ext), b'z')
        found = ' '.join(pg.scan(self.root))
        for ext in ('.nsp', '.xci', '.nca', '.nsz', '.xcz', '.nso', '.nro', '.bfttf'):
            self.assertIn(ext, found)

    def test_keys_files_and_key_content(self):
        wb(os.path.join(self.root, 'prod.keys'), b'x')
        wb(os.path.join(self.root, 'notes.txt'), b'master_key_00 = ' + b'ab' * 16)
        v = ' '.join(pg.scan(self.root))
        self.assertIn('prod.keys', v)
        self.assertIn('notes.txt', v)

    def test_generated_lifted_code(self):
        wb(os.path.join(self.root, 'src', 'chunk.c'),
           b'#include "cpu.h"\nvoid f_7000123456(Cpu *c) {\n    FN_ENTER(0x7000123456ull);\n}\n')
        self.assertTrue(any('lifted' in v.lower() for v in pg.scan(self.root)))

    def test_forbidden_directories(self):
        for d in ('targets', 'generated', 'extracted', 'romfs', 'exefs'):
            wb(os.path.join(self.root, d, 'f.txt'), b'x')
        found = ' '.join(pg.scan(self.root))
        for d in ('targets', 'generated', 'extracted', 'romfs', 'exefs'):
            self.assertIn(d, found)

    def test_main_returns_nonzero_on_violation(self):
        wb(os.path.join(self.root, 'a.nsp'), b'x')
        self.assertNotEqual(pg.main([self.root]), 0)

    def test_main_returns_zero_when_clean(self):
        self.assertEqual(pg.main([self.root]), 0)

    def test_gitdir_and_build_tools_are_ignored(self):
        wb(os.path.join(self.root, '.git', 'objects', 'a.nsp'), b'x')
        self.assertEqual(pg.scan(self.root), [])


if __name__ == '__main__':
    unittest.main()
