import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class TestNativeContacts(unittest.TestCase):
    def test_report_matches_elf_manifest(self):
        rep=json.loads((ROOT/'reports/native_contacts.json').read_text(encoding='utf-8'))
        meta=json.loads((ROOT/'reports/native_arm64.json').read_text(encoding='utf-8'))
        digest=next(x['sha256'] for x in meta['libraries'] if x['name']=='libcocos2dcpp.so')
        self.assertEqual(rep['library_sha256'],digest)
        self.assertEqual(len(rep['functions']),8)
        self.assertEqual(sum(x['instructions'] for x in rep['functions']),457)
        self.assertEqual(sum(len(x['verified_patterns']) for x in rep['functions']),18)
    def test_empty_listener_callbacks(self):
        rep=json.loads((ROOT/'reports/native_contacts.json').read_text(encoding='utf-8'))
        blank=[f for f in rep['functions'] if f['signature'].startswith('wildsContactListener::')
               and 'BeginContact' not in f['signature']]
        self.assertEqual(len(blank),3)
        self.assertTrue(all(f['instructions']==1 for f in blank))
    def test_lua_view(self):
        lua=shutil.which('luatex')
        if not lua:self.skipTest('luatex não encontrado')
        proc=subprocess.run([lua,'--luaonly','tests/test_contact_view.lua'],cwd=ROOT,capture_output=True,text=True,timeout=25)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
    def test_lua_syntax(self):
        lua=shutil.which('luatex')
        if not lua:self.skipTest('luatex não encontrado')
        proc=subprocess.run([lua,'--luaonly','tests/test_f15_syntax.lua'],cwd=ROOT,capture_output=True,text=True,timeout=25)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
