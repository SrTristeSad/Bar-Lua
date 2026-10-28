#!/usr/bin/env python3
"""F31: prova a linhagem HeroConfig+0x48 -> Hero+0x328 -> movimento.

Apenas BarbarQ 1.0.1811 (SHA fixado pelo manifesto). Identifica também
ValueType 19 como leitura de velocidade; preserva nomes desconhecidos.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
from analisar_esquema_heroi import audit as audit_schema, CHECKS as PRIOR_CHECKS
from analisar_valores_vida import command, instructions, SYMBOL
from analisar_movimento import read_float_va
from catalogar_niveis import HERO_TABLE

ROOT=Path(__file__).resolve().parents[1]
FUNCTIONS={
    'Hero::move_update(float)':('_ZN4Hero11move_updateEf',0xe585a8,240),
    'Hero::setSpeed(int)':('_ZN4Hero8setSpeedEi',0xe59844,8),
}
CHECKS={
    'Hero::move_update(float)':[
        (0xe585cc,'ldr',('s0','[x19, #0x328]')),
        (0xe585d4,'ldr',('s1','[x8, #0x98]')),
        (0xe585dc,'fdiv',('s10','s0','s1')),
        (0xe58600,'ldr',('s0','[x19, #0xd8]')),
        (0xe58624,'ldr',('s0','[x19, #0xdc]')),
        (0xe58684,'b',('Entity4moveEff',)),
    ],
    'Hero::setSpeed(int)':[
        (0xe59844,'str',('w1','[x0, #0x328]')),
        (0xe59848,'ret',()),
    ]
}
# De Hero::init: todos os campos permanecem mapeados, sem nomes inventados.
DESTINATIONS={
    '0x38':['0xc0'], '0x3c':['0x32c'],'0x40':['0x330'],
    '0x44':['0x314','0x310'],'0x48':['0x328','0xe0'],
    '0x4c':['0x31c','0x318'],'0x50':['0x1b8'],'0x54':['0x184'],
}

def validate_checks(decoded,checks):
    for addr,op,parts in checks:
        actual,operands=decoded.get(addr,('',''))
        if actual != op or not all(piece in operands for piece in parts):
            raise ValueError(f'F31: instrucao divergente 0x{addr:x}: {actual} {operands}')

def audit(library:Path,manifest:Path,table:Path):
    schema=audit_schema(library,manifest,table)  # SHA, loader, enum e init revalidados.
    symbols={(name,int(addr,16),int(size)) for addr,size,name in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    found=[]
    for name,(mangled,addr,size) in FUNCTIONS.items():
        if (mangled,addr,size) not in symbols:
            raise ValueError('F31: simbolo ausente: '+name)
        decoded=instructions(command('llvm-objdump','-d',f'--start-address=0x{addr:x}',f'--stop-address=0x{addr+size:x}',str(library)))
        if set(decoded)!=set(range(addr,addr+size,4)):
            raise ValueError('F31: funcao incompleta: '+name)
        validate_checks(decoded,CHECKS[name])
        found.append({'name':name,'address':hex(addr),'instructions':len(decoded),'checks':len(CHECKS[name])})
    by_type={record['value_type']:record for record in schema['value_types']}
    if by_type[19]['hero_offset']!='0x328':
        raise ValueError('F31: ValueType 19 nao acessa campo de velocidade')
    if by_type[5]['hero_offset']!='0x314' or by_type[11]['hero_offset']!='0x310':
        raise ValueError('F31: referencias de HP incompatíveis')
    # Correspondencia dos seis pares de cópias confirmada na auditoria F29/F30.
    # A velocidade aparece tambem em Hero+0xe0; nao assumir semantica de e0.
    with library.open('rb') as f:
        binary=f.read()
    divisor=read_float_va(binary,0x1e98098)
    if divisor!=100.0:
        raise ValueError('F31: divisor de movimento inesperado')
    slots=[]
    for offset,targets in DESTINATIONS.items():
        slots.append({'config_offset':offset,'hero_offsets':targets,
                      'meaning':'HP inicial' if offset=='0x44' else
                      'velocidade-base' if offset=='0x48' else 'nao identificado',
                      'confirmed':offset in ('0x44','0x48')})
    return {
        'phase':31,'apk_version':'1.0.1811','library_sha256':schema['elf_sha256'],
        'config_sha256':schema['config_sha256'],
        'verified_function_count':len(schema['functions'])+len(found),
        'verified_instruction_count':schema['total_instructions']+sum(f['instructions'] for f in found),
        'additional_checks':sum(f['checks'] for f in found),
        'functions':schema['functions']+found,
        'config_slots':slots,
        'confirmed_hp_slot':'0x44','confirmed_speed_slot':'0x48',
        'speed_hero_offset':'0x328','speed_value_type':19,'speed_divisor':divisor,
        'barbarian_level1_raw_speed':schema['example_barbarian']['210001']['0x48'],
        'barbarian_level1_movement_component':schema['example_barbarian']['210001']['0x48']/divisor,
        'limitations':[
            'Movimento usa velocidade+0x328 apenas quando estado interno permite; soma componente secundario+0xd8 e direcoes.',
            'A unidade exata, tempo de integracao e sincronismo de rede nao estao reconstruidos.',
            'Nao inferir ataque ou defesa a partir dos demais seis slots.',
            'Mapeamento vale apenas para BarbarQ ARM64 1.0.1811.',
        ],
    }

def lua_report(data):
    out=['-- F31: atribuição estática verificada; dados de configuração do APK não incluídos.',
         'return {phase=31,confirmed_hp_slot="0x44",confirmed_speed_slot="0x48",',
         f'  speed_hero_offset="0x328",speed_value_type=19,speed_divisor={data["speed_divisor"]:.1f},',
         f'  verified_instruction_count={data["verified_instruction_count"]},',
         '  config_slots={']
    for slot in data['config_slots']:
        off=','.join('"'+o+'"' for o in slot['hero_offsets'])
        meaning=json.dumps(slot['meaning'],ensure_ascii=False)
        out.append(f'    {{slot="{slot["config_offset"]}",hero_offsets={{{off}}},meaning={meaning}}},')
    return '\n'.join(out+['  },','}',''])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    ap.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    ap.add_argument('--table',type=Path,default=ROOT/'assets_original/configdata'/HERO_TABLE)
    ap.add_argument('--json',type=Path,default=ROOT/'reports/hero_semantics.json')
    ap.add_argument('--lua',type=Path,default=ROOT/'reports/hero_semantics.lua')
    args=ap.parse_args()
    result=audit(args.library,args.manifest,args.table)
    args.json.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.lua.write_text(lua_report(result),encoding='utf-8')
    print(f'F31: {result["verified_instruction_count"]} instrucoes em {result["verified_function_count"]} funcoes; 0x48 velocidade-base confirmado, ValueType=19')

if __name__=='__main__':main()
