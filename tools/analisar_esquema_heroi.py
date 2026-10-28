#!/usr/bin/env python3
"""F30: esquema HeroConfig recuperado do *loader* real e do dispatch ValueType.

Somente enderecos/opcodes do BarbarQ ARM64 1.0.1811 com SHA-256 fixado.
Sem supor significado dos atributos que o ELF nao permite identificar.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from analisar_valores_vida import command, instructions, SYMBOL
from catalogar_niveis import EXPECTED_SHA256, HERO_TABLE, parse_hero
from catalogar_habilidades import parse_table

ROOT=Path(__file__).resolve().parents[1]
FUNCTIONS={
    'HeroConfig::load':('_ZN6config4hero10HeroConfig4loadERN3tms5xconf8DataLineE',0x1517b1c,636),
    'Hero::init':('_ZN4Hero4initEPKN6config4hero10HeroConfigERKN6Entity11DataForInitE',0xe56734,700),
    'Hero::addHurtFromEnemy':('_ZN4Hero16addHurtFromEnemyEiib',0xe57678,356),
    'Hero::getValueByType':('_ZNK4Hero14getValueByTypeEN6config5skill9ValueTypeEfPKNS1_9OperationE',0xe58af8,652),
}
SLOTS=[0x38+i*4 for i in range(8)]
# Os callbacks Decoder sao atraves da PLT; verificar cada chamada junto a cada str.
LOAD_POINTS=[(0x1517bbc+i*12,0x1517bb8+i*12,slot) for i,slot in enumerate(SLOTS)]
# Observacoes diretas de init e dano. HP corrente: 0x314; base: 0x310.
CHECKS={
    'Hero::init':[
        (0xe5679c,'str',('w8','[x19, #0x314]')),
        (0xe567a0,'str',('w8','[x19, #0x310]')),
        (0xe56798,'ldr',('w8','[x21, #0x44]')),
        (0xe56780,'ldr',('w8','[x21, #0x38]')),
        (0xe56784,'str',('w8','[x19, #0xc0]')),
        (0xe567e0,'ldr',('w11','[x21, #0x54]')),
        (0xe567e8,'str',('w11','[x19, #0x184]')),
    ],
    'Hero::addHurtFromEnemy':[
        (0xe576ac,'ldr',('w23','[x20, #0x314]')),
        (0xe576c4,'str',('w8','[x20, #0x314]')),
        (0xe576d0,'str',('wzr','[x20, #0x314]')),
    ],
    'Hero::getValueByType':[
        (0xe58b10,'sub',('w8','w1','#0x2')),
        (0xe58b14,'cmp',('w8','#0x1f')),
        (0xe58b28,'ldrsw',('[x10, x8, lsl #2]',)),
        (0xe58b34,'fdiv',('s9','s0','s1')),
        (0xe58b3c,'ldr',('s0','[x20, #0x32c]')),
        (0xe58b64,'ldr',('s0','[x20, #0x314]')),
        (0xe58b7c,'ldr',('s0','[x20, #0x310]')),
    ],
}
TABLE_BASE=0xe58d84

def check(expected,inst,addr,op,parts):
    actual,operands=inst.get(addr,('',''))
    if actual!=op or any(x not in operands for x in parts):
        raise ValueError(f'F30: divergencia em {expected} no endereco 0x{addr:x}: {actual} {operands}')


def validate_loader(decoded):
    """Prova uma chamada decodeInt -> str consecutiva em cada campo configuravel."""
    for _,call_addr,offset in LOAD_POINTS:
        str_addr=call_addr+4
        check('HeroConfig::load',decoded,call_addr,'bl',('decodeInt',))
        check('HeroConfig::load',decoded,str_addr,'str',('w0',f'[x19, #0x{offset:x}]'))
    # Ha 2 strings, 2 objetos opcionais e 3 bools no bloco posterior.
    for addr,op,parts in [
        (0x1517b50,'bl',('decodeString',)),
        (0x1517c1c,'bl',('decodeString',)),
        (0x1517c6c,'bl',('decodeString',)),
        (0x1517cb8,'bl',('hasObject',)),
        (0x1517cf4,'bl',('hasObject',)),
        (0x1517d30,'bl',('decodeBool',)),
        (0x1517d40,'bl',('decodeBool',)),
        (0x1517d50,'bl',('decodeBool',)),
        (0x1517d60,'bl',('decodeInt',)),
        (0x1517d64,'str',('w0','[x19, #0x9c]')),
    ]:
        check('HeroConfig::load',decoded,addr,op,parts)


def decode_value_types(binary:bytes,decoded):
    if TABLE_BASE+32*4>len(binary):raise ValueError('F30: tabela de despacho ausente')
    result=[]
    for i in range(32):
        rel=struct.unpack_from('<i',binary,TABLE_BASE+i*4)[0]
        target=TABLE_BASE+rel
        if not (0xe58af8<=target<0xe58d84 and target%4==0):
            raise ValueError(f'F30: destino invalido do ValueType={i+2}: {target:x}')
        op,args=decoded.get(target,('',''))
        if op=='ldr' and args.startswith('s0, [x20, #0x'):
            match=re.match(r's0, \[x20, #0x([a-f0-9]+)\]',args)
            offset='0x'+match.group(1) if match else None
        else:
            offset=None
        result.append({'value_type':i+2,'target':f'0x{target:x}',
                       'hero_offset':offset,'kind':'hero_field' if offset else
                       ('delegate_entity' if target==0xe58b44 else 'derived_value')})
    if result[3]['hero_offset']!='0x314' or result[9]['hero_offset']!='0x310':
        raise ValueError('F30: ValueType de HP nao corresponde a leitura nativa')
    return result


def audit(library:Path,manifest:Path,table:Path):
    data=json.loads(manifest.read_text('utf-8'))
    expected=next(item['sha256'] for item in data['libraries'] if item['name']=='libcocos2dcpp.so')
    with library.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest!=expected:raise ValueError('F30: hash da biblioteca diferente do APK 1.0.1811')
    raw=library.read_bytes()
    if hashlib.sha256(table.read_bytes()).hexdigest()!=EXPECTED_SHA256[HERO_TABLE]:
        raise ValueError('F30: hash da tabela de herois diferente do APK 1.0.1811')
    symbols={(name,int(addr,16),int(size)) for addr,size,name in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    results=[]; allinst={}
    for name,(mangled,start,size) in FUNCTIONS.items():
        if (mangled,start,size) not in symbols:raise ValueError('F30: simbolo ausente '+name)
        inst=instructions(command('llvm-objdump','-d',f'--start-address=0x{start:x}',f'--stop-address=0x{start+size:x}',str(library)))
        if set(inst)!=set(range(start,start+size,4)):
            raise ValueError('F30: instrucao incompleta em '+name)
        if name=='HeroConfig::load':validate_loader(inst)
        for addr,op,parts in CHECKS.get(name,[]):check(name,inst,addr,op,parts)
        results.append({'name':name,'address':hex(start),'bytes':size,'instructions':len(inst)})
        allinst[name]=inst
    types=decode_value_types(raw,allinst['Hero::getValueByType'])
    parsed=parse_table(table.read_bytes(),'hero.heroconfig')
    rows={str(k):parse_hero(parsed[k])['values'] for k in (210001,220001,230001)}
    if [rows[str(k)]['0x44'] for k in (210001,220001,230001)] != [240,240,240]:
        raise ValueError('F30: sentinela HP dos tres niveis do barbaro divergente')
    return {'phase':30,'apk_version':'1.0.1811','elf_sha256':digest,
            'config_sha256':hashlib.sha256(table.read_bytes()).hexdigest(),
            'functions':results,'total_instructions':sum(f['instructions'] for f in results),
            'slot_load_order':[f'0x{slot:x}' for slot in SLOTS],
            'confirmed_hp_slot':'0x44','hero_hp_current_offset':'0x314','hero_hp_base_offset':'0x310',
            'example_barbarian':rows,
            'value_types':types,
            'limits':'Offsets validos somente para APK 1.0.1811. ValueType IDs sao numericos; seus nomes nao foram recuperados. 0x310 contem o valor base inicial do HP; efeitos externos podem altera-lo. Sem combate integrado.'}


def lua_report(data):
    lines=['-- F30: offsets estruturais comprovados por HeroConfig::load / Hero::init / addHurt',
           'return {phase=30,confirmed_hp_slot="0x44",hp_current="0x314",hp_initial="0x310",',
           f'  total_instructions={data["total_instructions"]},',
           '  slot_load_order={'+','.join('"'+s+'"' for s in data['slot_load_order'])+'},',
           '  value_types={']
    for t in data['value_types']:
        lines.append(f'    {{id={t["value_type"]},offset={json.dumps(t["hero_offset"]) if t["hero_offset"] else "nil"},kind="{t["kind"]}"}},')
    lines+=['  },','}','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    p.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    p.add_argument('--table',type=Path,default=ROOT/'assets_original/configdata'/HERO_TABLE)
    p.add_argument('--json',type=Path,default=ROOT/'reports/hero_schema.json')
    p.add_argument('--lua',type=Path,default=ROOT/'reports/hero_schema.lua')
    args=p.parse_args()
    result=audit(args.library,args.manifest,args.table)
    args.json.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    args.lua.write_text(lua_report(result),encoding='utf-8')
    print(f'F30: {result["total_instructions"]} instrucoes, 8 campos mapeados, 32 ValueTypes; campo HP 0x44 confirmado')
if __name__=='__main__':main()
