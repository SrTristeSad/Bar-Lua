#!/usr/bin/env python3
"""F32: audita dano e parametro de alcance no ELF BarbarQ 1.0.1811.

Nao presume dano final, unidades de alcance ou defesa: a prova consiste
em HeroConfig::load, Hero::init, setters com nomes nativos, ValueType e reInit.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from analisar_semantica_heroi import audit as audit_previous
from analisar_esquema_heroi import check
from analisar_valores_vida import command, instructions, SYMBOL
from catalogar_niveis import HERO_TABLE

ROOT=Path(__file__).resolve().parents[1]
FUNCS={
 'Hero::setDamage(int)':('_ZN4Hero9setDamageEi',0xe59824,8),
 'Hero::setDamageScope(int)':('_ZN4Hero14setDamageScopeEi',0xe59834,8),
 'Hero::reInit(int, bool)':('_ZN4Hero6reInitEib',0xe569f0,1432),
}
CHECKS={
 'Hero::setDamage(int)':[(0xe59824,'str',('w1','[x0, #0x32c]')),(0xe59828,'ret',())],
 'Hero::setDamageScope(int)':[(0xe59834,'str',('w1','[x0, #0x330]')),(0xe59838,'ret',())],
 'Hero::reInit(int, bool)':[
  (0xe56b00,'ldr',('w11','[x19, #0x32c]')),
  (0xe56b10,'ldr',('w8','[x20, #0x3c]')),
  (0xe56b14,'ldr',('w9','[x21, #0x3c]')),
  (0xe56b18,'ldr',('w10','[x19, #0x330]')),
  (0xe56b24,'str',('w8','[x19, #0x32c]')),
  (0xe56b28,'ldr',('w8','[x20, #0x40]')),
  (0xe56b2c,'ldr',('w9','[x21, #0x40]')),
  (0xe56b38,'str',('w8','[x19, #0x330]')),
 ]
}
COPIES=[
 (0xe56788,'ldr',('w8','[x21, #0x3c]')),
 (0xe5678c,'str',('w8','[x19, #0x32c]')),
 (0xe56790,'ldr',('w8','[x21, #0x40]')),
 (0xe56794,'str',('w8','[x19, #0x330]')),
]
READS=[
 (0xe58b3c,'ldr',('s0','[x20, #0x32c]')),
 (0xe58b5c,'ldr',('s0','[x20, #0x330]')),
]

def validate(decoded, checks, label):
    for address,opcode,parts in checks:
        check(label, decoded,address,opcode,parts)


def audit(library:Path,manifest:Path,table:Path):
    previous=audit_previous(library,manifest,table)
    symbols={(name,int(addr,16),int(size)) for addr,size,name in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    verified=[]
    for label,(mangled,start,size) in FUNCS.items():
        if (mangled,start,size) not in symbols:
            raise ValueError('F32: simbolo ausente: '+label)
        decoded=instructions(command('llvm-objdump','-d',f'--start-address=0x{start:x}',f'--stop-address=0x{start+size:x}',str(library)))
        if set(decoded)!=set(range(start,start+size,4)):
            raise ValueError('F32: funcao incompleta: '+label)
        validate(decoded,CHECKS[label],label)
        verified.append({'name':label,'address':hex(start),'bytes':size,'instructions':len(decoded),'checks':len(CHECKS[label])})
    init_addr=0xe56734
    init=instructions(command('llvm-objdump','-d',f'--start-address=0x{init_addr:x}',f'--stop-address=0x{init_addr+700:x}',str(library)))
    vtype_addr=0xe58af8
    vtypes=instructions(command('llvm-objdump','-d',f'--start-address=0x{vtype_addr:x}',f'--stop-address=0x{vtype_addr+652:x}',str(library)))
    validate(init,COPIES,'Hero::init')
    validate(vtypes,READS,'Hero::getValueByType')
    by_type={x['value_type']:x for x in json.loads((ROOT/'reports/hero_schema.json').read_text('utf-8'))['value_types']}
    if by_type[2]['hero_offset']!='0x32c' or by_type[3]['hero_offset']!='0x330':
        raise ValueError('F32: dispatch ValueType 2/3 inconsistente')
    if previous['config_sha256'] != json.loads((ROOT/'reports/hero_schema.json').read_text('utf-8'))['config_sha256']:
        raise ValueError('F32: tabela de configuracao nao validada')
    slots=[]
    for entry in previous['config_slots']:
        item=dict(entry)
        if item['config_offset']=='0x3c':
            item.update(meaning='dano-base (Hero::setDamage)',confirmed=True,value_type=2)
        elif item['config_offset']=='0x40':
            item.update(meaning='parametro de alcance de dano (Hero::setDamageScope)',confirmed=True,value_type=3)
        slots.append(item)
    return {
        'phase':32,'apk_version':'1.0.1811',
        'library_sha256':previous['library_sha256'],'config_sha256':previous['config_sha256'],
        'verified_function_count':previous['verified_function_count']+len(verified),
        'verified_instruction_count':previous['verified_instruction_count']+sum(f['instructions'] for f in verified),
        'extra_checks':sum(len(x) for x in CHECKS.values())+len(COPIES)+len(READS),
        'new_functions':verified,'config_slots':slots,
        'damage':{'config_slot':'0x3c','hero_offset':'0x32c','setter':'Hero::setDamage(int)','value_type':2},
        'damage_scope':{'config_slot':'0x40','hero_offset':'0x330','setter':'Hero::setDamageScope(int)','value_type':3},
        'limits':[
            'O nome setDamage indica parametro de dano, nao a formula final aplicada ao alvo.',
            'setDamageScope confirma um parametro de escopo/alcance de dano, mas sua unidade, formato e efeito nas hitboxes nao foram recuperados.',
            'Nao identificado aqui nenhum campo de defesa.',
            'Offsets, opcodes e SHA valem apenas para ARM64 BarbarQ 1.0.1811.',
        ],
    }


def as_lua(data):
    lines=['-- F32: linhagem estatica confirmada no ELF, sem dados proprietarios de configuracao.',
           'return {phase=32,',
           f'  verified_instruction_count={data["verified_instruction_count"]},',
           f'  extra_checks={data["extra_checks"]},',
           '  damage={slot="0x3c",offset="0x32c",value_type=2,setter="Hero::setDamage(int)"},',
           '  damage_scope={slot="0x40",offset="0x330",value_type=3,setter="Hero::setDamageScope(int)"},',
           '}','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    parser.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    parser.add_argument('--table',type=Path,default=ROOT/'assets_original/configdata'/HERO_TABLE)
    parser.add_argument('--json',type=Path,default=ROOT/'reports/hero_combat_fields.json')
    parser.add_argument('--lua',type=Path,default=ROOT/'reports/hero_combat_fields.lua')
    args=parser.parse_args()
    result=audit(args.library,args.manifest,args.table)
    args.json.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    args.lua.write_text(as_lua(result),encoding='utf-8')
    print(f'F32: dano-base/escopo confirmados; {result["verified_instruction_count"]} instr. auditadas; {result["extra_checks"]} novos checks')

if __name__=='__main__':main()
