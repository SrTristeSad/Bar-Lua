"""Executa testes de geometria no Lua real."""
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SpriteGeometryLuaTests(unittest.TestCase):
    def test_geometry_in_lua(self):
        exe=shutil.which('lua') or shutil.which('luajit') or shutil.which('luatex')
        if not exe:self.skipTest('Interpretador Lua indisponível')
        args=[exe]+(['--luaonly'] if Path(exe).name=='luatex' else [])+['tests/test_sprite_geometry.lua']
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn('Testes sprite geometry: OK',p.stdout)
