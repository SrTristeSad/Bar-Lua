#!/usr/bin/env python3
"""F20: audita o clique de habilidade ARM64 e os ataques animados do bárbaro.
Gera apenas metadados; não publica instruções nem binários proprietários.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from bexport import parse_file

FUNCTIONS={
    'Hero::onButtonClicked(config::skill::ButtonType)': (0xe57918,104),
    'Hero::getButtonState(int) const': (0xe5b264,36),
}
PATTERNS={
    'Hero::onButtonClicked(config::skill::ButtonType)':{
        'range_guard':r'cmp\s+w1,\s*#0x11',
        'configuration_read':r'ldr\s+w9,\s*\[x8,\s*#0x3bc\]',
        'configuration_required':r'cmp\s+w9,\s*#0x1',
        'creates_configured_skill':r'bl\s+[^\n]*CreateSkillBySkillConfigId',
        'adds_skill_to_entity':r'b\s+[^\n]*Entity8addSkill',
    },
    'Hero::getButtonState(int) const':{
        'range_guard':r'cmp\s+w1,\s*#0x11',
        'state_byte_read':r'ldrb\s+w8,\s*\[x8,\s*#0x44c\]',
        'nonzero_state':r'cset\s+w0,\s*ne',
    },
}
INSTRUCTION=re.compile(r'^\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+[a-z][\w.]*\b',re.I|re.M)

def audit(so:Path, manifest:Path, animation:Path) -> dict:
    m=json.loads(manifest.read_text(encoding='utf-8'))
    expected=next(x['sha256'] for x in m['libraries'] if x['name']=='libcocos2dcpp.so')
    actual=hashlib.sha256(so.read_bytes()).hexdigest()
    if expected!=actual:raise ValueError('SHA-256 divergente da biblioteca original')
    observed={}
    for name,(addr,size) in FUNCTIONS.items():
        proc=subprocess.run(['llvm-objdump','-d',f'--start-address=0x{addr:x}',f'--stop-address=0x{addr+size:x}',str(so)],
            check=True,capture_output=True,text=True,timeout=30)
        instructions=[int(x,16) for x in INSTRUCTION.findall(proc.stdout)]
        if instructions!=list(range(addr,addr+size,4)):
            raise ValueError('Instruções ou offsets não correspondem: '+name)
        misses=[key for key,rx in PATTERNS[name].items() if not re.search(rx,proc.stdout)]
        if misses:raise ValueError('Padrão ausente: '+str(misses))
        observed[name]={'address':f'0x{addr:x}','size_bytes':size,'instructions':size//4,
                        'checks':sorted(PATTERNS[name])}
    data=parse_file(animation,include_frames=False)
    names={m['name']:m for a in data['animations'] for m in a['movements']}
    attacks={}
    for n in (1,2,3):
        variants=[]
        for d in range(5):
            name=f'attack{n}_{d}'
            if name not in names or names[name]['duration']<=0:
                raise ValueError('Animação esperada ausente: '+name)
            variants.append({'name':name,'duration_frames':names[name]['duration']})
        attacks[f'attack{n}']=variants
    return {'phase':20,'apk_version':'1.0.1811','library_sha256':actual,
            'animation_path':'character/babarian/babarian.bexportjson',
            'animation_sha256':hashlib.sha256(animation.read_bytes()).hexdigest(),
            'functions':observed,'attack_movements':attacks,
            'limits':'Ataques são nomes de movimentos. Não foi comprovado vínculo com IDs de habilidades, duração em segundos, dano, hitbox nem cooldown.'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    parser.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    parser.add_argument('--animation',type=Path,default=ROOT/'assets_original/character/babarian/babarian.bexportjson')
    parser.add_argument('--output',type=Path,default=ROOT/'reports/native_attacks.json')
    args=parser.parse_args()
    result=audit(args.library,args.manifest,args.animation)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Fase 20: 2 funções ARM64, 35 instruções, 15 variantes de animações confirmadas')
if __name__=='__main__':main()
