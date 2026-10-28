from pathlib import Path
import shutil,subprocess,unittest
ROOT=Path(__file__).resolve().parents[1]
class ObjectLuaTests(unittest.TestCase):
    def test_lua_geometry(self):self.execute('test_map_objects.lua')
    def test_lua_physics_toggle(self):self.execute('test_playtest_tmx.lua')
    def execute(self,path):
        exe=shutil.which('lua') or shutil.which('luajit') or shutil.which('luatex')
        if not exe:self.skipTest('Lua indisponivel')
        cmd=[exe]+(['--luaonly'] if Path(exe).name=='luatex' else [])+[f'tests/{path}']
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn(' OK',r.stdout)
