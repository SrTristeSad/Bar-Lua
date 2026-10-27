import shutil, subprocess, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SceneViewTests(unittest.TestCase):
    def test_scene_view_lua(self):
        exe=shutil.which('lua') or shutil.which('luajit') or shutil.which('luatex') or shutil.which('luahbtex')
        if not exe:self.skipTest('Lua indisponível')
        cmd=[exe]+(['--luaonly'] if Path(exe).name in ('luatex','luahbtex') else [])+['tests/test_scene_view.lua']
        r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn('Testes scene_view: OK',r.stdout)