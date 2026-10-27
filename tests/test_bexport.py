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
        original = Path(__file__).resolve().parents[1] / 'assets_original'
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


    def test_indices_de_display_originais(self):
        original = Path(__file__).resolve().parents[1] / 'assets_original'
        if not original.is_dir():
            self.skipTest('Assets do APK indisponíveis')
        bones = frames = hidden = 0
        for path in sorted(original.rglob('*.bexportjson')):
            asset = parse_file(path, include_frames=True)
            for armature in asset['armatures']:
                by_name = {b['name']: b for b in armature['bones']}
                for bone in armature['bones']:
                    bones += 1
                    self.assertTrue(-1 <= bone['initial_display'] < len(bone['displays']))
                    self.assertIsInstance(bone['layer_order'], int)
                for animation in asset['animations']:
                    for movement in animation['movements']:
                        for track in movement['tracks']:
                            bone = by_name.get(track['bone'])
                            if not bone:
                                continue
                            for key in track['keys']:
                                frames += 1
                                self.assertTrue(-1 <= key['display_index'] < len(bone['displays']))
                                hidden += key['display_index'] == -1
        self.assertEqual(bones, 2552)
        self.assertEqual(frames, 38727)
        self.assertEqual(hidden, 18)

    def test_indice_mantem_display_vazio(self):
        original = Path(__file__).resolve().parents[1] / 'assets_original'
        file = original / 'character' / 'lizi' / 'damowangyanwu_001.bexportjson'
        if not file.is_file():
            self.skipTest('Assets do APK indisponíveis')
        data = parse_file(file, include_frames=True)
        bone = data['armatures'][0]['bones'][0]
        self.assertEqual(bone['displays'], [''])

if __name__ == '__main__':
    unittest.main()