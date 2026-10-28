from pathlib import Path
import importlib.util
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tmxprep', ROOT / 'tools/preparar_recursos.py')
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)

class TMXObjectTests(unittest.TestCase):
    def test_original_five_object_groups(self):
        all_maps = sorted((ROOT / 'assets_original').rglob('*.tmx'))
        found = {}
        for path in all_maps:
            item = prep.parse_map(path, ROOT / 'assets_original')
            count = sum(len(g['objects']) for g in item['objectgroups'])
            if count:
                found[path.stem] = (item['objectgroups'][0]['objects'][0], count)
        self.assertEqual(set(found), {f'petisland_0{i}' for i in range(1,6)})
        for item,count in found.values():
            self.assertEqual(count, 1)
            self.assertEqual((item['shape'],item['x'],item['y'],item['width'],item['height']),
                             ('rectangle',395.,138.,232.,238.))
            self.assertEqual(item['properties'], {})
    def test_no_auto_collision_flag(self):
        elem=ET.fromstring('''<map><objectgroup name="objects"><object id="12" x="7" y="9" width="15" height="11"/>
          <object id="13" x="8" y="9" width="20" height="17"><ellipse/></object></objectgroup></map>''')
        groups=prep.parse_object_groups(elem)
        self.assertEqual(groups[0]['objects'][0]['shape'], 'rectangle')
        self.assertEqual(groups[0]['objects'][1]['shape'], 'ellipse')
        self.assertNotIn('collidable', groups[0]['objects'][0])

if __name__ == '__main__':unittest.main()
