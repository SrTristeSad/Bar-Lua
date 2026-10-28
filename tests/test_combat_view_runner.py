from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
class CombatViewRunner(unittest.TestCase):
    def test_lua_ui(self):
        luatex=shutil.which('luatex')
        if not luatex: self.skipTest('luatex ausente')
        proc=subprocess.run([luatex,'--luaonly', 'tests/test_combat_view.lua'],
                            cwd=ROOT,capture_output=True,text=True,timeout=25)
        self.assertEqual(proc.returncode,0,proc.stderr or proc.stdout)
        self.assertIn('OK',proc.stdout)
