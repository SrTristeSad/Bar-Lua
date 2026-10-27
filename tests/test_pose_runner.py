"""Executa testes de matemática 2D com um interpretador Lua, quando instalado."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PoseLuaTests(unittest.TestCase):
    def test_pose_math_when_interpreter_available(self):
        exe = shutil.which("lua") or shutil.which("luajit") or shutil.which("luatex")
        if exe is None:
            self.skipTest("Lua não disponível")
        cmd = [exe] + (["--luaonly"] if Path(exe).name == "luatex" else []) + ["tests/test_pose.lua"]
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        self.assertIn("Testes pose: OK", result.stdout)
