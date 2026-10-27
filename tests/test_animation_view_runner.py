"""Smoke test em Lua do visualizador de animações."""
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class AnimationViewTests(unittest.TestCase):
    def test_animation_draw_in_lua(self):
        exe=shutil.which('lua') or shutil.which('luajit') or shutil.which('luatex')
        if not exe:self.skipTest('Lua indisponível')
        args=[exe]+(['--luaonly'] if Path(exe).name=='luatex' else [])+['tests/test_animation_view.lua']
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn('Testes animation_view: OK',p.stdout)
