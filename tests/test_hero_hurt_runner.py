from __future__ import annotations
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class HurtLuaTests(unittest.TestCase):
    def test_lua_transition_and_panel(self):
        executable = shutil.which('luatex')
        if not executable:
            self.skipTest('luatex ausente')
        process = subprocess.run([executable, '--luaonly', 'tests/test_hero_hurt.lua'],
                                 cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode,0,process.stdout+process.stderr)
        self.assertIn('F25 HERO HURT LUA OK',process.stdout)
    def test_main_integrated(self):
        text=(ROOT/'main.lua').read_text('utf-8')
        for needed in ('src.hero_hurt_view','reports/entity_damage_flow.lua',
                       'heroHurtView.draw', 'heroHurtView.keypressed',
                       'setMode(18)', 'lists[18][1]'):
            self.assertIn(needed,text)
        self.assertIn('mode == 18',text)
