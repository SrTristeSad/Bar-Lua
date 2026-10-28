#!/usr/bin/env python3
"""F34: verifica o filtro real pos-QueryAABB do BarbarQ ARM64 1.0.1811.

Nao publica ativos do APK, nao simula conditions, nem sugere que um candidato
esta validado como alvo de habilidade ou que recebeu dano.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from analisar_valores_vida import SYMBOL, command, instructions
from analisar_esquema_heroi import check
from analisar_movimento import read_float_va

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = {
    'CSectorQueryCallback::Query': ('_ZN20CSectorQueryCallback5QueryEv', 0xe62134, 140),
    'CSectorQueryCallback::ReportFixture': ('_ZN20CSectorQueryCallback13ReportFixtureEP9b2Fixture', 0xe621c0, 624),
    'CSelectTargetSector::Filter': ('_ZN19CSelectTargetSector6FilterEv', 0xe63d58, 188),
    'CSelectTargetSector::GetSelectTargets': ('_ZN19CSelectTargetSector16GetSelectTargetsEv', 0xe63e14, 632),
}
CHECKS = {
    'CSectorQueryCallback::Query': [
        (0xe6219c,'bl',('QueryAABB',)),
    ],
    'CSectorQueryCallback::ReportFixture': [
        (0xe621f0,'ldr',('x8','[x1, #0x10]')),
        (0xe621f4,'ldr',('x19','[x8, #0xb0]')),
        (0xe621fc,'cbz',('x19',)),
        (0xe62200,'ldr',('w8','[x19, #0x20]')),
        (0xe62204,'ldr',('w9','[x20, #0x28]')),
        (0xe62208,'and',('w8','w9','w8')),
        (0xe6220c,'cbz',('w8',)),
        (0xe62230,'ldr',('w8','[x19, #0x1a8]')),
        (0xe62240,'cmp',('w8','#0x1')),
        (0xe62248,'cmp',('w8','#0x3')),
        (0xe622ac,'cmp',('w8','#0x2')),
        (0xe62294,'scvtf',('s0','w0')),
        (0xe6229c,'fmul',('s0','s0','s0')),
        (0xe622a0,'fcmp',('s10','s0')),
        (0xe622a4,'b.pl',()),
        (0xe622d8,'fmov',('s12','#0.50000000')),
        (0xe622e4,'fcmp',('s11','s0')),
        (0xe622e8,'b.hi',()),
        (0xe62318,'fcmp',('s11','s0')),
        (0xe6231c,'b.hi',()),
        (0xe62328,'bl',('cosDeg',)),
        (0xe62338,'bl',('sinDeg',)),
        (0xe62340,'fsqrt',('s0','s10')),
        (0xe62360,'fcmp',('s0','s1')),
        (0xe62364,'b.lt',()),
        (0xe62388,'fdiv',('s0','s1','s0')),
        (0xe6238c,'bl',('acosDeg',)),
        (0xe6239c,'asr',('w8','w8','#1')),
        (0xe623a4,'fcmp',('s0','s1')),
        (0xe623a8,'b.pl',()),
        (0xe623ac,'ldr',('w8','[x19, #0x30]')),
        (0xe623f8,'orr',('w0','wzr','#0x1')),
    ],
    'CSelectTargetSector::Filter': [
        (0xe63d70,'ldr',('x8','[x19, #0x28]')),
        (0xe63da4,'ldr',('w1','[x8, x22, lsl #2]')),
        (0xe63dac,'bl',('GetCondition',)),
        (0xe63db8,'bl',('SetTargetEntitys',)),
        (0xe63dc4,'bl',('SetCreateEntity',)),
        (0xe63dd0,'bl',('SetBindSkill',)),
        (0xe63dd8,'ldr',('x8','[x8, #0x30]')),
        (0xe63de0,'blr',('x8',)),
        (0xe63dec,'cmp',('x9','x8')),
    ],
    'CSelectTargetSector::GetSelectTargets': [
        (0xe6401c,'bl',('QueryAABB',)),
        (0xe64024,'ldr',('x8','[x8, #0x8]')),
        (0xe6402c,'blr',('x8',)),
    ],
}

def audit(library: Path, manifest: Path, previous_report: Path):
    data=json.loads(manifest.read_text('utf8'))
    expected=next(row['sha256'] for row in data['libraries'] if row['name']=='libcocos2dcpp.so')
    with library.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest!=expected:
        raise ValueError('F34: hash da biblioteca incompatível com o APK original')
    prev=json.loads(previous_report.read_text('utf8'))
    if prev['phase']!=33 or prev['elf_sha256']!=digest or prev['verified_functions'][3]['name']!='Sector::GetSelectTargets':
        raise ValueError('F34: catalogo F33 incompatível')
    symbols={(name,int(addr,16),int(size)) for addr,size,name in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    relocation_text=command('readelf','-rW',str(library))
    virtual_dimensions={
        '0x24bdb18':'_ZNK6Entity17getPhysicalRadiusEv',
        '0x24bdb20':'_ZNK6Entity16getPhysicalRectAEv',
        '0x24bdb28':'_ZNK6Entity16getPhysicalRectBEv',
    }
    for address,symbol in virtual_dimensions.items():
        if not any((line.split() and line.split()[0].lstrip('0')==address[2:].lstrip('0')) and symbol in line
                   for line in relocation_text.splitlines()):
            raise ValueError('F34: vtable de dimensoes divergente: '+address)
    epsilon=read_float_va(library.read_bytes(),0x1e98550)
    if not 0.000099 < epsilon < 0.000101:
        raise ValueError('F34: tolerancia angular divergente')
    verified=[]
    for label,(symbol,start,size) in FUNCTIONS.items():
        if (symbol,start,size) not in symbols:raise ValueError('F34: simbolo divergente '+label)
        instr=instructions(command('llvm-objdump','-d',f'--start-address=0x{start:x}',f'--stop-address=0x{start+size:x}',str(library)))
        if set(instr)!=set(range(start,start+size,4)):
            raise ValueError('F34: desmontagem ARM64 incompleta: '+label)
        for address,opcode,parts in CHECKS[label]:check(label,instr,address,opcode,parts)
        verified.append({'name':label,'address':hex(start),'bytes':size,
                         'instructions':len(instr),'checks':len(CHECKS[label])})
    return {
        'phase':34,'apk_version':'1.0.1811','elf_sha256':digest,
        'verified_functions':verified,
        'verified_instructions':sum(x['instructions'] for x in verified),
        'checkpoints':sum(x['checks'] for x in verified),
        'vtable_dimension_relocations':virtual_dimensions,
        'angular_epsilon':epsilon,
        'callback':{
            'body_user_data_offset':'0xb0','entity_type_mask_offset':'0x20',
            'callback_type_mask_offset':'0x28','entity_shape_type_offset':'0x1a8',
            'shape_types':{'1':'circulo + Entity::getPhysicalRadius','2':'retangulo + getPhysicalRectA/B','3':'insercao direta'},
            'circle_boundary':'distancia quadrada estritamente menor que (raio busca+raio virtual)^2',
            'rect_boundary':'abs(dx),abs(dy) menores ou iguais a (raio busca+dimensao virtual*0.5)',
            'angle_boundary':'angulo acosDeg < trunc(largura do setor /2), depois de limite de vetor quase zero',
            'angle_epsilon_reference':'0x1e98550',
            'fixture_callback_continues':True,
        },
        'post_filter':{
            'function':'CSelectTargetSector::Filter',
            'condition_ids_offset':'0x28',
            'calls':['CConditionManager::GetCondition','CCondition::SetTargetEntitys',
                     'CCondition::SetCreateEntity','CCondition::SetBindSkill','condicao virtual +0x30'],
            'stops_when_target_vector_empty':True,
        },
        'confirmed_order':['b2World::QueryAABB', 'CSectorQueryCallback::ReportFixture',
                           'CSelectTargetSector::Filter (chamada virtual +0x8)'],
        'limits':[
            'Fixture pode ser aceita no callback mas eliminada pelos CCondition posteriores.',
            'Getters de dimensoes comprovados por vtable; valores concretos por entidade e fonte de colisores ainda exigem investigacao.',
            'A entidade de forma 3 entra diretamente na lista depois da mascara; nao passar pelo teste angular nao comprova dano.',
            'Sem prova de vinculo entre habilidade 4010020, seletor especifico e aplicacao de dano.',
            'A bancada Lua modela somente predicados estaticos confirmados, sem invocar Box2D nem efeitos.']
    }

def as_lua(data):
    return ('-- F34: filtro estatico confirmado, sem CCondition, dano ou combat loop.\n'
            'return {phase=34,verified_instructions='+str(data['verified_instructions'])+
            ',checkpoints='+str(data['checkpoints'])+
            ',shape_types={circle=1,rect=2,direct=3},'+
            ' mask_entity_offset="0x20",mask_callback_offset="0x28",'+
            'shape_offset="0x1a8",angular_epsilon=0.0001,conditions_resolved=false}\n')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    p.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    p.add_argument('--previous',type=Path,default=ROOT/'reports/sector_scope.json')
    p.add_argument('--json',type=Path,default=ROOT/'reports/sector_filter.json')
    p.add_argument('--lua',type=Path,default=ROOT/'reports/sector_filter.lua')
    args=p.parse_args()
    result=audit(args.library,args.manifest,args.previous)
    args.json.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    args.lua.write_text(as_lua(result),'utf8')
    print('F34:',result['verified_instructions'],'instr ARM64,',result['checkpoints'],'checagens, callback e post-filtro')
if __name__=='__main__':main()
