from __future__ import annotations
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DeathRuleTests(unittest.TestCase):
    def test_lua(self):
        binary=shutil.which('luatex')
        if not binary:self.skipTest('luatex ausente')
        result=subprocess.run([binary,'--luaonly','tests/test_death_rules.lua'],cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        self.assertIn('F26 DEATH RULES LUA OK',result.stdout)
    def test_main(self):
        main=(ROOT/'main.lua').read_text(encoding='utf-8')
        for term in ('src.death_view','reports/death_flow.lua','lists[19][1]',
                     'deathView.draw','deathView.keypressed','setMode(19)',
                     'mode == 19'):
            self.assertIn(term,main)
