import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SkillSchemaLua(unittest.TestCase):
    def test_view_lua(self):
        exe=shutil.which('luatex')
        if not exe:self.skipTest('luatex ausente')
        result=subprocess.run([exe,'--luaonly','tests/test_hero_skill_schema.lua'],cwd=ROOT,text=True,capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('F39 SKILL SCHEMA LUA OK',result.stdout)
