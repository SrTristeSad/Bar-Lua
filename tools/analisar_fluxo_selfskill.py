#!/usr/bin/env python3
"""F41 — relação do terceiro vetor com CFunction no BarbarQ 1.0.1811.

Escopo: inspeção estática de ELF e configurações originais fornecidas pelo usuário;
não implementa ataques, nem redistribui texto ou binários proprietários.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analisar_valores_vida import command, instructions, SYMBOL
from analisar_esquema_heroi import check
from decodificar_skill_xconf import audit as audit40, decode_absent_object_suffix
from catalogar_habilidades import parse_table

# Nome, símbolo exato, endereço ELF e tamanho, não offsets de arquivo.
FUNCTIONS={
 'CSkill::CSkill(config)':('_ZN6CSkillC1EPKN6config5skill15HeroSkillConfigE',0xe64c40,188),
 'CSkill::GetTargetEntitys':('_ZN6CSkill16GetTargetEntitysEv',0xe64f1c,152),
 'CSkill::CreateSkillBySkillConfigId':('_ZN6CSkill26CreateSkillBySkillConfigIdEP6EntityiPKNSt3__16vectorI12CSkillEntityNS2_9allocatorIS4_EEEEi',0xe650b4,320),
 'CSkill::AddFunction':('_ZN6CSkill11AddFunctionEiP9CFunctioni',0xe64fbc,120),
 'CSelfSkill::CSelfSkill':('_ZN10CSelfSkillC1EP6CSkilli',0xe6555c,596),
 'CSelfSkill::Init':('_ZN10CSelfSkill4InitERK12CSkillEntityPKNSt3__16vectorIS0_NS3_9allocatorIS0_EEEE',0xe657b0,372),
 'CSelfSkill::Update':('_ZN10CSelfSkill6UpdateEf',0xe65924,364),
 'CSelfSkill::HasFunctions':('_ZN10CSelfSkill12HasFunctionsEv',0xe65a90,16),
}
CHECKS={
 'CSkill::CSkill(config)':[
   (0xe64c94,'add',('x8','x19','#0xe8')), (0xe64c9c,'str',('x8','[x20, #0x38]')),
   (0xe64ca0,'ldr',('w8','[x19, #0xc8]')), (0xe64cc0,'str',('w8','[x20, #0x40]')),
 ],
 'CSkill::GetTargetEntitys':[
   (0xe64f2c,'ldr',('w0','[x19, #0x40]')),
   (0xe64f30,'bl',('CSelectTarget','GetSelectById')),
 ],
 'CSkill::CreateSkillBySkillConfigId':[
   (0xe65144,'ldr',('w26','[x24, #0x40]')),
   (0xe65154,'mov',('w8','#0x2742')),
   (0xe65158,'cmp',('w26','w8')),
   (0xe6516c,'bl',('CSelfSkill')),
   (0xe65180,'bl',('CMultiTargetSkill')),
 ],
 'CSkill::AddFunction':[
   (0xe64fcc,'cbz',('x2',)),
   (0xe64fe4,'bl',('CreateFunctionByFunctionId',)),
 ],
 'CSelfSkill::CSelfSkill':[
   (0xe6559c,'ldr',('x9','[x1, #0x38]')),
   (0xe655a0,'str',('x9','[x19, #0x38]')),
   (0xe65634,'ldr',('x9','[x19, #0x38]')),
   (0xe65640,'sub',('x9','x9','x8')),
   (0xe65644,'lsr',('x9','x9','#2')),
   (0xe65648,'cmp',('w9','#0x0')),
   (0xe6564c,'b.le',()),
   (0xe6566c,'ldr',('w1','[x8, x22, lsl #2]')),
   (0xe65668,'ldr',('x9','[x9, #0x18]')),
   (0xe6567c,'blr',('x9',)),
   (0xe65680,'str',('x0','[x21, x22, lsl #3]')),
 ],
 'CSelfSkill::Init':[
   (0xe6585c,'ldp',('x9','x8','[x8]')),
   (0xe65864,'lsr',('x24','x8','#2')),
   (0xe6586c,'b.lt',()),
   (0xe65898,'bl',('CFunction','SetCreatorEntity')),
   (0xe658a4,'bl',('CFunction','SetTargetEntitys')),
   (0xe658b0,'bl',('CFunction','SetEntity')),
   (0xe6590c,'cbnz',('w24',)),
 ],
 'CSelfSkill::Update':[
   (0xe65940,'ldp',('x20','x8','[x19, #0x1b0]')),
   (0xe65948,'b.eq',()),
   (0xe6596c,'blr',('x8',)),
   (0xe6597c,'blr',('x8',)),
   (0xe659e0,'ldrb',('w8','[x22, #0x58]')),
   (0xe65a00,'bl',('memmove',)),
 ],
 'CSelfSkill::HasFunctions':[
   (0xe65a90,'ldp',('x8','x9','[x0, #0x1b0]')),
   (0xe65a98,'cset',('w0','ne')),
 ],
}


def audit(root:Path=ROOT)->dict:
    root=Path(root)
    old=audit40(root) # valida hash, versão e esquema de carregamento
    library=root/'lib/arm64-v8a/libcocos2dcpp.so'
    symbols={(name,int(va,16),int(sz)) for va,sz,name in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    audited=[]
    for label,(symbol,address,size) in FUNCTIONS.items():
        if (symbol,address,size) not in symbols:
            raise ValueError(f'F41: símbolo nativo original divergente: {label}')
        ops=instructions(command('llvm-objdump','-d',f'--start-address=0x{address:x}',
            f'--stop-address=0x{address+size:x}',str(library)))
        if set(ops)!=set(range(address,address+size,4)):
            raise ValueError(f'F41: instruções incompletas: {label}')
        for va,opcode,parts in CHECKS[label]:
            check(label,ops,va,opcode,parts)
        audited.append({'name':label,'va':hex(address),'bytes':size,'instructions':size//4,
                        'checkpoints':len(CHECKS[label])})
    config=root/'assets_original/configdata'
    file=config/'config.skill.heroskillconfig.txt'
    if hashlib.sha256(file.read_bytes()).hexdigest()!=old['table_sha256']:
        raise ValueError('F41: configuração de habilidade não confere')
    rows=parse_table(file.read_bytes(),'heroskillconfig')
    function_tables={}
    combined={}
    for p in sorted(config.glob('config.skill.function*.txt')):
        name=p.stem.split('config.skill.',1)[-1]
        table=parse_table(p.read_bytes(),name)
        function_tables[name]={'records':len(table),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        for key in table:
            combined.setdefault(key,[]).append(name)
    third=[];zero=0;nonzero=0;basic=None
    examples=[]
    for key,row in rows.items():
        if ' - ' not in row['payload']:
            continue
        parsed=decode_absent_object_suffix(row['payload'])
        ids=parsed['third_vector_ids']
        third.extend(ids)
        if ids:nonzero+=1
        else:zero+=1
        if key==4010020:
            basic=parsed
        if ids and len(examples)<5:
            examples.append({'skill_id':key,'function_ids':ids[:4],
                             'function_tables':[combined.get(item,[]) for item in ids[:4]]})
    if basic is None or basic['third_vector_ids'] or basic['kind']!=10050:
        raise ValueError('F41: ataque 4010020 não corresponde ao esquema original')
    type_counts=Counter()
    for fid in third:
        for table in combined.get(fid,[]):
            type_counts[table]+=1
    unmatched={fid for fid in third if fid not in combined}
    return {
      'phase':41,'apk_version':'1.0.1811','elf_sha256':old['elf_sha256'],
      'config_sha256':old['table_sha256'],'total_native_functions':len(audited),
      'native_functions':audited,
      'verified_arm64_instructions':sum(x['instructions'] for x in audited),
      'checkpoints':sum(x['checkpoints'] for x in audited),
      'skill_records_decoded':old['records_decoded'],
      'skill_records_pending_optional_object':old['records_skipped_optional_object'],
      'skills_with_function_ids':nonzero,'skills_without_function_ids':zero,
      'third_vector_total_entries':len(third),'third_vector_distinct_ids':len(set(third)),
      'function_table_summary':function_tables,
      'function_id_occurrences_by_table':dict(sorted(type_counts.items())),
      'unmatched_distinct_function_ids':len(unmatched),
      'examples':examples,
      'basic_skill':{'id':4010020,'button_binding_id':10039,'selector_id':10050,
                     'third_vector_function_ids':[], 'instantiated_functions_from_config':0},
      'native_links':{
        'config_vector':'HeroSkillConfig+0xE8 -> CSkill+0x38',
        'constructor':'CSelfSkill::CSelfSkill percorre CSkill+0x38 e cria CFunction via método virtual +0x18',
        'init':'CSelfSkill::Init configura criador, alvos e contexto das funções instanciadas',
        'update':'CSelfSkill::Update percorre funções ativas e limpa funções inativas',
        'selector':'HeroSkillConfig+0xC8 -> CSkill+0x40 -> CSelectTarget::GetSelectById',
        'selector_branch':'CSkill::CreateSkillBySkillConfigId utiliza 10050 para CSelfSkill, outros valores para CMultiTargetSkill'},
      'limits':[
        'A terceira lista contém identificadores de funções; não é a lista de condições do criador ou dos alvos.',
        'O ataque 4010020 não instancia funções diretamente pela lista vazia; pode depender de outro mecanismo, ainda não descoberto.',
        'CSkill+0x40 é um identificador de seletor de alvos, também usado para decidir CSelfSkill/CMultiTargetSkill; não é um tipo independente de habilidade.',
        'A associação de um ID a uma tabela de funções não demonstra quando sua ação é executada.',
        'Nenhum ataque, dano, tempo de recarga ou respawn foi integrado ao gameplay.'
      ]}


def lua_report(d:dict)->str:
    b=d['basic_skill']; tables=d['function_id_occurrences_by_table']
    safe=[(name,n) for name,n in sorted(tables.items(),key=lambda i:(-i[1],i[0]))][:8]
    lines=['-- F41: auditoria de funções da habilidade; modelo de pesquisa sem gameplay.',
      'return {phase=41,gameplay_enabled=false,verified=true,',
      f'  functions={d["total_native_functions"]},instructions={d["verified_arm64_instructions"]},checks={d["checkpoints"]},',
      f'  decoded={d["skill_records_decoded"]},pending={d["skill_records_pending_optional_object"]},',
      f'  with_functions={d["skills_with_function_ids"]},without_functions={d["skills_without_function_ids"]},',
      f'  entries={d["third_vector_total_entries"]},distinct={d["third_vector_distinct_ids"]},unmatched={d["unmatched_distinct_function_ids"]},',
      f'  basic_id={b["id"]},selector_id={b["selector_id"]},basic_functions=0,damage_chain_verified=false,',
      '  categories={']
    for name,n in safe:
        lines.append(f'    {{name={json.dumps(name)},count={n}}},')
    lines.append('  }}\n')
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    result=audit(args.root)
    (args.root/'reports/self_skill_flow.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (args.root/'reports/self_skill_flow.lua').write_text(lua_report(result),encoding='utf-8')
    print('F41:',result['verified_arm64_instructions'],'instruções; '
          f'{result["third_vector_total_entries"]} IDs de função, '
          f'{result["unmatched_distinct_function_ids"]} sem tabela correspondente')

if __name__=='__main__':main()
