import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_ataques import audit

class Attacks(unittest.TestCase):
    def test_provenance_report_from_original(self):
        args=(ROOT/'lib/arm64-v8a/libcocos2dcpp.so',ROOT/'reports/native_arm64.json',
              ROOT/'assets_original/character/babarian/babarian.bexportjson')
        report=audit(*args)
        self.assertEqual(report,json.loads((ROOT/'reports/native_attacks.json').read_text()))
        self.assertEqual(sum(len(x) for x in report['attack_movements'].values()),15)
        self.assertEqual(sum(x['instructions'] for x in report['functions'].values()),35)
    def test_reject_wrong_library(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            target=Path(tmp)/'wrong.so';target.write_bytes(b'wrong')
            with self.assertRaisesRegex(ValueError,'SHA-256'):
                audit(target,ROOT/'reports/native_arm64.json',
                      ROOT/'assets_original/character/babarian/babarian.bexportjson')
    def test_lua_preview(self):
        for name in ('test_attack_preview','test_attack_preview_real','test_attack_sprites_real'):
            p=subprocess.run(['luatex','--luaonly',f'tests/{name}.lua'],cwd=ROOT,
                             capture_output=True,text=True,timeout=30)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertIn(' OK',p.stdout)
if __name__=='__main__':unittest.main()
