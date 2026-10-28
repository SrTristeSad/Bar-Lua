#!/usr/bin/env python3
"""F36: evidencia estaticamente CCamp/CBuff/CEntityKind no BarbarQ 1.0.1811.

Não executa o ELF e não infere que um predicado é usado pelo ataque 4010020.
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

ROOT=Path(__file__).resolve().parents[1]
FUNCTIONS={
  'CCampCondition::Init':('_ZN14CCampCondition4InitEN6config5skill11ContainTypeEi',0xe44578,8),
  'CCampCondition::GetCreatorResult':('_ZN14CCampCondition16GetCreatorResultEv',0xe44580,268),
  'CCampCondition::GetTargetResult':('_ZN14CCampCondition15GetTargetResultEPK12CSkillEntity',0xe446ac,268),
  'CBuffCondition::GetTargetResult':('_ZN14CBuffCondition15GetTargetResultEPK12CSkillEntity',0xe447f0,108),
  'CEntityKindTypeCondition::GetCreatorResult':('_ZN24CEntityKindTypeCondition16GetCreatorResultEv',0xe44864,80),
  'CEntityKindTypeCondition::GetTargetResult':('_ZN24CEntityKindTypeCondition15GetTargetResultEPK12CSkillEntity',0xe448b4,84),
}
CHECKS={
 'CCampCondition::Init':[(0xe44578,'stp',('w1','w2','[x0, #0xc]'))],
 'CCampCondition::GetCreatorResult':[
 (0xe44590,'ldr',('x8','[x19, #0x28]')),
 (0xe445d4,'cmp',('w8','#0x7')),
 (0xe445fc,'br',('x8',)),
 (0xe44600,'ldr',('w8','[x0, #0x17c]')),
 (0xe44604,'ldr',('w9','[x20, #0x17c]')),
 (0xe44668,'cset',('w8','eq')),
 (0xe44670,'cmp',('w9','#0x3')),
 (0xe44678,'eor',('w8','w8','w9'))],
 'CCampCondition::GetTargetResult':[
 (0xe446cc,'bl',('GetEntity',)),
 (0xe44700,'cmp',('w8','#0x7')),
 (0xe44728,'br',('x8',)),
 (0xe4472c,'ldr',('w8','[x0, #0x17c]')),
 (0xe44730,'ldr',('w9','[x20, #0x17c]')),
 (0xe44750,'ldr',('w8','[x20, #0x17c]')),
 (0xe44798,'ldr',('w9','[x19, #0xc]')),
 (0xe447a4,'eor',('w8','w8','w9'))],
 'CBuffCondition::GetTargetResult':[
 (0xe4480c,'bl',('GetEntity',)),
 (0xe4481c,'bl',('getStateDetails',)),
 (0xe44828,'ldrb',('w9','[x0, #0x4]')),
 (0xe4482c,'cmp',('w8','#0x2')),
 (0xe44834,'eor',('w8','w8','w9')),
 (0xe4483c,'cmp',('w8','#0x2'))],
 'CEntityKindTypeCondition::GetCreatorResult':[
 (0xe4488c,'ldr',('w8','[x8, #0x20]')),
 (0xe44890,'ldp',('w10','w9','[x19, #0xc]')),
 (0xe4489c,'cmp',('w10','#0x3')),
 (0xe448a4,'eor',('w0','w8','w9'))],
 'CEntityKindTypeCondition::GetTargetResult':[
 (0xe448e0,'ldr',('w8','[x8, #0x20]')),
 (0xe448e4,'ldp',('w10','w9','[x19, #0xc]')),
 (0xe448f0,'cmp',('w10','#0x3')),
 (0xe448f8,'eor',('w0','w8','w9'))],
}
JUMPS={
 'CCampCondition::GetCreatorResult':(0xe4468c,0xe445ec,[0xe44600,0xe44610,0xe44624,0xe44630,0xe4463c,0xe44648,0xe44654,0xe44660]),
 'CCampCondition::GetTargetResult':(0xe447b8,0xe44718,[0xe4472c,0xe4473c,0xe44750,0xe4475c,0xe44768,0xe44774,0xe44780,0xe4478c]),
}

def raw32(blob,va):
    if blob[:6]!=b'\x7fELF\x02\x01':raise ValueError('ELF64 LE esperado')
    phoff=struct.unpack_from('<Q',blob,0x20)[0]
    entry,n=struct.unpack_from('<HH',blob,0x36)
    if not 56<=entry<=256 or not 1<=n<=128:raise ValueError('ELF headers invalidos')
    for i in range(n):
        t,_,offset,base,_,size,_,_=struct.unpack_from('<IIQQQQQQ',blob,phoff+i*entry)
        if t==1 and base<=va and va+4<=base+size:
            return struct.unpack_from('<i',blob,offset+va-base)[0]
    raise ValueError('VA sem PT_LOAD')

def audit(library:Path,manifest:Path,prev:Path,tables:Path):
    manifests=json.loads(manifest.read_text('utf8'))
    expected=next(e['sha256'] for e in manifests['libraries'] if e['name']=='libcocos2dcpp.so')
    raw=library.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=expected:raise ValueError('F36: ELF original divergente')
    previous=json.loads(prev.read_text('utf8'))
    if previous['phase']!=35 or previous['elf_sha256']!=digest:raise ValueError('F36: F35 incompleta')
    syms={(name,int(addr,16),int(size)) for addr,size,name in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    functions=[]
    for label,(symbol,start,size) in FUNCTIONS.items():
        if (symbol,start,size) not in syms:raise ValueError('F36: simbolo divergente '+label)
        decoded=instructions(command('llvm-objdump','-d',f'--start-address=0x{start:x}',f'--stop-address=0x{start+size:x}',str(library)))
        expected_addr=set(range(start,start+size,4))
        if label in JUMPS:
            jump_start,_,targets=JUMPS[label]
            expected_addr-=set(range(jump_start,jump_start+4*len(targets),4))
            # Sao 8 int32 LE no .text, relativos ao inicio da propria tabela.
            actual=[jump_start+raw32(raw,jump_start+4*i) for i in range(len(targets))]
            if actual != targets:raise ValueError('F36: jump table divergiu '+label)
        if set(decoded)!=expected_addr:
            raise ValueError('F36: instrucoes ARM64 divergentes '+label)
        for addr,opcode,operands in CHECKS[label]:check(label,decoded,addr,opcode,operands)
        functions.append({'name':label,'address':hex(start),'bytes':size,'instructions':len(decoded),'checks':len(CHECKS[label])})
    configs={}
    for short in ('conditioncamp','conditionbuff','conditionentitytype'):
        raw_table=(tables/f'config.skill.{short}.txt').read_bytes()
        rows=parse_lines(raw_table)
        if previous['table_summaries'][short]['sha256']!=hashlib.sha256(raw_table).hexdigest():
            raise ValueError('F36: tabela original alterada '+short)
        parsed=[]
        for row in rows:
            cells=row['parameters'].split()
            if len(cells)<2:raise ValueError('F36: registro incompleto '+short)
            contain,value=int(cells[0]),int(cells[1])
            parsed.append((contain,value))
        configs[short]={'count':len(rows),'sha256':hashlib.sha256(raw_table).hexdigest(),
            'contain_types':sorted(set(pair[0] for pair in parsed)),
            'condition_args':sorted(set(pair[1] for pair in parsed))[:12]}
    return {'phase':36,'apk_version':'1.0.1811','elf_sha256':digest,
        'functions':functions,'verified_instructions':sum(x['instructions'] for x in functions),
        'checkpoints':sum(x['checks'] for x in functions),
        'jump_tables_checked':len(JUMPS),'config_tables':configs,
        'confirmed_rules':[
          'CCampCondition: campos Entity +0x17C; 8 seletores de camp; ContainType==3 aceita comparacao, outros invertem; NULL falso.',
          'CEntityKindTypeCondition: campo Entity +0x20 compara inteiro configurado; ContainType==3 aceita igualdade, outros negam; NULL falso.',
          'CBuffCondition: getStateDetails(id) retorna opcional; byte +0x4 combina-se por XOR com (ContainType==2); entidade NULL falso.',
        ],'limitations':[
          'Os tres predicados sao isolados; nao reproduzem todo o estado de Entity, os buffs nem a associacao a habilidades.',
          'Nao ha evidencia de que a habilidade 4010020 use estes IDs de condicao.',
          'Nenhum dano e aplicado, nenhum alvo final ou callback dinamico e simulado.'
        ]}

def as_lua(report):
    return ('-- F36: relatorio estatico, apenas evidencia de predicados.\n'
            'return {phase=36,verified_instructions='+str(report['verified_instructions'])+
            ',checkpoints='+str(report['checkpoints'])+',functions='+str(len(report['functions']))+
            ',skill_binding_resolved=false,gameplay_enabled=false}\n')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    parser.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    parser.add_argument('--previous',type=Path,default=ROOT/'reports/condition_flow.json')
    parser.add_argument('--tables',type=Path,default=ROOT/'assets_original/configdata')
    parser.add_argument('--json',type=Path,default=ROOT/'reports/concrete_conditions.json')
    parser.add_argument('--lua',type=Path,default=ROOT/'reports/concrete_conditions.lua')
    args=parser.parse_args()
    report=audit(args.library,args.manifest,args.previous,args.tables)
    args.json.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    args.lua.write_text(as_lua(report),encoding='utf8')
    print('F36:',report['verified_instructions'],'instr.',report['checkpoints'],'checks,',len(report['functions']),'funcoes')

if __name__=='__main__':main()
