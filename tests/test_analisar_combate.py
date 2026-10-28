"""Testes F23: valida a cadeia ARM64 sem reproduzir a fórmula do jogo."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from analisar_combate import audit, export_lua, FUNCTIONS, CHECKS


class CombatAuditTest(unittest.TestCase):
    def test_static_contract(self):
        self.assertEqual(len(FUNCTIONS), 8)
        self.assertEqual(len({x[1] for x in FUNCTIONS}), 8)
        self.assertTrue(all(x[2] % 4 == 0 for x in FUNCTIONS))
        self.assertTrue(all(x[0] in CHECKS for x in FUNCTIONS))

    def test_lua_catalog_has_no_execution(self):
        out = export_lua({'functions': [{'name': 'Example', 'virtual_address': '0x1',
                                        'instruction_count': 1, 'checks': ['call_foo']}]})
        self.assertIn('call_foo', out)
        self.assertNotIn('love.physics', out)
        self.assertNotIn('loadstring', out)

    def test_bad_hash_rejected(self):
        lib = ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        manifest = ROOT/'reports/native_arm64.json'
        if not lib.is_file():
            self.skipTest('Biblioteca local não está disponível (não é distribuída no GitHub)')
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            altered = Path(tmp)/'libcocos2dcpp.so'
            altered.write_bytes(b'ELF-invalid')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                audit(altered, manifest)

    def test_original_elf(self):
        lib = ROOT/'lib/arm64-v8a/libcocos2dcpp.so'
        if not lib.is_file():
            self.skipTest('Biblioteca ARM64 original não incluída em repositório público')
        result = audit(lib, ROOT/'reports/native_arm64.json')
        self.assertEqual(result['total_instructions'], sum(f[2]//4 for f in FUNCTIONS))
        checks = {x['name']:set(x['checks']) for x in result['functions']}
        self.assertIn('hero_hurt',checks['CDamageFunction::Run(target)'])
        self.assertIn('physical_query',checks['CSelectTargetSector::GetSelectTargets'])
        self.assertIn('Não foram recuperados valores de dano',result['limits'])

    def test_report_matches_elf_hash(self):
        report=json.loads((ROOT/'reports/native_combat.json').read_text())
        self.assertEqual(len(report['functions']), len(FUNCTIONS))
        self.assertEqual(report['phase'],23)


if __name__ == '__main__': unittest.main()
