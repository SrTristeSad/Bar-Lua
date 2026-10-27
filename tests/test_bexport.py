"""Testes das animações binárias com casos inválidos e APK opcional."""
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
from bexport import BExportError, parse_bytes, parse_file

class AnimationParserTests(unittest.TestCase):
    def test_arquivo_vazio(self):
        with self.assertRaises(BExportError):
            parse_bytes(b'')

    def test_ponteiro_invalido(self):
        with self.assertRaises(BExportError):
            parse_bytes(b'\xff' * 100)

    def test_parser_de_toda_colecao_opcional(self):
        original = Path(__file__).resolve().parents[2] / 'barbarq_lua_fase1' / 'assets_original'
        if not original.is_dir():
            self.skipTest('APK extraído indisponível (teste de integração opcional)')
        files = sorted(original.rglob('*.bexportjson'))
        self.assertEqual(len(files), 1079)
        movements = tracks = keys = 0
        for path in files:
            data = parse_file(path, include_frames=True)
            self.assertEqual(data['version'], 2)
            self.assertTrue(data['armatures'])
            for animation in data['animations']:
                for move in animation['movements']:
                    movements += 1
                    for track in move['tracks']:
                        tracks += 1
                        frames = track['keys']
                        self.assertEqual(track['key_count'], len(frames))
                        indices = [k['at'] for k in frames]
                        self.assertEqual(indices, sorted(indices))
                        self.assertTrue(all(index <= move['duration'] for index in indices))
                        keys += len(frames)
        self.assertEqual((movements, tracks, keys), (2657, 7452, 38727))

if __name__ == '__main__':
    unittest.main()