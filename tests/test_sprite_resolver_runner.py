"""Testes Lua do resolver de imagens, se há interpretador instalado."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class SpriteResolverLuaTests(unittest.TestCase):
    def test_resolver_lua(self):
        exe = shutil.which('lua') or shutil.which('luajit') or shutil.which('luatex')
        if exe is None:
            self.skipTest('Lua não disponível')
        args = [exe] + (['--luaonly'] if Path(exe).name == 'luatex' else []) + ['tests/test_sprite_resolver.lua']
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + '\n' + result.stderr)
        self.assertIn('Testes sprite resolver: OK', result.stdout)
