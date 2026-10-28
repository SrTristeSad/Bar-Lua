"""Executa casos Lua reais em luatex/lua; não promete validação gráfica do LÖVE."""
from pathlib import Path
import subprocess
import shutil
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PlaytestLuaTest(unittest.TestCase):
    def _run(self, name):
        exe = shutil.which('lua') or shutil.which('luajit') or shutil.which('luatex')
        if not exe:
            self.skipTest('Lua/luatex indisponível')
        cmd = [exe] + (['--luaonly'] if Path(exe).name == 'luatex' else []) + [f'tests/{name}.lua']
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=35)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(' OK', r.stdout)
    def test_playtest_math_and_physics_calls(self):
        self._run('test_playtest')
    def test_real_original_assets(self):
        if not (ROOT / 'cache/animations.lua').is_file():
            self.skipTest('Cache de recursos locais ausente')
        self._run('test_playtest_integration')