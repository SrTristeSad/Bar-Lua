import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "preparar_recursos.py"
spec = importlib.util.spec_from_file_location("prepare", MODULE)
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)

class ConverterTests(unittest.TestCase):
    def test_lua_string_escaping(self):
        self.assertEqual(prepare.lua('a"b\\c'), '"a\\"b\\\\c"')
        self.assertEqual(prepare.lua('á'), '"\\195\\161"')

    def test_numvec(self):
        self.assertEqual(prepare.numvec('{{658,740},{80,80}}', 4), [658, 740, 80, 80])

    def test_original_apk_when_available(self):
        original = Path(__file__).resolve().parents[1] / "assets_original"
        if not original.is_dir():
            self.skipTest("APK extraído indisponível (teste de integração opcional)")
        with tempfile.TemporaryDirectory() as folder:
            summary = prepare.prepare(original, Path(folder))
            self.assertEqual(summary["maps"], 32)
            self.assertEqual(summary["tile_layers"], 32)
            self.assertEqual(summary["atlases_xml"], 2)
            self.assertEqual(summary["sprites_xml"], 195)
            self.assertTrue((Path(folder) / 'maps.lua').stat().st_size > 500)
            self.assertEqual(summary['animation_files'], 1079)
            self.assertEqual(summary['animation_keyframes'], 38727)
            self.assertTrue((Path(folder) / 'animations.lua').stat().st_size > 5000)

if __name__ == "__main__":
    unittest.main()