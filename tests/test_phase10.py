"""Auditoria dos recursos de botões e referências de subcenas no CSB original."""
import shutil
import subprocess
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from csb import parse_file
ROOT=Path(__file__).resolve().parents[1]

class ScenePhase10Tests(unittest.TestCase):
    def test_subcenas_e_estados_do_apk(self):
        files=sorted((ROOT/'assets_original').rglob('*.csb'))
        if not files:self.skipTest('Recursos originais não disponíveis')
        self.assertEqual(len(files),560)
        paths={p.relative_to(ROOT/'assets_original').as_posix().lower() for p in files}
        counts=dict(project=0,linked=0,buttons=0,normal=0,pressed=0,disabled=0)
        for file in files:
            doc=parse_file(file)
            def inspect(node):
                if node['class']=='Button':
                    counts['buttons']+=1
                    for state,resource in node.get('button_states',{}).items():
                        counts[state]+=1
                        self.assertTrue(resource['path'])
                if node['class']=='ProjectNode':
                    counts['project']+=1
                    path=node.get('project_file','').lower()
                    if path in paths:counts['linked']+=1
                for child in node['children']:inspect(child)
            inspect(doc['root'])
        self.assertEqual(counts,dict(project=1005,linked=985,buttons=2909,normal=2313,pressed=612,disabled=956))

    def test_navegador_lua(self):
        exe=next((shutil.which(x) for x in ('lua','luajit','luatex','luahbtex') if shutil.which(x)),None)
        if exe is None:self.skipTest('Lua não instalado')
        command=[exe]+(['--luaonly'] if Path(exe).name in ('luatex','luahbtex') else [])+['tests/test_scene_navigation.lua']
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('FASE10 OK',result.stdout)
