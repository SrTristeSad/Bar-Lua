from __future__ import annotations
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class RebornLuaTests(unittest.TestCase):
    def test_lua_rules_and_view(self):
        luatex=shutil.which('luatex')
        if luatex is None:self.skipTest('luatex ausente')
        run=subprocess.run([luatex,'--luaonly','tests/test_reborn_rules.lua'],cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stdout+'\n'+run.stderr)
        self.assertIn('F27 REBORN LUA OK',run.stdout)
    def test_main_mode_and_resources(self):
        text=(ROOT/'main.lua').read_text(encoding='utf-8')
        for token in ['src.reborn_view','reports/reborn_flow.lua','lists[20][1]',
                      'rebornView.draw','rebornView.keypressed','setMode(20)',
                      'mode == 20']:
            self.assertIn(token,text)
    def test_native_report_export_exists(self):
        self.assertTrue((ROOT/'reports/reborn_flow.json').exists())
        self.assertTrue((ROOT/'reports/reborn_flow.lua').exists())
