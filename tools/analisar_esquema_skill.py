#!/usr/bin/env python3
"""F39: checagem de carregamento HeroSkillConfig e referências ao ataque básico.

Não interpreta tokens posicionais como vetores sem comprovação de seu layout.
O código e o relatório não contêm texto ou linhas proprietárias de configuração.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from analisar_valores_vida import SYMBOL, command, instructions
from analisar_esquema_heroi import check
from catalogar_habilidades import parse_table

ROOT=Path(__file__).resolve().parents[1]
NAME='_ZN6config5skill15HeroSkillConfig4loadERN3tms5xconf8DataLineE'
ADDRESS=0x152e3e8
SIZE=1528
KEY_CHECKS=[
    (0x152e420,'mov',('x0','x20')),
    (0x152e424,'bl',('decodeString',)),
    (0x152e780,'mov',('x0','x20')),
    (0x152e784,'bl',('hasObject',)),
    (0x152e7c8,'bl',('decodeInt',)),
    (0x152e7d0,'ldr',('[x21, #0xb0]',)),
    (0x152e7f0,'bl',('append',)),
    (0x152e830,'bl',('decodeInt',)),
    (0x152e854,'bl',('decodeInt',)),
    (0x152e868,'ldr',('[x21, #0xd0]',)),
    (0x152e888,'bl',('append',)),
    (0x152e8c8,'bl',('decodeInt',)),
    (0x152e8ec,'bl',('decodeInt',)),
    (0x152e8f4,'ldr',('[x21, #0xe8]',)),
    (0x152e914,'bl',('append',)),
    (0x152e954,'bl',('decodeInt',)),
    (0x152e978,'bl',('decodeInt',)),
    (0x152e98c,'str',('[x19, #0x100]',)),
]


def record_tail(payload: str) -> dict:
    """Mostra tokens finais sem dizer que correspondem a condições/funções."""
    terms=payload.split()
    if len(terms)<5 or not all(re.fullmatch(r'-?\d+',t) for t in terms[-4:]):
        raise ValueError('F39: sufixo da habilidade incompatível')
    return {'token_count':len(terms), 'last_four_numeric':[int(x) for x in terms[-4:]],
            'first_numeric':int(terms[0])}


def find_occurrences(folder:Path, skill_id:int) -> list:
    # Só contagens em arquivos de configuração. Não exponha descrições ou linhas.
    pattern=re.compile(rb'(?<!\d)'+str(skill_id).encode()+rb'(?!\d)')
    output=[]
    for file in sorted(folder.glob('config.*.txt')):
        matches=len(pattern.findall(file.read_bytes()))
        if matches:
            output.append({'table':file.name,'token_occurrences':matches})
    return output


def audit(root:Path=ROOT)->dict:
    library=root/'lib/arm64-v8a/libcocos2dcpp.so'
    with library.open('rb') as f: sha=hashlib.file_digest(f,'sha256').hexdigest()
    prev=json.loads((root/'reports/skill_condition_gate.json').read_text('utf8'))
    if prev['phase']!=38 or prev['elf_sha256']!=sha:
        raise ValueError('F39: ELF diferente da auditoria F38')
    symbols={(name,int(va,16),int(sz)) for va,sz,name in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    if (NAME,ADDRESS,SIZE) not in symbols:
        raise ValueError('F39: função carregadora não encontrada')
    ops=instructions(command('llvm-objdump','-d',f'--start-address=0x{ADDRESS:x}',f'--stop-address=0x{ADDRESS+SIZE:x}',str(library)))
    if set(ops)!=set(range(ADDRESS,ADDRESS+SIZE,4)):
        raise ValueError('F39: desmontagem incompleta')
    for addr,opcode,parts in KEY_CHECKS:
        check('HeroSkillConfig::load',ops,addr,opcode,parts)
    cfg=root/'assets_original/configdata'
    data=(cfg/'config.skill.heroskillconfig.txt').read_bytes()
    binds=(cfg/'config.skill.functionbindskill.txt').read_bytes()
    catalog=json.loads((root/'reports/skill_catalog_summary.json').read_text('utf8'))
    for key,raw in [('heroskillconfig',data),('functionbindskill',binds)]:
        if hashlib.sha256(raw).hexdigest()!=catalog['table_sha256'][key]:
            raise ValueError('F39: tabela divergente: '+key)
    skills=parse_table(data,'heroskillconfig')
    links=parse_table(binds,'functionbindskill')
    if links[10039]['payload'].split()!=['1','2','4010020']:
        raise ValueError('F39: vínculo de botão mudou')
    basic=skills[4010020]
    tail=record_tail(basic['payload'])
    if tail['last_four_numeric']!=[10050,0,0,-1]:
        raise ValueError('F39: sequência final do ataque básico mudou')
    return {
      'phase':39,'apk_version':'1.0.1811','elf_sha256':sha,
      'function':'config::skill::HeroSkillConfig::load','address':hex(ADDRESS),
      'function_bytes':SIZE,'verified_instructions':len(ops),'checkpoints':len(KEY_CHECKS),
      'native_fields':{
        'first_vector':'HeroSkillConfig+0xB0','second_vector':'HeroSkillConfig+0xD0',
        'third_vector':'HeroSkillConfig+0xE8','enhancement_pointer':'HeroSkillConfig+0x100',
        'optional_object':'HeroSkillConfig+0xA8'},
      'table_sha256':catalog['table_sha256']['heroskillconfig'],
      'records':len(skills),
      'binding':{'id':10039,'button':2,'skill_id':4010020},
      'basic_skill':{'id':4010020,'tail':tail, 'condition_lists_verified':False,
                     'direct_damage_chain_verified':False},
      'token_occurrences':find_occurrences(cfg,4010020),
      'limits':[
         'A carga nativa confirma tres vetores e um ponteiro de melhoria; o esquema textual de todas as colunas ainda não foi determinado.',
         'Tokens 10050,0,0,-1 constam no fim do registro; nao se atribuem automaticamente a listas de condicoes.',
         'Ocorrencia numerica em outra tabela nao prova encadeamento de execucao.',
         'Nao cria hitbox, alvo, dano nem modificação da cena.'
      ]
    }


def lua_report(data:dict)->str:
    tables=data['token_occurrences']
    out=['-- F39: metadados de auditoria, sem strings proprietarias do APK.', 'return {',
         '  phase=39,gameplay_enabled=false,',
         '  skill_id=4010020,button=2,condition_lists_verified=false,',
         '  instructions='+str(data['verified_instructions'])+',checks='+str(data['checkpoints'])+',',
         '  record_count='+str(data['records'])+',',
         '  tail={10050,0,0,-1},',
         '  fields={"0xB0","0xD0","0xE8","0x100"},',
         '  occurrences={']
    for row in tables:
        out.append('    {table="'+row['table']+'",count='+str(row['token_occurrences'])+'},')
    out+=['  }','}','']
    return '\n'.join(out)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=ROOT)
    ap.add_argument('--json',type=Path)
    ap.add_argument('--lua',type=Path)
    args=ap.parse_args()
    r=audit(args.root)
    j=args.json or args.root/'reports/hero_skill_schema.json'
    l=args.lua or args.root/'reports/hero_skill_schema.lua'
    j.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    l.write_text(lua_report(r),encoding='utf8')
    print('F39: ',r['verified_instructions'],'instrucoes',r['checkpoints'],'checks',
          len(r['token_occurrences']),'tabelas com ocorrencias')

if __name__=='__main__':main()
