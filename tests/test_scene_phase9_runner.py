"""Executa as suites Lua da Fase 9 junto a unittest discover."""
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ScenePhase9Tests(unittest.TestCase):
    def test_lua_resolver_and_layout(self):
        exe=shutil.which('lua') or shutil.which('luajit') or shutil.which('luatex') or shutil.which('luahbtex')
        if not exe:self.skipTest('Lua indisponível')
        for path in ['tests/test_scene_resources.lua','tests/test_scene_layout.lua']:
            cmd=[exe]+(['--luaonly'] if Path(exe).name in ('luatex','luahbtex') else [])+[path]
            with self.subTest(path=path):
                r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=30)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                self.assertIn('OK',r.stdout)
