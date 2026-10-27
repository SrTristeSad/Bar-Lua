import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestMovementLua(unittest.TestCase):
    def test_lua_codec_and_view(self):
        binary=shutil.which('luatex')
        if not binary:
            self.skipTest('luatex indisponível')
        for test_file in ('tests/test_movement_codec.lua', 'tests/test_movement_view.lua'):
            with self.subTest(file=test_file):
                p=subprocess.run([binary,'--luaonly',test_file],cwd=ROOT,text=True,capture_output=True,timeout=20)
                self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
                self.assertIn('tests OK',p.stdout)