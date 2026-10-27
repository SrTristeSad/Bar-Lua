import shutil
import subprocess
import unittest
from pathlib import Path

class TestFlowView(unittest.TestCase):
    def test_flow_view(self):
        lua = shutil.which('luatex')
        if not lua:
            self.skipTest('luatex não instalado; teste do módulo Lua requer interpretador')
        root=Path(__file__).resolve().parents[1]
        result=subprocess.run([lua,'--luaonly','tests/test_flow_view.lua'],
                              cwd=root, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        self.assertIn('flow_view tests OK', result.stdout)