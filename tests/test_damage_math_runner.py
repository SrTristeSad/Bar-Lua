import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class LuaDamageMathTests(unittest.TestCase):
    def test_lua(self):
        exe=shutil.which('luatex')
        if not exe: self.skipTest('luatex não instalado')
        r=subprocess.run([exe,'--luaonly','tests/test_damage_math.lua'],cwd=ROOT,check=False,text=True,capture_output=True,timeout=20)
        self.assertEqual(r.returncode,0,r.stderr or r.stdout)
        self.assertIn('F24 DAMAGE MATH LUA OK',r.stdout)
