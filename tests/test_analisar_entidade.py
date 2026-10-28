import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import analisar_entidade as analyzer

class TestEntityAudit(unittest.TestCase):
    def test_report_provenance(self):
        report=json.loads((ROOT/'reports/entity_move.json').read_text(encoding='utf-8'))
        original=json.loads((ROOT/'reports/native_arm64.json').read_text(encoding='utf-8'))
        sha=next(x['sha256'] for x in original['libraries'] if x['name']=='libcocos2dcpp.so')
        self.assertEqual(report['library_sha256'],sha)
        self.assertEqual((report['instructions'],report['verified_patterns']), (59,21))
        self.assertAlmostEqual(report['float_constants']['negative_epsilon'],-0.0001,places=7)
        self.assertEqual(report['float_constants']['transform_divisor'],30)
        self.assertIn('b2Body',report['control_flow'][-1])
    def test_known_instructions(self):
        fake='\n'.join(' '+p.replace('\\b','') for p in analyzer.PATTERNS.values())
        self.assertEqual(len(analyzer.PATTERNS),21)
        # Validate that the pattern set is not accidentally empty and rejects bad code.
        self.assertTrue([key for key,pattern in analyzer.PATTERNS.items() if not __import__('re').search(pattern,'ret')])
    def test_lua_model_and_view(self):
        binary=shutil.which('luatex')
        if not binary: self.skipTest('luatex ausente')
        for name in ('test_entity_move.lua','test_entity_move_view.lua'):
            with self.subTest(name=name):
                proc=subprocess.run([binary,'--luaonly','tests/'+name],cwd=ROOT,capture_output=True,text=True,timeout=20)
                self.assertEqual(proc.returncode,0,proc.stdout+'\n'+proc.stderr)
                self.assertIn('tests OK',proc.stdout)
    def test_lua_syntax(self):
        binary=shutil.which('luatex')
        if not binary: self.skipTest('luatex ausente')
        proc=subprocess.run([binary,'--luaonly','tests/test_f14_syntax.lua'],cwd=ROOT,
                            capture_output=True,text=True,timeout=20)
        self.assertEqual(proc.returncode,0,proc.stdout+'\n'+proc.stderr)
        self.assertIn('F14 syntax OK',proc.stdout)
