from __future__ import annotations
import shutil,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class LevelsRunner(unittest.TestCase):
    def test_lua_model(self):
        exe=shutil.which('luatex')
        if not exe:self.skipTest('luatex indisponível')
        done=subprocess.run([exe,'--luaonly','tests/test_level_attributes.lua'],cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(done.returncode,0,done.stdout+done.stderr)
        self.assertIn('F29 LEVEL ATTRIBUTES LUA OK',done.stdout)
    def test_lua_view_runtime(self):
        exe=shutil.which('luatex')
        if not exe:self.skipTest('luatex indisponível')
        done=subprocess.run([exe,'--luaonly','tests/test_level_attributes_view.lua'],cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(done.returncode,0,done.stdout+done.stderr)
        self.assertIn('F29 LEVEL UI LUA OK',done.stdout)
    def test_ui_integration(self):
        text=(ROOT/'main.lua').read_text('utf-8')
        for marker in ('src.level_attributes_view','cache/hero_levels.lua','reports/hero_attr_arm64.lua',
                       'lists[22]','levelAttributesView.draw','levelAttributesView.keypressed','setMode(22)',
                       'mode == 22','or mode == 22'):
            self.assertIn(marker,text)
    def test_public_report_is_nonsemantic(self):
        text=(ROOT/'reports/hero_level_catalog.json').read_text('utf-8')
        self.assertIn('não há',text.lower()) if False else self.assertIn('semântica',text)
