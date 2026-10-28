#!/usr/bin/env python3
"""F28 — checkpoints da reinicialização de herói do BarbarQ ARM64 1.0.1811.

Não executa código do jogo, nem supõe que os campos identificados tenham
interpretação de HP/velocidade sem análise de uso. Apenas índices e operações.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from analisar_valores_vida import command, instructions, SYMBOL

ROOT=Path(__file__).resolve().parents[1]
FUNCTIONS={
    'Hero::reInit':('_ZN4Hero6reInitEib',0xE569F0,1432),
    'Hero::InitSkillAndAttri':('_ZN4Hero17InitSkillAndAttriERKN6Entity11DataForInitE',0xE57810,184),
    'Hero::PlayerRestartGame':('_ZN4Hero17PlayerRestartGameEv',0xE57980,172),
}
# Endereço, opcode, fragmentos presentes nos operandos ARM64.
CHECKS={
 'Hero::reInit':[
    (0xE56A0C,'mov',('w23','w2')),
    (0xE56A10,'mov',('w22','w1')),
    (0xE56A2C,'mov',('w21','#0x2710')),
    (0xE56A30,'madd',('w8','w22','w21','w8')),
    (0xE56A38,'add',('w20','w8','w25')),
    (0xE56A44,'bl',('getConfById',)),
    (0xE56A54,'madd',('w8','w8','w21','w9')),
    (0xE56A64,'bl',('getConfById',)),
    (0xE56A6C,'tbz',('w23','#0x0','0xe56ae8')),
    (0xE56AD8,'bl',('Hero4init',)),
    (0xE56AE0,'bl',('ReimportWithBringData',)),
    (0xE56AF0,'bl',('Entity8setLevel',)),
    (0xE56AF4,'ldr',('w8','[x20, #0x38]')),
    (0xE56AF8,'ldr',('w9','[x21, #0x38]')),
    (0xE56B04,'sub',('w8','w8','w9')),
    (0xE56B0C,'str',('w8','[x19, #0xc0]')),
    (0xE56B10,'ldr',('w8','[x20, #0x3c]')),
    (0xE56B24,'str',('w8','[x19, #0x32c]')),
    (0xE56B28,'ldr',('w8','[x20, #0x40]')),
    (0xE56B38,'str',('w8','[x19, #0x330]')),
    (0xE56B3C,'ldp',('w8','w9','[x20, #0x44]')),
    (0xE56B40,'ldp',('w10','w11','[x21, #0x44]')),
    (0xE56B5C,'str',('w10','[x19, #0x328]')),
    (0xE56B80,'str',('q0','[x19, #0x310]')),
    (0xE56B84,'str',('w9','[x19, #0xe0]')),
    (0xE56B88,'cbz',('w8','0xe56bc4')),
    (0xE56BAC,'ldr',('w8','[x8, #0x10]')),
    (0xE56BC0,'str',('w8','[x19, #0x20c]')),
    (0xE56BC4,'ldr',('x8','[x20, #0x88]')),
    (0xE56C1C,'ldr',('w8','[x20, #0x50]')),
    (0xE56C34,'str',('w8','[x19, #0x1b8]')),
    (0xE56C68,'bl',('wilds_util5split',)),
    (0xE56C78,'bl',('wilds_util5split',)),
    (0xE56DA8,'bl',('CreateSkillBySkillConfigId',)),
    (0xE56DB8,'bl',('Entity8addSkill',)),
    (0xE56E00,'bl',('LogicEventSet9FireEvent',)),
 ],
 'Hero::InitSkillAndAttri':[
    (0xE57820,'strb',('w10','[x0, #0x44c]')),
    (0xE5782C,'str',('q0','[x8]')),
    (0xE5786C,'mov',('w9','#0x12')),
    (0xE578C0,'str',('x9','[x0, #0x460]')),
    (0xE578C4,'b',('Entity17InitSkillAndAttri',)),
 ],
 'Hero::PlayerRestartGame':[
    (0xE579A8,'str',('wzr','[x19, #0x190]')),
    (0xE579AC,'str',('w8','[x19, #0x370]')),
    (0xE579B4,'ldr',('w8','[x0, #0x7c]')),
    (0xE579B8,'str',('w8','[x19, #0x574]')),
    (0xE57A08,'bl',('LogicEventSet9FireEvent',)),
 ],
}

def validate(name, decoded):
    _,base,size=FUNCTIONS[name]
    if set(decoded)!=set(range(base,base+size,4)):
        raise ValueError('F28: instruções incompletas em '+name)
    for at,op,fragments in CHECKS[name]:
        got,operand=decoded.get(at,('',''))
        if got!=op or not all(s in operand for s in fragments):
            raise ValueError(f'F28: checkpoint divergente {name}@{at:#x}: {got} {operand}')


def audit(library:Path,manifest:Path):
    data=json.loads(manifest.read_text(encoding='utf-8'))
    expected=next(row['sha256'] for row in data['libraries'] if row['name']=='libcocos2dcpp.so')
    with library.open('rb') as f:
        digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest!=expected:
        raise ValueError('F28: SHA256 diferente do APK original 1.0.1811')
    matches={(name,int(addr,16),int(size)) for addr,size,name in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    records=[]
    for name,(symbol,address,size) in FUNCTIONS.items():
        if (symbol,address,size) not in matches:
            raise ValueError('F28: símbolo/offset/tamanho não conferem: '+name)
        decoded=instructions(command('llvm-objdump','-d',f'--start-address=0x{address:x}',
                                     f'--stop-address=0x{address+size:x}',str(library)))
        validate(name,decoded)
        records.append({'name':name,'address':hex(address),'bytes':size,
                        'instructions':len(decoded),'checks':len(CHECKS[name])})
    return {'phase':28,'apk_version':'1.0.1811','library_sha256':digest,
            'functions':records,
            'total_instructions':sum(x['instructions'] for x in records),
            'total_checks':sum(x['checks'] for x in records),
            'constants':{'config_level_stride':10000,'config_id_offset':-10000},
            'simple_delta_fields':[
                {'entity_offset':'0xc0','config_offset':'0x38'},
                {'entity_offset':'0x32c','config_offset':'0x3c'},
                {'entity_offset':'0x330','config_offset':'0x40'},
                {'entity_offset':'0x310','config_offset':'0x44'},
                {'entity_offset':'0x314','config_offset':'0x44'},
                {'entity_offset':'0x328','config_offset':'0x48'},
                {'entity_offset':'0x318','config_offset':'0x4c'},
                {'entity_offset':'0x31c','config_offset':'0x4c'},
                {'entity_offset':'0x1b8','config_offset':'0x50'},
            ],
            'facts':{
                'two_paths':'reInit(level, full) com full=true chama Hero::init e ReimportWithBringData; full=false chama setLevel e aplica diferença de configurações.',
                'config_keys':'ID da configuração do nível: baseId + level*10000 -10000; configuração anterior usa o valor do campo +0x180.',
                'skills':'Ramo diferencial divide listas numéricas da configuração em 0x58 e cria/adiciona habilidades ausentes na lista anterior.',
                'conditional':'Blocos com flag +0x204, configuração +0x88 e listas de habilidades dependem de dados não modelados.',
                'restart':'PlayerRestartGame é separado de reborn: limpa +0x190, redefine atacante +0x370, salva marco +0x574 do gerenciador e emite evento.',
            },
            'limits':'Modelo Lua reproduz apenas aritmética de campos verificados, sem semântica definitiva dos atributos, flags opcionais, skills, eventos, física ou respawn real.'}


def lua_report(data):
    lines=['-- F28: catálogo ARM64 auditado, sem execução nativa','return {',
           f'  total_instructions={data["total_instructions"]},',
           f'  total_checks={data["total_checks"]},',
           '  version="1.0.1811",','  simple_delta_fields={']
    for r in data['simple_delta_fields']:
        lines.append(f'    {{entity="{r["entity_offset"]}",config="{r["config_offset"]}"}},')
    lines.extend(['  },','  functions={'])
    for r in data['functions']:
        lines.append(f'    {{name="{r["name"]}",address="{r["address"]}",instructions={r["instructions"]}}},')
    lines.extend(['  },','}'])
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    p.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    p.add_argument('--json',type=Path,default=ROOT/'reports/reinit_flow.json')
    p.add_argument('--lua',type=Path,default=ROOT/'reports/reinit_flow.lua')
    a=p.parse_args()
    report=audit(a.library,a.manifest)
    a.json.parent.mkdir(parents=True,exist_ok=True)
    a.lua.parent.mkdir(parents=True,exist_ok=True)
    a.json.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    a.lua.write_text(lua_report(report),encoding='utf-8')
    print(f'F28: {len(report["functions"])} funções, {report["total_instructions"]} instruções, {report["total_checks"]} checkpoints')

if __name__=='__main__': main()
