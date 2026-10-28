#!/usr/bin/env python3
"""F27: análise estática do agendamento de morte/renascimento no ARM64 BarbarQ 1.0.1811.

Conferência de SHA256, símbolos, vtables/relocações e checkpoints do executável
original. NENHUMA rotina de jogo é executada ou transcrita integralmente.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from analisar_valores_vida import command, instructions, SYMBOL
from analisar_morte import RELOC, VTABLE_SYMBOL

ROOT = Path(__file__).resolve().parents[1]
FUNCS = {
    'Hero::update': ('_ZN4Hero6updateEf', 0xE58E84, 900),
    'Hero::reborn': ('_ZN4Hero6rebornEb', 0xE57EE0, 276),
    'Entity::reborn': ('_ZN6Entity6rebornEb', 0xE4D4DC, 4),
    'Hero::resetReviveData': ('_ZN4Hero15resetReviveDataEb', 0xE57BD0, 384),
}
CHECKS = {
    'Hero::update': [
        (0xE58F3C, 'ldrb', ('w8', '[x19, #0x1bc]')),
        (0xE58F40, 'cbz', ('w8', '0xe58f54')),
        (0xE58F44, 'ldr', ('x8', '[x19]')),
        (0xE58F48, 'ldr', ('x8', '[x8, #0x98]')),
        (0xE58F4C, 'mov', ('x0', 'x19')),
        (0xE58F50, 'blr', ('x8',)),
        (0xE59184, 'ldr', ('w8', '[x19, #0x574]')),
        (0xE5918C, 'b.eq', ('0xe591c4',)),
        (0xE59198, 'ldrb', ('w8', '[x0, #0xc4]')),
        (0xE591A4, 'sub', ('w8', 'w20', 'w8')),
        (0xE591A8, 'cmp', ('w8', '#0x41a')),
        (0xE591AC, 'b.lt', ('0xe591c4',)),
        (0xE591B0, 'ldr', ('x8', '[x19]')),
        (0xE591B4, 'ldr', ('x8', '[x8, #0x50]')),
        (0xE591B8, 'orr', ('w1', 'wzr', '#0x1')),
        (0xE591C0, 'blr', ('x8',)),
    ],
    'Hero::reborn': [
        (0xE57F08, 'and', ('w20', 'w1', '#0x1')),
        (0xE57F10, 'bl', ('Entity6reborn',)),
        (0xE57F14, 'str', ('wzr', '[x19, #0x190]')),
        (0xE57F1C, 'str', ('w8', '[x19, #0x370]')),
        (0xE57F28, 'bl', ('Hero15resetReviveData',)),
        (0xE57F3C, 'bl', ('findIndexByKey',)),
        (0xE57F4C, 'bl', ('getPlayInfoByKey',)),
        (0xE57F54, 'cbz', ('x8', '0xe57f98')),
        (0xE57F60, 'bl', ('Hero15reAddExtraSkill',)),
        (0xE57F68, 'cbz', ('w8', '0xe57f84')),
        (0xE57F80, 'bl', ('Entity8addSkill',)),
        (0xE57F94, 'bl', ('setPlayerLive',)),
        (0xE57FCC, 'bl', ('LogicEventSet9FireEvent',)),
    ],
    'Entity::reborn': [(0xE4D4DC, 'ret', ())],
    'Hero::resetReviveData': [
        (0xE57C0C, 'strb', ('wzr', '[x9, #0x4]')),
        (0xE57C10, 'tbz', ('w20', '#0x0', '0xe57c48')),
        (0xE57C20, 'bl', ('GetRandomBirthPlace',)),
        (0xE57C44, 'bl', ('b2Body12SetTransform',)),
        (0xE57C88, 'bl', ('UnRegisterAllEvent',)),
        (0xE57C9C, 'bl', ('Hero6reInit',)),
        (0xE57CAC, 'bl', ('Entity8setLevel',)),
        (0xE57D18, 'bl', ('Entity8setScore',)),
        (0xE57D20, 'str', ('w8', '[x19, #0x574]')),
    ],
}


def validate(label, decoded):
    _, start, size = FUNCS[label]
    if set(decoded) != set(range(start, start + size, 4)):
        raise ValueError(f'F27: instruções incompletas de {label}')
    for address, op, fragments in CHECKS[label]:
        actual_op, operand = decoded.get(address, ('', ''))
        if actual_op != op or not all(piece in operand for piece in fragments):
            raise ValueError(f'F27: checkpoint divergente {label}@{address:#x}: {actual_op} {operand}')


def verify_slots(vtables, relocs):
    hero = vtables.get('_ZTV4Hero')
    entity = vtables.get('_ZTV6Entity')
    if hero is None or entity is None:
        raise ValueError('F27: Hero/Entity vtable ausente')
    required = {
        'hero_update': (hero + 16 + 0x10, '_ZN4Hero6updateEf'),
        'hero_reborn': (hero + 16 + 0x50, '_ZN4Hero6rebornEb'),
        'hero_die_logic': (hero + 16 + 0x98, '_ZN4Hero8dieLogicEv'),
        'entity_reborn': (entity + 16 + 0x50, '_ZN6Entity6rebornEb'),
    }
    for key, (where, symbol) in required.items():
        if relocs.get(where) != symbol:
            raise ValueError(f'F27: slot virtual divergente {key}: {where:#x}')
    return {key: {'relocation_address':hex(where),'symbol':symbol} for key,(where,symbol) in required.items()}


def audit(library:Path, manifest:Path):
    metadata=json.loads(manifest.read_text(encoding='utf-8'))
    expected=next(row['sha256'] for row in metadata['libraries'] if row['name']=='libcocos2dcpp.so')
    with library.open('rb') as f:
        digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest != expected:
        raise ValueError('F27: biblioteca ARM64 não corresponde ao APK 1.0.1811 (SHA256)')
    text=command('readelf','-Ws',str(library))
    symbols={(name,int(addr,16),int(size)) for addr,size,name in SYMBOL.findall(text)}
    vtables={name:int(addr,16) for addr,size,name in VTABLE_SYMBOL.findall(text)}
    relocs={int(addr,16):symbol for addr,_,symbol in RELOC.findall(command('readelf','-r',str(library)))}
    slots=verify_slots(vtables,relocs)
    funcs=[]
    for label,(symbol,start,size) in FUNCS.items():
        if (symbol,start,size) not in symbols:
            raise ValueError('F27: símbolo/tamanho/endereço divergente em '+label)
        decoded=instructions(command('llvm-objdump','-d',f'--start-address=0x{start:x}',f'--stop-address=0x{start+size:x}',str(library)))
        validate(label,decoded)
        funcs.append({'name':label,'address':hex(start),'instructions':len(decoded),'checks':len(CHECKS[label])})
    return {
        'phase':27,'apk_version':'1.0.1811','library_sha256':digest,
        'functions':funcs,'total_instructions':sum(x['instructions'] for x in funcs),
        'total_checks':sum(x['checks'] for x in funcs),'virtual_slots':slots,
        'facts':{
            'death_schedule':'Hero::update lê +0x1bc; quando não zero, chama método virtual +0x98 (Hero::dieLogic pela vtable).',
            'respawn_call':'O trecho final de Hero::update possui uma chamada virtual +0x50 (Hero::reborn pela vtable), condicionada por verificação de marco de tempo, estado do BattleManager e valor +0x574.',
            'respawn_flag':'A chamada no trecho de Hero::update passa true para o argumento bool de Hero::reborn; não é prova de intervalo em segundos.',
            'reborn':'Hero::reborn chama Entity::reborn (ret puro), zera +0x190, restaura identificador de atacante +0x370 para -1, executa resetReviveData e emite evento.',
            'reset':'resetReviveData só chama GetRandomBirthPlace/Box2D::SetTransform quando o argumento bool está ativo. Executa reInit, setLevel e setScore em caminhos confirmados.',
            'live':'PlayerInfoManager::setPlayerLive(true) é chamado se o registro do jogador existir; ausência do registro pula esse ramo.',
        },
        'limits':'Não se afirma segundos de respawn, tempo exato de animações, rota de rede, proteção de spawn, regra integral dos modos, HP final nem que o leitor Lua reproduza reborn nativo.',
    }


def lua_catalog(report):
    rows=['-- F27: metadados validados; nao executa morte/respawn reais','return {',
          '  version="1.0.1811",','  total_instructions=%d,'%report['total_instructions'],
          '  total_checks=%d,'%report['total_checks'],'  flag_offset="0x1bc",',
          '  die_logic_virtual_offset="0x98",','  respawn_virtual_offset="0x50",',
          '  source="Hero::update,Hero::reborn,Hero::resetReviveData",',
          '  functions={']
    for f in report['functions']:
        rows.append('    {name=%s,address=%s,instructions=%d,checks=%d},'%
                    (json.dumps(f['name']),json.dumps(f['address']),f['instructions'],f['checks']))
    rows.extend(['  },','}'])
    return '\n'.join(rows)+'\n'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    parser.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    parser.add_argument('--json',type=Path,default=ROOT/'reports/reborn_flow.json')
    parser.add_argument('--lua',type=Path,default=ROOT/'reports/reborn_flow.lua')
    args=parser.parse_args()
    data=audit(args.library,args.manifest)
    args.json.parent.mkdir(parents=True,exist_ok=True)
    args.lua.parent.mkdir(parents=True,exist_ok=True)
    args.json.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.lua.write_text(lua_catalog(data),encoding='utf-8')
    print('F27:',data['total_instructions'],'instruções,',data['total_checks'],'checkpoints,',len(data['functions']),'funções')
if __name__=='__main__': main()
