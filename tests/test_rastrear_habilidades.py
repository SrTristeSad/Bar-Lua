import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rastrear_habilidades import trace, export_lua

class TraceSkillTests(unittest.TestCase):
    def test_original_records_and_examples(self):
        report, entries = trace(ROOT / 'assets_original', ROOT/'reports/skill_catalog_summary.json')
        self.assertEqual(report, json.loads((ROOT/'reports/skill_trace_summary.json').read_text(encoding='utf-8')))
        self.assertEqual(report['indexed_records'], 72765)
        self.assertEqual(report['selected_skill_ids'], 277)
        self.assertEqual(entries[4010020]['incoming_total'], 1)
        self.assertEqual(entries[4010020]['incoming'][0]['id'], 10039)
        self.assertEqual(entries[4010020]['outgoing_total'], 0)
        self.assertIn(10052, [r['id'] for r in entries[4020020]['outgoing']])
        self.assertEqual([r['id'] for r in entries[10070]['outgoing']], [4070020,4080020])
        self.assertEqual(export_lua(entries), (ROOT/'cache/skill_trace.lua').read_text(encoding='utf-8'))

    def test_integrity_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp)/'old.json'
            old = json.loads((ROOT/'reports/skill_catalog_summary.json').read_text())
            old['table_sha256']['functiondamage'] = '0'*64
            bad.write_text(json.dumps(old))
            with self.assertRaisesRegex(ValueError,'SHA-256'):
                trace(ROOT/'assets_original',bad)

    def test_lua_ui_and_cache(self):
        p = subprocess.run(['luatex','--luaonly','tests/test_skill_trace.lua'],capture_output=True,text=True,cwd=ROOT,timeout=30)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
        self.assertIn('F22 OK',p.stdout)
