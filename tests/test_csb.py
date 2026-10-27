"""Regressões do leitor CSB FlatBuffers; sem dependências fora do stdlib."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from csb import parse_bytes, parse_file, SceneError

ROOT=Path(__file__).resolve().parents[1]

class CsbTests(unittest.TestCase):
    def test_arquivos_invalidos(self):
        for payload in (b'', b'\0'*64, b'\xFF'*128, b'\x04\x00\0\0'):
            with self.subTest(size=len(payload)), self.assertRaises(SceneError):
                parse_bytes(payload)

    def test_todos_arquivos_originais(self):
        assets=ROOT/'assets_original'
        if not assets.is_dir(): self.skipTest('APK não extraído')
        files=sorted(assets.rglob('*.csb'))
        self.assertEqual(len(files), 560)
        scenes=[parse_file(path) for path in files]
        self.assertEqual(sum(s['node_count'] for s in scenes),26612)
        self.assertEqual(sum(s['classes'].get('Button',0) for s in scenes),2909)
        self.assertEqual(sum(s['classes'].get('ImageView',0) for s in scenes),6820)
        self.assertTrue(all(s['version'] for s in scenes))

    def test_tela_setting(self):
        path=ROOT/'assets_original/gui/00_setting.csb'
        if not path.exists():self.skipTest('APK não extraído')
        scene=parse_file(path)
        self.assertEqual(scene['node_count'],227)
        self.assertEqual(scene['root']['props']['name'],'Setting')
        self.assertEqual(scene['root']['props']['size'],[960.0,540.0])
        panel=scene['root']['children'][0]
        self.assertEqual(panel['class'],'Panel')
        back=panel['children'][0]
        self.assertEqual(back['resource']['path'],'Gui/large/bg_hd_2.png')
        self.assertEqual(back['props']['name'],'_Back')
        self.assertEqual(back['props']['position'][1],270)

if __name__=='__main__':unittest.main()