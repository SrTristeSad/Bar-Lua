#!/usr/bin/env python3
"""F26: verifica onDied, dieLogic e o slot virtual no ELF BarbarQ 1.0.1811.

Inspeciona apenas instruções/relocações presentes no binário fornecido.
Não executa, injeta ou traduz o código nativo.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from analisar_valores_vida import command, instructions, SYMBOL

ROOT = Path(__file__).resolve().parents[1]
FUNCS = {
    'Hero::addHurtFromEnemy': ('_ZN4Hero16addHurtFromEnemyEiib', 0xE57678, 356),
    'Entity::onDied': ('_ZN6Entity6onDiedEv', 0xE4B554, 12),
    'Entity::dieLogic': ('_ZN6Entity8dieLogicEv', 0xE4D1F8, 740),
    'Hero::dieLogic': ('_ZN4Hero8dieLogicEv', 0xE5988C, 400),
}
CHECKS = {
    'Hero::addHurtFromEnemy': [
        (0xE576AC,'ldr', ('w23','[x20, #0x314]')),
        (0xE576D0,'str', ('wzr','[x20, #0x314]')),
        (0xE576D4,'str', ('w22','[x20, #0x370]')),
        (0xE576D8,'ldr', ('x8','[x8, #0x48]')),
        (0xE576E0,'blr', ('x8',)),
    ],
    'Entity::onDied': [
        (0xE4B554,'orr', ('w8','wzr','#0x1')),
        (0xE4B558,'strb', ('w8','[x0, #0x1bc]')),
        (0xE4B55C,'ret', ()),
    ],
    'Entity::dieLogic': [
        (0xE4D288,'orr', ('w1','wzr','#0x8')),
        (0xE4D298,'bl', ('Entity8addState',)),
        (0xE4D2A0,'bl', ('Entity10clearChain',)),
        (0xE4D2C8,'ldr', ('w1','[x19, #0x30]')),
        (0xE4D2CC,'strb', ('wzr','[x19, #0x1bc]')),
        (0xE4D2D0,'strb', ('wzr','[x19, #0x2e8]')),
        (0xE4D2E0,'bl', ('PlayerInfoManager13setPlayerLive',)),
    ],
    'Hero::dieLogic': [
        (0xE598B8,'bl', ('Entity8dieLogic',)),
        (0xE598C4,'bl', ('CSkillRandom9OnHeroDie',)),
        (0xE598D8,'bl', ('setRandomSkillsByKey',)),
        (0xE59938,'bl', ('getBattleData',)),
        (0xE59944,'add', ('w8','w8','#0x1')),
        (0xE5996C,'fmov', ('s1','#0.75000000')),
        (0xE59970,'fmul', ('s0','s0','s1')),
        (0xE59974,'fcvtzs', ('w24','s0')),
        (0xE5997C,'mov', ('x0','x19')),
        (0xE59984,'bl', ('Entity8setScore',)),
        (0xE59994,'bl', ('setPlayScoreByKey',)),
        (0xE599A4,'bl', ('setPlayOldScoreByKey',)),
        (0xE599B4,'bl', ('onKDAChange',)),
        (0xE599F0,'bl', ('LogicEventSet9FireEvent',)),
    ]
}
RELOC = re.compile(r'^\s*([0-9a-f]+)\s+[0-9a-f]+\s+R_AARCH64_ABS64\s+([0-9a-f]+)\s+(\S+)', re.M)
VTABLE_SYMBOL = re.compile(r'^\s*\d+:\s*([0-9a-f]+)\s+(\d+)\s+OBJECT\s+\w+\s+DEFAULT\s+\d+\s+(\S+)', re.M)


def verify_function(label, insns):
    _, va, length = FUNCS[label]
    expected = set(range(va, va + length, 4))
    if set(insns) != expected:
        raise ValueError('F26: instruções faltando ou excedentes em ' + label)
    for va, opcode, parts in CHECKS[label]:
        actual_op, operand_text = insns.get(va, ('',''))
        if actual_op != opcode or not all(s in operand_text for s in parts):
            raise ValueError(f'F26: checkpoint divergente 0x{va:x} em {label}: {actual_op} {operand_text}')


def resolve_virtual(vtables, relocations):
    """Itanium C++ ABI: vptr = vtable + 16; ldr [vptr+0x48] = vtable+0x58."""
    result = {}
    for cls, virtual_symbol, logic_symbol in (
        ('Hero','_ZN6Entity6onDiedEv','_ZN4Hero8dieLogicEv'),
        ('Entity','_ZN6Entity6onDiedEv','_ZN6Entity8dieLogicEv')):
        start = vtables.get('_ZTV'+str(len(cls))+cls)
        if start is None:
            raise ValueError('F26: vtable ausente: ' + cls)
        immediate = start + 16 + 0x48
        if relocations.get(immediate) != virtual_symbol:
            raise ValueError('F26: slot virtual não corresponde a onDied: '+cls)
        # dieLogic occupies different slot from the immediate callback.
        downstream = start + 16 + 0x98
        if relocations.get(downstream) != logic_symbol:
            raise ValueError('F26: slot distinto de dieLogic não encontrado: '+cls)
        result[cls] = {
            'vtable':hex(start), 'vptr_offset':'0x10',
            'damage_callback_offset':'0x48','damage_callback_relocation':hex(immediate),
            'damage_callback_symbol':virtual_symbol,
            'die_logic_offset':'0x98', 'die_logic_relocation':hex(downstream),
            'die_logic_symbol':logic_symbol,
        }
    return result


def audit(library:Path, manifest:Path):
    manifest_data=json.loads(manifest.read_text(encoding='utf-8'))
    reference=next(item['sha256'] for item in manifest_data['libraries'] if item['name']=='libcocos2dcpp.so')
    with library.open('rb') as fd:
        digest=hashlib.file_digest(fd,'sha256').hexdigest()
    if digest!=reference:
        raise ValueError('F26: SHA256 inválido: não é o ELF original BarbarQ 1.0.1811')
    symtext=command('readelf','-Ws',str(library))
    symbols={(name,int(addr,16),int(size)) for addr,size,name in SYMBOL.findall(symtext)}
    vtables={name:int(addr,16) for addr,size,name in VTABLE_SYMBOL.findall(symtext)}
    relocations={int(addr,16):symbol for addr,_,symbol in RELOC.findall(command('readelf','-r',str(library)))}
    slots=resolve_virtual(vtables,relocations)
    functions=[]
    for label,(symbol,start,length) in FUNCS.items():
        if (symbol,start,length) not in symbols:
            raise ValueError('F26: assinatura de símbolo divergente: '+label)
        insns=instructions(command('llvm-objdump','-d',f'--start-address=0x{start:x}',f'--stop-address=0x{start+length:x}',str(library)))
        verify_function(label,insns)
        functions.append({'name':label,'address':hex(start),'instructions':len(insns),'checks':len(CHECKS[label])})
    return {
        'phase':26,'apk_version':'1.0.1811','library_sha256':digest,
        'functions':functions,'total_instructions':sum(f['instructions'] for f in functions),
        'total_checks':sum(f['checks'] for f in functions),
        'virtual_slots':slots,
        'observations':{
            'first_on_died':'A chamada virtual imediata por dano fatal usa o offset +0x48 e resolve Entity::onDied, inclusive na vtable Hero.',
            'on_died':'Entity::onDied apenas define o byte +0x1bc como 1. Não executa sozinho a lógica da morte.',
            'die_logic':'Entity::dieLogic limpa cadeia de habilidades, altera estado e marca jogador não vivo; Hero::dieLogic acrescenta limpeza de skills aleatórias, estatísticas, redução de score e evento.',
            'score_core':'Hero::dieLogic calcula perda truncando para zero 75% da diferença entre pontuação atual e pontuação antiga antes de gravar a nova pontuação.',
            'score_scope':'Modelo apenas para pontuação inteira não negativa com pontuação anterior <= atual; sem reproduzir regras de modo, modificadores, morte ou eventos.',
        },
        'limits':'Não está confirmado quem agenda/chama dieLogic após onDied, nem o ciclo completo de animação de morte, respawn, recompensas ou dano em batalha.',
    }


def lua_catalog(report):
    lines=['-- F26: dados estáticos auditados do ELF; sem executar morte ou combate', 'return {', '  version="1.0.1811",',
           '  total_instructions=%d,'%report['total_instructions'], '  total_checks=%d,'%report['total_checks'],
           '  first_callback="Entity::onDied",','  callback_flag="0x1bc",',
           '  hero_die_logic="Hero::dieLogic",','  score_fraction=0.75,','  functions={']
    for f in report['functions']:
        lines.append('    {name=%s,address=%s,instructions=%d,checks=%d},' %
                     (json.dumps(f['name']),json.dumps(f['address']),f['instructions'],f['checks']))
    lines.extend(['  },','}'])
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    p.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    p.add_argument('--report',type=Path,default=ROOT/'reports/death_flow.json')
    p.add_argument('--lua',type=Path,default=ROOT/'reports/death_flow.lua')
    a=p.parse_args()
    report=audit(a.library,a.manifest)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.lua.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    a.lua.write_text(lua_catalog(report),encoding='utf-8')
    print('F26:',len(report['functions']),'funções,',report['total_instructions'],'instruções,',report['total_checks'],'checkpoints, slot virtual confirmado')
if __name__=='__main__': main()
