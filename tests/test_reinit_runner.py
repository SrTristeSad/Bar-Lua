from __future__ import annotations
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ReinitRunner(unittest.TestCase):
    def test_rules_in_lua(self):
        luatex=shutil.which('luatex')
        if not luatex:self.skipTest('luatex não disponível')
        proc=subprocess.run([luatex,'--luaonly','tests/test_reinit_rules.lua'],
                            cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertIn('F28 REINIT LUA OK',proc.stdout)
    def test_gui_integration(self):
        app=(ROOT/'main.lua').read_text('utf-8')
        for marker in ('src.reinit_view','reports/reinit_flow.lua','lists[21][1]',
                       'reinitView.draw','reinitView.keypressed','setMode(21)',
                       'mode == 21','or mode == 21'):
            self.assertIn(marker,app)
    def test_report_present(self):
        self.assertTrue((ROOT/'reports/reinit_flow.json').exists())
        self.assertTrue((ROOT/'reports/reinit_flow.lua').exists())
