#!/usr/bin/env python3
"""F37: verifica predicados de relação entre entidades e comparação de valores.

Análise estática de libcocos2dcpp.so (BarbarQ 1.0.1811): não executa o
binário nem infere vínculo com uma habilidade específica.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path
from analisar_valores_vida import SYMBOL, command, instructions
from analisar_esquema_heroi import check
from analisar_condicoes import parse_lines
from analisar_condicoes_concretas import raw32

ROOT=Path(__file__).resolve().parents[1]
CONFIG_HASHES={
  'conditionskillentitytype':'ce34067c6f082965b402e485a318c95134183d9dced8c8d0c36808f32def3cf6',
  'conditionvaluecompare':'7a013fa6e0ce953d5f60873824d03796457d85a31d70de6e27ee23623ebca24a',
}
FUNCTIONS={
 'SkillEntity::GetCreatorResult':('_ZN25CSkillEntityTypeCondition16GetCreatorResultEv',0xe44f90,8),
 'SkillEntity::GetTargetResult':('_ZN25CSkillEntityTypeCondition15GetTargetResultEPK12CSkillEntity',0xe44f98,156),
 'SkillEntity::Init':('_ZN25CSkillEntityTypeCondition4InitEN6config5skill11ContainTypeEi',0xe45034,8),
 'Compare::GetCreatorResult':('_ZN22CCompareValueCondition16GetCreatorResultEv',0xe44a60,124),
 'Compare::GetTargetResult':('_ZN22CCompareValueCondition15GetTargetResultEPK12CSkillEntity',0xe44d68,252),
 'Compare::GetResult':('_ZN22CCompareValueCondition9GetResultEP6EntityS1_',0xe44adc,596),
 'Compare::Operate':('_ZN22CCompareValueCondition7OperateEfN6config5skill19OperationSymbolTypeEf',0xe44ee0,76),
 'Compare::GetTargetResult(no-arg)':('_ZN22CCompareValueCondition15GetTargetResultEv',0xe44e64,124),
}
CHECKS={
 'SkillEntity::GetCreatorResult':[(0xe44f90,'orr',('w0','wzr','#0x1'))],
 'SkillEntity::GetTargetResult':[
  (0xe44fa8,'ldr',('w9','[x19, #0x10]')), (0xe44fb0,'cmp',('w9','#0x3')),
  (0xe44fc0,'bl',('GetEntity',)), (0xe44fc4,'ldr',('w20','[x0, #0x30]')),
  (0xe44fd0,'bl',('GetEntity',)), (0xe44fd4,'ldr',('w8','[x0, #0x188]')),
  (0xe44fdc,'cmp',('w20','w8')), (0xe44ff4,'ldr',('x9','[x19, #0x20]')),
  (0xe45004,'cmp',('w8','w9')), (0xe45014,'eor',('w0','w8','w9')),
  (0xe45024,'cset',('w0','eq'))],
 'SkillEntity::Init':[(0xe45034,'stp',('w1','w2','[x0, #0xc]'))],
 'Compare::GetCreatorResult':[
  (0xe44a74,'ldr',('x9','[x19, #0x38]')),(0xe44a78,'ldr',('x8','[x8, #0x38]')),
  (0xe44a84,'blr',('x8',)),(0xe44aa0,'blr',('x8',)),(0xe44ad8,'b',('GetResult',))],
 'Compare::GetTargetResult':[
  (0xe44d7c,'ldp',('x8','x10','[x19, #0x38]')),
  (0xe44d8c,'cmp',('w9','#0x2')),(0xe44d94,'cmp',('w8','#0x2')),
  (0xe44dd4,'bl',('GetEntity',)),(0xe44e40,'ldp',('x29','x30','[sp, #0x20]')),
  (0xe44e4c,'b',('GetResult',)),(0xe44e50,'orr',('w0','wzr','#0x1'))],
 'Compare::GetResult':[
  (0xe44b04,'cmp',('w22','#0x3e9')),(0xe44b14,'bl',('GetValue',)),
  (0xe44b24,'fdiv',('s8','s1','s0')),(0xe44b50,'bl',('getValueByType',)),
  (0xe44b5c,'fmov',('s8','#-1.00000000')),
  (0xe44bc0,'fcmp',('s8','s1')),(0xe44bc8,'fcmp',('s0','s1')),
  (0xe44c08,'fdiv',('s1','s1','s2')),
  (0xe44c10,'fadd',('s8','s8','s1')),(0xe44c20,'fsub',('s8','s8','s1')),
  (0xe44c28,'fmul',('s8','s8','s1')),(0xe44c30,'fdiv',('s8','s8','s1')),
  (0xe44c98,'cmp',('w8','#0x5')),(0xe44cb8,'br',('x8',)),
  (0xe44cd0,'b',('0xe44d18',)),(0xe44ce8,'cset',('w0','gt')),
  (0xe44cf4,'cset',('w0','gt')),(0xe44d00,'cset',('w0','ge')),
  (0xe44d0c,'cset',('w0','mi')),(0xe44d18,'cset',('w0','ls'))],
 'Compare::Operate':[
  (0xe44ee0,'cmp',('w1','#0x3')),(0xe44f04,'fdiv',('s1','s1','s2')),
  (0xe44f0c,'fadd',('s0','s1','s0')),(0xe44f14,'fsub',('s0','s0','s1')),
  (0xe44f1c,'fmul',('s0','s1','s0')),(0xe44f24,'fdiv',('s0','s0','s1'))],
 'Compare::GetTargetResult(no-arg)':[
  (0xe44e78,'ldr',('x9','[x19, #0x38]')),
 ],
}
TABLES={
 'Compare::GetResult': [
   (0xe44d30, [0xe44c10,0xe44c20,0xe44c28,0xe44c30]),
   (0xe44d40, [0xe44c74,0xe44c7c,0xe44c84,0xe44c8c]),
   (0xe44d50, [0xe44cbc,0xe44cd4,0xe44cf0,0xe44cfc,0xe44d08,0xe44d14]),
 ],
 'Compare::Operate':[(0xe44f2c,[0xe44f0c,0xe44f14,0xe44f1c,0xe44f24])],
}
# 2 tabelas de operation em GetResult e 1 de comparação. A soma de offsets
# cobre todo o bloco de 14 DWORDs em [0xe44d30, 0xe44d68).

def read_f32(blob,va):
    if blob[:6]!=b'\x7fELF\x02\x01':raise ValueError('ELF64 little endian esperado')
    phoff=struct.unpack_from('<Q',blob,0x20)[0]
    entry,n=struct.unpack_from('<HH',blob,0x36)
    for i in range(n):
        t,_,offset,base,_,filesz,_,_=struct.unpack_from('<IIQQQQQQ',blob,phoff+i*entry)
        if t==1 and base<=va and va+4<=base+filesz:
            return struct.unpack_from('<f',blob,offset+va-base)[0]
    raise ValueError('Constante nao encontrada em PT_LOAD: '+hex(va))

def audit(library:Path,manifest:Path,previous:Path,tables_dir:Path):
    meta=json.loads(manifest.read_text('utf8'))
    expected=next(x['sha256'] for x in meta['libraries'] if x['name']=='libcocos2dcpp.so')
    blob=library.read_bytes()
    digest=hashlib.sha256(blob).hexdigest()
    if digest != expected:raise ValueError('F37: ELF original divergente')
    prev=json.loads(previous.read_text('utf8'))
    if prev.get('phase')!=36 or prev.get('elf_sha256')!=digest:
        raise ValueError('F37: falta relatorio F36 valido')
    syms={(name,int(a,16),int(size)) for a,size,name in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    audited=[]
    for label,(symbol,start,size) in FUNCTIONS.items():
        if (symbol,start,size) not in syms:raise ValueError('F37: simbolo diferente: '+label)
        ops=instructions(command('llvm-objdump','-d',f'--start-address=0x{start:x}',f'--stop-address=0x{start+size:x}',str(library)))
        expected_offsets=set(range(start,start+size,4))
        for table, targets in TABLES.get(label,[]):
            actual=[table+raw32(blob,table+4*i) for i in range(len(targets))]
            if actual!=targets:raise ValueError('F37: jump table divergente '+label+hex(table))
            expected_offsets-=set(range(table,table+4*len(targets),4))
        if set(ops)!=expected_offsets:
            diff=sorted(expected_offsets.symmetric_difference(set(ops)))[:5]
            raise ValueError('F37: instrucao divergente '+label+': '+str([hex(i) for i in diff]))
        for addr,op,parts in CHECKS[label]: check(label,ops,addr,op,parts)
        audited.append({'name':label,'start':hex(start),'bytes':size,'verified_instructions':len(ops),'checkpoints':len(CHECKS[label])})
    configs={}
    for stem in ('conditionskillentitytype','conditionvaluecompare'):
        raw=(tables_dir/f'config.skill.{stem}.txt').read_bytes()
        rows=parse_lines(raw)
        if hashlib.sha256(raw).hexdigest()!=CONFIG_HASHES[stem]:
            raise ValueError('F37: tabela original divergente '+stem)
        configs[stem]={'records':len(rows),'sha256':hashlib.sha256(raw).hexdigest()}
        if stem=='conditionskillentitytype':
            configs[stem]['cases']=[{'id':r['id'],'contain':int(r['parameters'].split()[0]),'mode':int(r['parameters'].split()[1])} for r in rows]
    ratio=read_f32(blob,0x1e98098)
    epsilon=read_f32(blob,0x1e98550)
    if ratio!=100.0 or not 0.0<epsilon<1.0:raise ValueError('F37: constantes nao esperadas')
    return {
       'phase':37,'apk_version':'1.0.1811','elf_sha256':digest,
       'functions':audited,'verified_instructions':sum(x['verified_instructions'] for x in audited),
       'checkpoints':sum(x['checkpoints'] for x in audited),'jump_tables':sum(len(x) for x in TABLES.values()),
       'ratio':ratio,'compare_epsilon':epsilon,'config_tables':configs,
       'confirmed_rules':[
          'SkillEntity GetCreatorResult retorna true sem avaliacao adicional.',
          'SkillEntity GetTargetResult: modo 1 compara os IDs do CSkillEntity; modo 3 compara o campo +0x30 do Entity de destino com +0x188 do Entity vinculado ao criador.',
          'SkillEntity: ContainType 3 preserva igualdade; demais valores invertem o resultado; modos desconhecidos retornam ContainType==3.',
          'Compare GetResult avalia ValueType nos dois Entity, normaliza valores por /100, trata sentinela -1 como falha e aplica duas operacoes opcionais.',
          'Compare: seis comparadores (aproximadamente igual/diferente, >, >=, <, <=) via tabela ARM64, com tolerancia extraida do ELF.',
          'Operate: aplica + - * / sobre operando percentual, para codigos 0..3; outros codigos retornam o valor original.'
       ],'limits':[
          'Nao interpreta automaticamente todos os 1406 registros de comparevalue; seus operandos devem ser resolvidos por SParseValueInfo e Entity::getValueByType.',
          'Nao foi vinculada uma condicao a habilidade 4010020.',
          'Nao existe combate real, alvo final, hitbox nem aplicacao de dano.',
          'Ponteiros e chamadas sem verificacao NULL do original nao sao simulados como acesso inseguro.'
       ]
    }

def as_lua(d):
    return ('-- F37: evidencias ARM64, simulacao isolada sem combate real.\n'
       + 'return {phase=37,verified_instructions='+str(d['verified_instructions'])
       +',checkpoints='+str(d['checkpoints'])+',functions='+str(len(d['functions']))
       +',ratio=100,epsilon='+repr(d['compare_epsilon'])+',skill_binding_resolved=false,gameplay_enabled=false}\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    ap.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    ap.add_argument('--previous',type=Path,default=ROOT/'reports/concrete_conditions.json')
    ap.add_argument('--tables',type=Path,default=ROOT/'assets_original/configdata')
    ap.add_argument('--json',type=Path,default=ROOT/'reports/compare_conditions.json')
    ap.add_argument('--lua',type=Path,default=ROOT/'reports/compare_conditions.lua')
    args=ap.parse_args()
    report=audit(args.library,args.manifest,args.previous,args.tables)
    args.json.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    args.lua.write_text(as_lua(report),encoding='utf8')
    print('F37',report['verified_instructions'],'instrucoes,',report['checkpoints'],'checks;',report['config_tables']['conditionvaluecompare']['records'],'condicoes numericas')

if __name__=='__main__':main()
