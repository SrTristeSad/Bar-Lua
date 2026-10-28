#!/usr/bin/env python3
"""F29: cruza os slots numéricos da config com Hero::init/reInit/getValueByType.

Audita opcodes ARM64 e símbolo/tamanho no ELF com SHA-256 fixado ao APK.
O nome funcional dos slots continua não recuperado.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from analisar_valores_vida import command,instructions,SYMBOL
ROOT=Path(__file__).resolve().parents[1]
FUNCTIONS={
 'Hero::init':('_ZN4Hero4initEPKN6config4hero10HeroConfigERKN6Entity11DataForInitE',0xe56734,700),
 'Hero::reInit':('_ZN4Hero6reInitEib',0xe569f0,1432),
 'Hero::getValueByType':('_ZNK4Hero14getValueByTypeEN6config5skill9ValueTypeEfPKNS1_9OperationE',0xe58af8,652),
}
# Verificações de transferência entre offsets da config (x21/x20) e herói (x19/x20).
CHECKS={
 'Hero::init':[
 (0xe56780,'ldr',('w8','[x21, #0x38]')),
 (0xe56784,'str',('w8','[x19, #0xc0]')),
 (0xe56788,'ldr',('w8','[x21, #0x3c]')),
 (0xe5678c,'str',('w8','[x19, #0x32c]')),
 (0xe56790,'ldr',('w8','[x21, #0x40]')),
 (0xe56794,'str',('w8','[x19, #0x330]')),
 (0xe56798,'ldr',('w8','[x21, #0x44]')),
 (0xe567a0,'str',('w8','[x19, #0x310]')),
 (0xe567a4,'ldr',('w8','[x21, #0x48]')),
 (0xe567a8,'str',('w8','[x19, #0x328]')),
 (0xe567ac,'ldr',('w9','[x21, #0x4c]')),
 (0xe567b0,'str',('w9','[x19, #0x31c]')),
 (0xe567b8,'ldr',('w9','[x21, #0x50]')),
 (0xe567bc,'str',('w9','[x19, #0x1b8]')),
 (0xe567e0,'ldr',('w11','[x21, #0x54]')),
 ],
 'Hero::reInit':[
 (0xe56af4,'ldr',('w8','[x20, #0x38]')),
 (0xe56af8,'ldr',('w9','[x21, #0x38]')),
 (0xe56b04,'sub',('w8','w8','w9')),
 (0xe56b0c,'str',('w8','[x19, #0xc0]')),
 (0xe56b10,'ldr',('w8','[x20, #0x3c]')),
 (0xe56b28,'ldr',('w8','[x20, #0x40]')),
 (0xe56b3c,'ldp',('w8','w9','[x20, #0x44]')),
 (0xe56b60,'ldr',('w10','[x20, #0x4c]')),
 (0xe56c1c,'ldr',('w8','[x20, #0x50]')),
 ],
 'Hero::getValueByType':[
 (0xe58b10,'sub',('w8','w1','#0x2')),
 (0xe58b3c,'ldr',('s0','[x20, #0x32c]')),
 (0xe58b5c,'ldr',('s0','[x20, #0x330]')),
 (0xe58b64,'ldr',('s0','[x20, #0x314]')),
 (0xe58b6c,'ldr',('s0','[x20, #0x318]')),
 (0xe58b74,'ldr',('s0','[x20, #0xe0]')),
 (0xe58b7c,'ldr',('s0','[x20, #0x310]')),
 (0xe58c58,'ldr',('s0','[x20, #0x328]')),
 (0xe58c68,'ldr',('s0','[x20, #0x33c]')),
 (0xe58cc8,'ldr',('s0','[x20, #0x36c]')),
 ],
}

def validate(name,decoded):
    _,base,size=FUNCTIONS[name]
    if set(decoded)!=set(range(base,base+size,4)):
        raise ValueError('F29: região ARM64 incompleta '+name)
    for addr,op,parts in CHECKS[name]:
        actual,operands=decoded.get(addr,('',''))
        if actual!=op or not all(piece in operands for piece in parts):
            raise ValueError('F29: checkpoint divergente '+name+': '+hex(addr)+': '+str((actual,operands)))

def audit(binary:Path,manifest:Path):
    info=json.loads(manifest.read_text('utf-8'))
    expected=next(p['sha256'] for p in info['libraries'] if p['name']=='libcocos2dcpp.so')
    with binary.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest!=expected:raise ValueError('F29: SHA256 divergente; esperado BarbarQ 1.0.1811')
    symbols={(name,int(addr,16),int(size)) for addr,size,name in SYMBOL.findall(command('readelf','-Ws',str(binary)))}
    records=[]
    for name,(mangled,addr,size) in FUNCTIONS.items():
        if (mangled,addr,size) not in symbols:raise ValueError('F29: símbolo ausente '+name)
        decoded=instructions(command('llvm-objdump','-d',f'--start-address=0x{addr:x}',f'--stop-address=0x{addr+size:x}',str(binary)))
        validate(name,decoded)
        records.append({'name':name,'address':hex(addr),'bytes':size,'instructions':len(decoded),'checks':len(CHECKS[name])})
    return {'phase':29,'apk_version':'1.0.1811','library_sha256':digest,
            'functions':records,'total_instructions':sum(r['instructions'] for r in records),
            'total_checks':sum(r['checks'] for r in records),
            'config_offset_slots':['0x38','0x3c','0x40','0x44','0x48','0x4c','0x50','0x54'],
            'facts':{
                'init':'Atribui campos da configuração HeroConfig em offsets 0x38..0x50 ao estado do herói, com duplicações para alguns slots.',
                'reinit':'No caminho incremental faz diferença entre configurações antiga e nova para os slots verificados.',
                'get_value':'Hero::getValueByType contém leitura de vários atributos em offsets internos, selecionada por ValueType.',
                'semantics':'Os nomes dos atributos e correspondência exata ValueType não foram identificados. Sem fórmulas de HP/ataque/defesa/velocidade.'},
            'limits':'A disposição textual do TXT e a disposição binária do struct são correlacionadas por ordem; o ELF isoladamente não prova esse alinhamento nem o nome dos campos.'}

def lua_report(rep):
    out=['-- F29: inspeção read-only verificada contra ELF; não é cálculo de combate','return {',
         '  total_instructions='+str(rep['total_instructions'])+',',
         '  total_checks='+str(rep['total_checks'])+',','  functions={']
    for f in rep['functions']:
        out.append('    {name="'+f['name']+'",address="'+f['address']+'",instructions='+str(f['instructions'])+'},')
    out+=['  },','}','']
    return '\n'.join(out)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    p.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    p.add_argument('--json',type=Path,default=ROOT/'reports/hero_attr_arm64.json')
    p.add_argument('--lua',type=Path,default=ROOT/'reports/hero_attr_arm64.lua')
    a=p.parse_args()
    rep=audit(a.library,a.manifest)
    a.json.parent.mkdir(parents=True,exist_ok=True)
    a.json.write_text(json.dumps(rep,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    a.lua.write_text(lua_report(rep),encoding='utf-8')
    print('F29: %d instruções, %d checkpoints'%(rep['total_instructions'],rep['total_checks']))
if __name__=='__main__':main()
