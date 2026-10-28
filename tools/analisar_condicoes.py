#!/usr/bin/env python3
"""F35: audita o ciclo de CCondition, pacotes e limite de alvos no ELF do APK.

A análise é somente-leitura. Não infere classes concretas por registros nem
transforma o filtro de candidatos em combate real.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from analisar_valores_vida import SYMBOL, command, instructions
from analisar_esquema_heroi import check

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = {
    'CCondition::GetTargetResult': ('_ZN10CCondition15GetTargetResultEv',0xe44428,148),
    'CCondition::FilterTarget': ('_ZN10CCondition12FilterTargetEv',0xe444bc,188),
    'CPackCondition::FilterTarget': ('_ZN14CPackCondition12FilterTargetEv',0xe454b0,160),
    'CTargetsCountCondition::FilterTarget': ('_ZN22CTargetsCountCondition12FilterTargetEv',0xe45098,320),
    'CConditionManager::GetCondition': ('_ZNK17CConditionManager12GetConditionEi',0xe45b5c,116),
}
CHECKS = {
    'CCondition::GetTargetResult': [
        (0xe44448,'lsr',('x9','x9','#4')),
        (0xe44474,'ldr',('x9','[x9, #0x20]')),
        (0xe44480,'blr',('x9',)),
        (0xe44488,'tbz',('w8','#0x0')),
        (0xe44498,'orr',('w0','wzr','#0x1')),
        (0xe444a8,'mov',('w0','wzr')),
    ],
    'CCondition::FilterTarget': [
        (0xe444dc,'lsr',('x21','x10','#4')),
        (0xe444f0,'ldr',('x9','[x9, #0x20]')),
        (0xe444fc,'blr',('x9',)),
        (0xe44504,'tbnz',('w8','#0x0')),
        (0xe44518,'ldr',('w10','[x0, #-0x10]!')),
        (0xe44528,'str',('w10','[x22]')),
        (0xe44530,'bl',('GetEntity',)),
        (0xe44534,'str',('x0','[x22, #0x8]')),
        (0xe44544,'str',('x9','[x8, #0x8]')),
        (0xe44564,'cset',('w0','ne')),
    ],
    'CPackCondition::FilterTarget': [
        (0xe454c4,'ldr',('x8','[x19, #0x38]')),
        (0xe454d4,'lsr',('x21','x8','#2')),
        (0xe454fc,'bl',('GetCondition',)),
        (0xe45504,'str',('x8','[x0, #0x28]')),
        (0xe4550c,'str',('x8','[x0, #0x20]')),
        (0xe45518,'str',('x8','[x0, #0x30]')),
        (0xe45520,'blr',('x8',)),
        (0xe4553c,'cset',('w0','ne')),
    ],
    'CTargetsCountCondition::FilterTarget': [
        (0xe450d0,'ldr',('w10','[x19, #0x38]')),
        (0xe450dc,'cmp',('w10','w20')),
        (0xe450e4,'ldrb',('w11','[x19, #0x3c]')),
        (0xe450fc,'bl',('Instance',)),
        (0xe45114,'bl',('__NextInt',)),
        (0xe45130,'ldr',('q0','[x8, x9]')),
        (0xe45134,'str',('q0','[x8, x22]')),
        (0xe451a4,'str',('x9','[x0, #0x8]')),
        (0xe451b0,'cset',('w0','ne')),
    ],
    'CConditionManager::GetCondition': [
        (0xe45ba4,'msub',('w8','w8','w10','w1')),
        (0xe45bac,'ldr',('x19','[x11, w8, sxtw #3]')),
        (0xe45bb4,'ldr',('x8','[x8, #0x10]')),
        (0xe45bbc,'blr',('x8',)),
    ],
}
TABLES = [
    'conditionbuff','conditioncamp','conditionentitytype','conditionpack',
    'conditionskillentitytype','conditiontargetscount','conditionvaluecompare'
]

def parse_lines(raw: bytes):
    """Interpreta o cabeçalho ``id comprimento_em_BYTES nome_utf8``; preserva cauda opaca."""
    entries=[]
    for lineno, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        fields=line.split(b' ',2)
        if len(fields)!=3:
            raise ValueError(f'F35: campos ausentes na linha {lineno}')
        try:
            item_id=int(fields[0]); length=int(fields[1])
        except ValueError as exc:
            raise ValueError(f'F35: cabecalho invalido na linha {lineno}') from exc
        if item_id<0 or length<0 or len(fields[2])<length:
            raise ValueError(f'F35: comprimento invalido na linha {lineno}')
        remainder=fields[2]
        if remainder[length:length+1] not in (b'',b' '):
            raise ValueError(f'F35: delimitador invalido na linha {lineno}')
        name=remainder[:length].decode('utf8')
        tail=remainder[length:].strip().decode('utf8')
        entries.append({'id':item_id,'name':name,'parameters':tail})
    if len({x['id'] for x in entries}) != len(entries):
        raise ValueError('F35: IDs duplicados na tabela')
    return entries


def audit(library:Path,manifest:Path,previous:Path,tables:Path):
    meta=json.loads(manifest.read_text('utf8'))
    expected=next(x['sha256'] for x in meta['libraries'] if x['name']=='libcocos2dcpp.so')
    with library.open('rb') as f:
        digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest!=expected:
        raise ValueError('F35: ELF divergente da versao original 1.0.1811')
    prev=json.loads(previous.read_text('utf8'))
    if prev['phase']!=34 or prev['elf_sha256']!=digest:
        raise ValueError('F35: relatorio F34 ausente ou divergente')
    syms={(name,int(addr,16),int(size)) for addr,size,name in SYMBOL.findall(command('readelf','-Ws',str(library)))}
    ver=[]
    for label,(symbol,start,size) in FUNCTIONS.items():
        if (symbol,start,size) not in syms:
            raise ValueError('F35: simbolo ARM64 divergente: '+label)
        code=instructions(command('llvm-objdump','-d',f'--start-address=0x{start:x}',f'--stop-address=0x{start+size:x}',str(library)))
        if set(code)!=set(range(start,start+size,4)):
            raise ValueError('F35: funcao parcialmente decodificada: '+label)
        for a,op,parts in CHECKS[label]:
            check(label,code,a,op,parts)
        ver.append({'name':label,'address':hex(start),'size':size,'instructions':len(code),'checks':len(CHECKS[label])})
    configs={}
    for stem in TABLES:
        name='config.skill.'+stem+'.txt'
        raw=(tables/name).read_bytes()
        rows=parse_lines(raw)
        configs[stem]={'count':len(rows),'sha256':hashlib.sha256(raw).hexdigest()}
    return {
        'phase':35,'apk_version':'1.0.1811','elf_sha256':digest,
        'verified_functions':ver,'verified_instructions':sum(x['instructions'] for x in ver),
        'checkpoints':sum(x['checks'] for x in ver),'table_summaries':configs,
        'confirmed_rules':[
            'GetTargetResult (base): avalia todos os CSkillEntity e retorna falso ao primeiro predicado falso; vetor vazio retorna verdadeiro.',
            'FilterTarget (base): remove candidato reprovado substituindo-o pelo ultimo elemento do vetor; ordem dos alvos nao preservada.',
            'CPackCondition::FilterTarget: consulta cada ID do pacote, compartilha vetor e contextos e executa seu FilterTarget virtual na sequencia.',
            'CTargetsCountCondition::FilterTarget: se n<total, redimensiona vetor para n; modo aleatorio realiza trocas antes do corte.',
            'CSelectTargetSector::Filter (F34): para a cadeia quando a lista de alvos fica vazia.'
        ],
        'limits':[
            'Nao se reproduz ainda o significado de ContainType nem as sete subclasses concretas de condicao.',
            'Nao foi reproduzida a sequencia de RandNum::__NextInt para limites aleatorios.',
            'Os arquivos originais completos e nomes de configuracao permanecem apenas no cache privado, nao no GitHub.',
            'Nao ha prova de que habilidade 4010020 utilize algum pacote de condicoes especifico.',
            'A demonstracao Lua nao seleciona alvos finais, nao aplica dano e nao integra fisica.'
        ]
    }


def as_lua(data):
    return ('-- F35: evidencias de filtragem, sem efeitos de habilidade nem dados completos do APK.\n'
            'return {phase=35,verified_instructions='+str(data['verified_instructions'])+
            ',checkpoints='+str(data['checkpoints'])+
            ',tables='+str(len(data['table_summaries']))+',predicates_resolved=false,random_selection_resolved=false}\n')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--library',type=Path,default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    parser.add_argument('--manifest',type=Path,default=ROOT/'reports/native_arm64.json')
    parser.add_argument('--previous',type=Path,default=ROOT/'reports/sector_filter.json')
    parser.add_argument('--tables',type=Path,default=ROOT/'assets_original/configdata')
    parser.add_argument('--json',type=Path,default=ROOT/'reports/condition_flow.json')
    parser.add_argument('--lua',type=Path,default=ROOT/'reports/condition_flow.lua')
    args=parser.parse_args()
    data=audit(args.library,args.manifest,args.previous,args.tables)
    args.json.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    args.lua.write_text(as_lua(data),encoding='utf-8')
    print('F35:',data['verified_instructions'],'instrucoes;',data['checkpoints'],'checks;',sum(x['count'] for x in data['table_summaries'].values()),'registros')

if __name__=='__main__':main()
