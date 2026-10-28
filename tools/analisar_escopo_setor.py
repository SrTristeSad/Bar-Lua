#!/usr/bin/env python3
"""F33: ligação verificável HeroConfig.damageScope -> ValueType 3 -> SelectTargetSector.

Não converte a AABB de consulta na área definitiva de acerto. Tabelas
proprietárias não são copiadas para o relatório público.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from analisar_valores_vida import command, instructions, SYMBOL
from analisar_esquema_heroi import check
from analisar_movimento import read_float_va
from catalogar_habilidades import parse_table

ROOT=Path(__file__).resolve().parents[1]
SECTOR_SHA='385aece1b985ad3103f7c6b37d9dd57a8e52c9edcf7b66d7778070933fc142e7'
FUNCTIONS={
 'SelectSector::load':('_ZN6config5skill12SelectSector4loadERN3tms5xconf8DataLineE',0x152f860,504),
 'CircleParameters::load':('_ZN6config5skill16CircleParameters4loadERN3tms5xconf8DataLineE',0x186bd24,120),
 'Sector::constructor':('_ZN19CSelectTargetSectorC2EPKN6config5skill12SelectSectorE',0xe63c90,200),
 'Sector::GetSelectTargets':('_ZN19CSelectTargetSector16GetSelectTargetsEv',0xe63e14,632),
 'Hero::getValueByType':('_ZNK4Hero14getValueByTypeEN6config5skill9ValueTypeEfPKNS1_9OperationE',0xe58af8,652),
 'Entity::getValueByType':('_ZN6Entity14getValueByTypeEN6config5skill9ValueTypeEfPKS_PK6CSkillPKNS1_9OperationE',0xe45d5c,352),
}
CHECKS={
 'SelectSector::load':[
  (0x152f8e4,'bl',('decodeInt',)),(0x152f8e8,'str',('w0','[x20, #0x30]')),
  (0x152f8f0,'bl',('decodeInt',)),(0x152f8f4,'str',('w0','[x20, #0x34]')),
  (0x152f924,'str',('w0','[x20, #0x44]')),
  (0x152f950,'str',('x0','[x20, #0x48]'))],
 'CircleParameters::load':[
  (0x186bd3c,'bl',('decodeInt',)),(0x186bd40,'str',('w0','[x19, #0x8]')),
  (0x186bd48,'bl',('decodeInt',)),(0x186bd4c,'str',('w0','[x19, #0xc]'))],
 'Sector::constructor':[(0xe63c9c,'ldr',('x14','[x1, #0x48]')),(0xe63cd4,'str',('x14','[x0, #0x48]'))],
 'Sector::GetSelectTargets':[
  (0xe63e5c,'ldr',('x8','[x19, #0x48]')),
  (0xe63e60,'ldr',('w0','[x8, #0x8]')),
  (0xe63e64,'ldr',('s0','[x8, #0xc]')),
  (0xe63e78,'bl',('getValueByType',)),
  (0xe63f70,'fmul',('s0','s11','s0')),
  (0xe63ff0,'fdiv',('s1','s11','s0')),
  (0xe63ff4,'fdiv',('s2','s10','s0')),
  (0xe63ff8,'fdiv',('s0','s8','s0')),
  (0xe6401c,'bl',('QueryAABB',)),
  (0xe6402c,'blr',('x8',))],
 'Hero::getValueByType':[
  (0xe58b34,'fdiv',('s9','s0','s1')),
  (0xe58b5c,'ldr',('s0','[x20, #0x330]')),
  (0xe58cd0,'fmul',('s0','s9','s0'))],
 'Entity::getValueByType':[(0xe45db0,'mov',('w1','w8')),(0xe45dc4,'br',('x4',))],
}

def parse_sectors(raw:bytes):
    rows=parse_table(raw,'skill.selectsector')
    counts={}
    scoped=[]
    for id,entry in sorted(rows.items()):
        tokens=entry['payload'].split()
        if len(tokens)<11 or tokens[6]!='@':
            raise ValueError(f'F33: estrutura invalida do seletor {id}')
        try:
            prefix=[int(s) for s in tokens[:6]]
            vtype,factor=int(tokens[7]),int(tokens[8])
        except ValueError as err:
            raise ValueError(f'F33: campo numerico invalido do seletor {id}') from err
        counts[vtype]=counts.get(vtype,0)+1
        if vtype==3:
            scoped.append({'id':id,'value_type':vtype,'factor_percent':factor,
                           'operation_absent':tokens[9]=='-',
                           'direction_type':prefix[1],'sector_width_int':prefix[5]})
    return rows,counts,scoped


def audit(library:Path,manifest:Path,table:Path,combat_report:Path):
    manifest_data=json.loads(manifest.read_text('utf-8'))
    expected=next(r['sha256'] for r in manifest_data['libraries'] if r['name']=='libcocos2dcpp.so')
    with library.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=expected:raise ValueError('F33: hash da biblioteca incompatível')
    raw=table.read_bytes();table_sha=hashlib.sha256(raw).hexdigest()
    if table_sha!=SECTOR_SHA:raise ValueError('F33: hash da tabela de setores incompatível')
    previous=json.loads(combat_report.read_text('utf-8'))
    if previous['library_sha256']!=actual or previous['damage_scope']['hero_offset']!='0x330' or previous['damage_scope']['value_type']!=3:
        raise ValueError('F33: trilha de HeroConfig/F32 inconsistente')
    symbols={(s,int(a,16),int(n)) for a,n,s in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    verified=[];check_total=0
    for label,(sym,start,size) in FUNCTIONS.items():
        if (sym,start,size) not in symbols:raise ValueError('F33: símbolo inválido: '+label)
        decoded=instructions(command('llvm-objdump','-d',f'--start-address=0x{start:x}',f'--stop-address=0x{start+size:x}',str(library)))
        if set(decoded)!=set(range(start,start+size,4)):
            raise ValueError('F33: desmontagem incompleta: '+label)
        for addr,op,parts in CHECKS[label]:check(label,decoded,addr,op,parts)
        verified.append({'name':label,'virtual_address':hex(start),'bytes':size,'instructions':len(decoded),'checks':len(CHECKS[label])})
        check_total+=len(CHECKS[label])
    binary=library.read_bytes()
    ratio=read_float_va(binary,0x1e98098)
    if ratio!=100.0:raise ValueError('F33: escala do QueryAABB modificada')
    rows,counts,scoped=parse_sectors(raw)
    if len(rows)!=84 or len(scoped)!=18 or not any(s['id']==10052 and s['factor_percent']==100 and s['operation_absent'] for s in scoped):
        raise ValueError('F33: sentinelas da tabela de setores divergentes')
    return {'phase':33,'apk_version':'1.0.1811','elf_sha256':actual,'sector_sha256':table_sha,
            'verified_functions':verified,'verified_instructions':sum(s['instructions'] for s in verified),
            'checkpoints':check_total,'sector_records':len(rows),'value_type_counts':{str(k):v for k,v in sorted(counts.items())},
            'scope3_count':len(scoped),'scope3_with_simple_parameter':sum(s['operation_absent'] for s in scoped),
            'samples':[s for s in scoped if s['id'] in (10052,20052,30052,40052,50052,240052)],
            'query_aabb_divisor':ratio,'confirmed_path':[
                'HeroConfig+0x40 -> Hero+0x330 -> ValueType 3',
                'SelectSector::load carrega CircleParameters pelo ponteiro de offset +0x48',
                'CSelectTargetSector::GetSelectTargets le ValueType e fator e chama Entity::getValueByType',
                'Hero::getValueByType usa fator/100 multiplicado por Hero+0x330 para ValueType 3',
                'Setor calcula centro deslocado e consulta b2World::QueryAABB com centro e raio divididos por 100',
                'Apos QueryAABB ha chamada virtual para filtragem; consulta AABB nao garante alvo atingido'],
            'limits':[
                'Apenas parametros com operacao ausente (-) podem ser calculados pelo modulo Lua isolado.',
                'O AABB e somente etapa inicial de selecao; setor final, exclusoes e linha de visao nao foram reproduzidos.',
                'O caminho configuravel nao prova vinculo do setor 10052 com a habilidade 4010020.',
                'Escala 100 verificada no QueryAABB nao implica pixels ou hitbox valida na cena controlavel.']}

def as_lua(report):
    return ('-- F33: resumo publico de IDs/configuracoes, nao hitboxes jogaveis.\n'
            'return {phase=33,sector_records='+str(report['sector_records'])+
            ',scope3_count='+str(report['scope3_count'])+
            ',scope3_with_simple_parameter='+str(report['scope3_with_simple_parameter'])+
            ',query_aabb_divisor=100,scope_type=3,example_sector_id=10052,example_factor=100}\n')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    p.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    p.add_argument('--table',type=Path,default=ROOT/'assets_original/configdata/config.skill.selectsector.txt')
    p.add_argument('--combat-report',type=Path,default=ROOT/'reports/hero_combat_fields.json')
    p.add_argument('--json',type=Path,default=ROOT/'reports/sector_scope.json')
    p.add_argument('--lua',type=Path,default=ROOT/'reports/sector_scope.lua')
    args=p.parse_args()
    result=audit(args.library,args.manifest,args.table,args.combat_report)
    args.json.parent.mkdir(parents=True,exist_ok=True)
    args.json.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.lua.write_text(as_lua(result),encoding='utf-8')
    print('F33:',result['sector_records'],'setores,',result['scope3_count'],'com ValueType 3,',result['verified_instructions'],'instrucoes ARM64')

if __name__=='__main__':main()
