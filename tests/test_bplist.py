"""Verificações do parser .bplist, com integração opcional ao APK do usuário."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "bplist.py"
spec = importlib.util.spec_from_file_location("barlua_bplist", MODULE)
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)


class AtlasBinaryTests(unittest.TestCase):
    def test_rejeita_arquivo_vazio(self):
        with self.assertRaises(parser.BPlistError):
            parser.decode_bytes(b"")

    def test_rejeita_raiz_truncada(self):
        with self.assertRaises(parser.BPlistError):
            parser.decode_bytes(b"\xff" * 60)

    def test_originais_quando_disponiveis(self):
        original = Path(__file__).resolve().parents[2] / "barbarq_lua_fase1" / "assets_original"
        if not original.is_dir():
            self.skipTest("Recursos extraídos do APK não estão presentes (opcional)")
        atlases = sorted(original.rglob("*.bplist"))
        self.assertEqual(len(atlases), 171)
        total = 0
        for path in atlases:
            result = parser.decode_file(path)
            self.assertTrue(result["texture"])
            self.assertTrue(result["size"][0] > 0)
            for frame in result["frames"]:
                self.assertTrue(frame["name"])
                self.assertGreater(frame["w"], 0)
                self.assertLessEqual(frame["x"] + frame["w"], result["size"][0])
                self.assertLessEqual(frame["y"] + frame["h"], result["size"][1])
            total += len(result["frames"])
        self.assertEqual(total, 13680)


if __name__ == "__main__":
    unittest.main()