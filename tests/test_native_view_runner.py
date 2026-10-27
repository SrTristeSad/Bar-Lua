import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NativeViewRunner(unittest.TestCase):
    def test_lua(self):
        exe=next((shutil.which(x) for x in ('lua','luajit','luatex','luahbtex') if shutil.which(x)),None)
        if not exe:self.skipTest('Sem interpretador Lua')
        args=[exe] + (['--luaonly'] if Path(exe).name in ('luatex','luahbtex') else []) + ['tests/test_native_view.lua']
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        self.assertIn('FASE11 NATIVE VIEW OK',result.stdout)
