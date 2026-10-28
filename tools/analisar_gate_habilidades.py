#!/usr/bin/env python3
"""F38: auditoria estática do encadeamento das condições do CSkill.

Somente BarbarQ 1.0.1811. Não executa APK, não atribui condições
à habilidade 4010020 sem recuperar o esquema integral de HeroSkillConfig.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from analisar_valores_vida import SYMBOL, command, instructions
from analisar_esquema_heroi import check
from catalogar_habilidades import parse_table

ROOT=Path(__file__).resolve().parents[1]
FUNCS={
 'CSkill::ctor':('_ZN6CSkillC2EPKN6config5skill15HeroSkillConfigE',0xe64c40,188),
 'CSkill::creator_conditions':('_ZN6CSkill26GetCreatorConditionsResultEv',0xe653a0,220),
 'CSkill::target_conditions':('_ZN6CSkill25GetTargetConditionsResultERK12CSkillEntity',0xe65484,212),
 'CSkill::target_noarg':('_ZN6CSkill25GetTargetConditionsResultEv',0xe6547c,8),
 'CConditionManager::GetCondition':('_ZNK17CConditionManager12GetConditionEi',0xe45b5c,116),
 'CSkill::CreateSkillBySkillConfigId':('_ZN6CSkill26CreateSkillBySkillConfigIdEP6EntityiPKNSt3__16vectorI12CSkillEntityNS2_9allocatorIS4_EEEEi',0xe650b4,320),
}
CHECKS={
 'CSkill::ctor':[(0xe64c94,'add',('x19','#0xe8')),(0xe64c9c,'str',('x8','[x20, #0x38]')),(0xe64ca8,'add',('x19','#0xb0')),(0xe64cac,'add',('x19','#0xd0')),(0xe64cbc,'str',('x9','[x20, #0x28]')),(0xe64cc4,'str',('x10','[x20, #0x30]'))],
 'CSkill::creator_conditions':[(0xe653b8,'ldr',('[x19, #0x28]',)),(0xe653bc,'cbz',('x8',)),(0xe653f8,'ldr',('w1','[x8, x23, lsl #2]')),(0xe65400,'bl',('GetCondition',)),(0xe6540c,'bl',('SetTargetEntitys',)),(0xe65418,'bl',('SetCreateEntity',)),(0xe65424,'bl',('SetBindSkill',)),(0xe6542c,'ldr',('[x8, #0x18]',)),(0xe65434,'blr',('x8',)),(0xe6543c,'tbz',('w8','#0x0')),(0xe6544c,'orr',('#0x1',)),(0xe65464,'mov',('w0','wzr'))],
 'CSkill::target_conditions':[(0xe654a0,'ldr',('[x19, #0x30]',)),(0xe654a8,'cbz',('x8',)),(0xe654e4,'ldr',('w1','[x8, x24, lsl #2]')),(0xe654ec,'bl',('GetCondition',)),(0xe654f8,'bl',('SetCreateEntity',)),(0xe65500,'ldr',('[x8, #0x20]',)),(0xe65508,'mov',('x1','x20')),(0xe6550c,'blr',('x8',)),(0xe65514,'tbz',('w8','#0x0')),(0xe65524,'orr',('#0x1',)),(0xe6553c,'mov',('w0','wzr'))],
 'CSkill::target_noarg':[(0xe6547c,'orr',('w0','wzr','#0x1')),(0xe65480,'ret',())],
 'CConditionManager::GetCondition':[(0xe45ba4,'msub',('w8','w8','w10','w1')),(0xe45bac,'ldr',('x19','[x11, w8, sxtw #3]')),(0xe45bb4,'ldr',('[x8, #0x10]',)),(0xe45bbc,'blr',('x8',))],
 'CSkill::CreateSkillBySkillConfigId':[(0xe6511c,'cbz',('x24',)),(0xe65144,'ldr',('[x24, #0x40]',)),(0xe65154,'mov',('#0x2742',)),(0xe65158,'cmp',('w26','w8')),(0xe6516c,'bl',('CSelfSkill',)),(0xe65180,'bl',('CMultiTargetSkill',)),(0xe651a4,'blr',('x8',)),(0xe651a8,'str',('w21','[x23, #0x10]'))],
}

def audit(library:Path,manifest:Path,previous:Path,config_dir:Path):
    meta=json.loads(manifest.read_text('utf8'))
    expected=next(x['sha256'] for x in meta['libraries'] if x['name']=='libcocos2dcpp.so')
    with library.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    if expected!=digest:raise ValueError('F38: ELF original divergente')
    prev=json.loads(previous.read_text('utf8'))
    if prev.get('phase')!=37 or prev.get('elf_sha256')!=digest:raise ValueError('F38: relatorio F37 divergente')
    syms={(name,int(va,16),int(size)) for va,size,name in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    inspected=[]
    for label,(symbol,va,size) in FUNCS.items():
        if (symbol,va,size) not in syms:raise ValueError('F38: simbolo diferente: '+label)
        ops=instructions(command('llvm-objdump','-d',f'--start-address=0x{va:x}',f'--stop-address=0x{va+size:x}',str(library)))
        if set(ops)!=set(range(va,va+size,4)):raise ValueError('F38: instrucoes incompletas: '+label)
        for address,opcode,parts in CHECKS[label]:check(label,ops,address,opcode,parts)
        inspected.append({'function':label,'address':hex(va),'size':size,'instructions':len(ops),'checks':len(CHECKS[label])})
    skills_path=config_dir/'config.skill.heroskillconfig.txt'
    bindings_path=config_dir/'config.skill.functionbindskill.txt'
    skill_raw=skills_path.read_bytes(); bind_raw=bindings_path.read_bytes()
    hashes=meta.get('nothing',{})
    summary=json.loads((ROOT/'reports/skill_catalog_summary.json').read_text('utf8'))
    for k,raw in [('heroskillconfig',skill_raw),('functionbindskill',bind_raw)]:
        if hashlib.sha256(raw).hexdigest()!=summary['table_sha256'][k]:
            raise ValueError('F38: configuracao alterada: '+k)
    skills=parse_table(skill_raw,'heroskillconfig'); binds=parse_table(bind_raw,'functionbindskill')
    if 4010020 not in skills or binds[10039]['payload'].split()!=['1','2','4010020']:
        raise ValueError('F38: referencia do ataque basico inesperada')
    return {'phase':38,'apk_version':'1.0.1811','elf_sha256':digest,
      'audited':inspected,'verified_instructions':sum(x['instructions'] for x in inspected),
      'checkpoints':sum(x['checks'] for x in inspected),
      'binding':{'binding_id':10039,'button_code':2,'skill_id':4010020,'config_present':True},
      'native_fields':{'creator_ids':'CSkill+0x28 -> HeroSkillConfig+0xB0',
                       'target_ids':'CSkill+0x30 -> HeroSkillConfig+0xD0'},
      'rules':[
          'CSkill::GetCreatorConditionsResult: lista ausente/vazia retorna true; lista ativa executa condicoes em ordem e para no primeiro false.',
          'CSkill::GetTargetConditionsResult(CSkillEntity const&): lista ausente/vazia retorna true; virtual slot +0x20 para cada candidato e para no primeiro false.',
          'CSkill::GetTargetConditionsResult() sem argumento retorna true diretamente: nao avalia candidatos.',
          'Criador passa vetor de alvos, criador e skill ao CCondition; avaliacao de alvo fornece criador e candidato.',
          'CSkill::CreateSkillBySkillConfigId escolhe CSelfSkill para config tipo 10050; outros tipos vao para CMultiTargetSkill.'
       ],
      'limits':[
          'Nao decodifica as listas da configuracao 4010020; os ponteiros +0xb0/+0xd0 foram confirmados mas seus IDs nao foram atribuídos a essa habilidade.',
          'Nao prova a ligacao entre 4010020 e o seletor 10052 ou uma funcao de dano.',
          'Nao executa efeitos, alvo final, hitbox ou dano, nem reproduz gerenciamento de memoria do CConditionManager.',
          'Os dados originais de configuracao e o ELF nao entram no ZIP publico de fontes.'
       ]}

def as_lua(report):
    b=report['binding']
    return ('-- F38: portas de condicao verificadas; nenhuma regra de combate ativada.\n'
     + 'return {phase=38,verified_instructions='+str(report['verified_instructions'])
     +',checkpoints='+str(report['checkpoints'])+',functions='+str(len(report['audited']))
     +',skill_id='+str(b['skill_id'])+',button_code='+str(b['button_code'])
     +',creator_offset="0x28",target_offset="0x30",config_creator_offset="0xb0",config_target_offset="0xd0"'
     +',skill_binding_resolved=false,gameplay_enabled=false}\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    ap.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    ap.add_argument('--previous',type=Path,default=ROOT/'reports/compare_conditions.json')
    ap.add_argument('--config',type=Path,default=ROOT/'assets_original/configdata')
    ap.add_argument('--json',type=Path,default=ROOT/'reports/skill_condition_gate.json')
    ap.add_argument('--lua',type=Path,default=ROOT/'reports/skill_condition_gate.lua')
    a=ap.parse_args()
    result=audit(a.library,a.manifest,a.previous,a.config)
    a.json.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    a.lua.write_text(as_lua(result),encoding='utf8')
    print('F38:',result['verified_instructions'],'instrucoes',result['checkpoints'],'checks')
if __name__=='__main__':main()
