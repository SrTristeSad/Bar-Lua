#!/usr/bin/env python3
"""F40: decodifica os vetores xconf de HeroSkillConfig (APK 1.0.1811).

Não executa habilidades. Registros com objeto opcional presente permanecem
intencionalmente sem interpretar; não publicamos as linhas originais no relatório.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from analisar_esquema_skill import audit as audit39, KEY_CHECKS, ADDRESS, SIZE, NAME
from catalogar_habilidades import parse_table
from analisar_valores_vida import SYMBOL, command, instructions
from analisar_esquema_heroi import check

# Evidências complementares: contagem da lista e laço de decodeInt, escalar 0xc8,
# três vetores e o lookup final de EnhanceConfig.
CHECKS = [
 (0x152e7c8, 'bl', ('decodeInt',)),
 (0x152e7d0, 'ldr', ('[x21, #0xb0]',)),
 (0x152e820, 'cmp', ('w23', '#0x1')),
 (0x152e830, 'bl', ('decodeInt',)),
 (0x152e838, 'str', ('w0', '[x8, x24, lsl #2]')),
 (0x152e854, 'bl', ('decodeInt',)),
 (0x152e858, 'str', ('w0', '[x19, #0xc8]')),
 (0x152e860, 'bl', ('decodeInt',)),
 (0x152e868, 'ldr', ('[x21, #0xd0]',)),
 (0x152e8c8, 'bl', ('decodeInt',)),
 (0x152e8d0, 'str', ('w0', '[x8, x24, lsl #2]')),
 (0x152e8ec, 'bl', ('decodeInt',)),
 (0x152e8f4, 'ldr', ('[x21, #0xe8]',)),
 (0x152e954, 'bl', ('decodeInt',)),
 (0x152e95c, 'str', ('w0', '[x8, x24, lsl #2]')),
 (0x152e978, 'bl', ('decodeInt',)),
 (0x152e980, 'bl', ('runtime_typeid',)),
 (0x152e988, 'bl', ('getConfById',)),
 (0x152e98c, 'str', ('[x19, #0x100]',)),
]


def decode_absent_object_suffix(payload: str) -> dict:
    """Lê a cauda após o marcador ` - ` do objeto opcional ausente.

    Layout auditado no assembly: [nA, A..., kind, nB, B..., nC, C..., enhance_id].
    Não decodifica nem supõe o conteúdo dos campos textuais anteriores.
    """
    if ' - ' not in payload:
        raise ValueError('F40: marcador de objeto ausente não encontrado')
    suffix=payload.rsplit(' - ', 1)[1].split()
    try: values=[int(x) for x in suffix]
    except ValueError as exc: raise ValueError('F40: cauda contém token não inteiro') from exc
    i=0
    def read_int():
        nonlocal i
        if i >= len(values): raise ValueError('F40: cauda truncada')
        result=values[i]; i+=1
        return result
    def read_list():
        n=read_int()
        if not 0 <= n <= 1024: raise ValueError('F40: contagem de vetor inválida')
        if i+n>len(values): raise ValueError('F40: vetor truncado')
        return [read_int() for _ in range(n)]
    creator=read_list()
    kind=read_int()
    target=read_list()
    third=read_list()
    enhance=read_int()
    if i!=len(values):raise ValueError('F40: tokens extras após enhancement')
    return {'creator_condition_ids':creator,'kind':kind,
            'target_condition_ids':target,'third_vector_ids':third,'enhancement_id':enhance}


def audit(root: Path=ROOT) -> dict:
    phase39=audit39(root)  # SHA do ELF, símbolos, instruções, hashes, botão 10039
    library=root/'lib/arm64-v8a/libcocos2dcpp.so'
    ops=instructions(command('llvm-objdump','-d',f'--start-address=0x{ADDRESS:x}',
                             f'--stop-address=0x{ADDRESS+SIZE:x}',str(library)))
    for va, opcode, parts in CHECKS:
        check('HeroSkillConfig::load F40',ops,va,opcode,parts)
    prior=json.loads((root/'reports/skill_condition_gate.json').read_text('utf8'))
    if prior['phase']!=38 or prior['elf_sha256']!=phase39['elf_sha256']:
        raise ValueError('F40: evidências F38 divergentes')
    if (prior['native_fields']['creator_ids']!='CSkill+0x28 -> HeroSkillConfig+0xB0' or
        prior['native_fields']['target_ids']!='CSkill+0x30 -> HeroSkillConfig+0xD0'):
        raise ValueError('F40: relação dos vetores com CSkill mudou')
    config=root/'assets_original/configdata/config.skill.heroskillconfig.txt'
    raw=config.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=phase39['table_sha256']:
        raise ValueError('F40: dados xconf diferem do APK 1.0.1811')
    rows=parse_table(raw,'heroskillconfig')
    count_parsed=0; skipped=0
    sizes=[Counter(),Counter(),Counter()]
    kind_counts=Counter()
    basic=None
    for id,row in rows.items():
        if ' - ' not in row['payload']:
            skipped+=1
            continue
        try: obj=decode_absent_object_suffix(row['payload'])
        except ValueError as exc: raise ValueError(f'F40: estrutura inválida do registro {id}') from exc
        count_parsed+=1
        for c,items in zip(sizes, (obj['creator_condition_ids'], obj['target_condition_ids'],obj['third_vector_ids'])):
            c[len(items)]+=1
        kind_counts[obj['kind']]+=1
        if id==4010020:basic=obj
    if basic is None:raise ValueError('F40: habilidade 4010020 não decodificada')
    if (basic['creator_condition_ids']!=[] or basic['target_condition_ids']!=[] or
        basic['third_vector_ids']!=[] or basic['kind']!=10050 or basic['enhancement_id']!=-1):
        raise ValueError('F40: layout do ataque básico inesperado')
    if count_parsed+skipped!=len(rows):raise AssertionError('F40: contagem inconsistênte')
    return {'phase':40,'apk_version':'1.0.1811',
      'elf_sha256':phase39['elf_sha256'],
      'table_sha256':phase39['table_sha256'],
      'native_function':'HeroSkillConfig::load',
      'native_function_address':hex(ADDRESS),
      'verified_instructions':phase39['verified_instructions'],
      'checkpoints':len(KEY_CHECKS)+len(CHECKS),
      'new_checkpoints':len(CHECKS),
      'records_total':len(rows),'records_decoded':count_parsed,
      'records_skipped_optional_object':skipped,
      'vector_size_histograms':[{str(k):v for k,v in sorted(c.items())} for c in sizes],
      'skill_kind_sample_counts':{str(k):v for k,v in kind_counts.most_common(8)},
      'native_fields':{
        'creator_conditions':'HeroSkillConfig+0xB0 -> CSkill+0x28',
        'skill_kind':'HeroSkillConfig+0xC8',
        'target_conditions':'HeroSkillConfig+0xD0 -> CSkill+0x30',
        'third_vector':'HeroSkillConfig+0xE8 -> CSkill+0x38',
        'enhancement_reference':'HeroSkillConfig+0x100'},
      'basic_skill':{'id':4010020,'binding_id':10039,'button_code':2,
                     'creator_conditions':basic['creator_condition_ids'],
                     'skill_kind':basic['kind'],
                     'target_conditions':basic['target_condition_ids'],
                     'third_vector':basic['third_vector_ids'],
                     'enhancement_id':basic['enhancement_id'],
                     'skill_class':'CSelfSkill (native 10050 branch)',
                     'lists_verified':True,'damage_chain_verified':False},
      'limits':[
        'A cauda da configuração é decodificada para registros com objeto opcional ausente; registros com objeto presente são contabilizados, não decodificados.',
        'O terceiro vetor é preservado sem pressupor que execute dano ou animação.',
        'Lista vazia de condições não prova ausência de efeitos nativos ou de outras habilidades.',
        'Não confirma seleção final, hitbox, dano, tempo de recarga nem gameplay Windows.'
      ]}


def lua_report(d: dict)->str:
    b=d['basic_skill']
    return ('-- F40: evidencias do xconf; nenhum recurso original nem combate implementado.\n'
      'return {phase=40,gameplay_enabled=false,skill_id=4010020,button=2,\n'
      '  records='+str(d['records_total'])+',decoded='+str(d['records_decoded'])+',skipped='+str(d['records_skipped_optional_object'])+',\n'
      '  native_instructions='+str(d['verified_instructions'])+',checks='+str(d['checkpoints'])+',\n'
      '  kind='+str(b['skill_kind'])+',creator_count=0,target_count=0,third_count=0,enhancement=-1,\n'
      '  creator_offset="0xB0",target_offset="0xD0",third_offset="0xE8",\n'
      '  condition_lists_verified=true,damage_chain_verified=false}\n')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=ROOT)
    args=ap.parse_args()
    result=audit(args.root)
    (args.root/'reports/skill_xconf40.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    (args.root/'reports/skill_xconf40.lua').write_text(lua_report(result),encoding='utf8')
    print('F40:',result['records_decoded'],'registros decodificados /',result['records_total'],
          'total, listas do 4010020 vazias,', result['new_checkpoints'],'checks adicionais')

if __name__=='__main__': main()
