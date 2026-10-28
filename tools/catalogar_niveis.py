#!/usr/bin/env python3
"""F29: catálogo estrutural de níveis do APK BarbarQ 1.0.1811.

Relaciona IDs e slots pela ordem no TXT. Na F30, HeroConfig::load comprova
essa ordem, e o offset +0x44 foi identificado como HP inicial. Os outros
sete slots ainda nao devem ser rotulados ataque, defesa ou velocidade.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from catalogar_habilidades import parse_table, lua_string

ROOT = Path(__file__).resolve().parents[1]
SLOTS = ('0x38', '0x3c', '0x40', '0x44', '0x48', '0x4c', '0x50', '0x54')
HERO_TABLE = 'config.hero.heroconfig.txt'
ENTITY_TABLE = 'config.hero.entityconfig.txt'
EXPECTED_SHA256 = {
    HERO_TABLE: '33402fa701f4fd425779868cd805c11e9ae88cce74bf298331715035aff6d3a5',
    ENTITY_TABLE: '159248ff64a1852707abbb28cec748ceaf870ae126c26fbcfeed1f8efb6bfb8e',
}


def parse_hero(record: dict) -> dict:
    tokens=record['payload'].split()
    if len(tokens)<10 or not all(x.lstrip('-').isdigit() for x in tokens[:9]):
        raise ValueError('configuração de herói não tem campos numéricos esperados')
    # 0: ID de recurso; 1-8: valores que correspondem posicionalmente
    # às oito posições consecutivas observadas no struct HeroConfig.
    values={slot:int(tokens[i+1]) for i,slot in enumerate(SLOTS)}
    if not all(-2147483648 <= x <= 2147483647 for x in values.values()):
        raise ValueError('slot fora do int32')
    return {'resource_id':int(tokens[0]),'values':values}


def build_tables(assets: Path) -> tuple[dict,dict]:
    folder=assets/'configdata'
    herobytes=(folder/HERO_TABLE).read_bytes()
    entitybytes=(folder/ENTITY_TABLE).read_bytes()
    for name,data in ((HERO_TABLE,herobytes),(ENTITY_TABLE,entitybytes)):
        if hashlib.sha256(data).hexdigest()!=EXPECTED_SHA256[name]:
            raise ValueError('F29: SHA256 divergente em '+name+'; esperado APK 1.0.1811')
    heroes=parse_table(herobytes,'hero.heroconfig')
    entities=parse_table(entitybytes,'hero.entityconfig')
    parsed={k:parse_hero(v) for k,v in heroes.items()}
    groups=[]
    seen=set()
    missing=[]
    for entity_id,record in sorted(entities.items()):
        words=record['payload'].split()
        if len(words)<2 or not words[1].isdigit():
            continue
        base=int(words[1])
        if base not in parsed:
            missing.append({'entity_id':entity_id,'config_id':base})
            continue
        if base in seen:
            continue
        seen.add(base)
        label=heroes[base]['description']
        levels=[]
        for level in range(1,101):
            config_id=base+(level-1)*10000
            row=heroes.get(config_id)
            # Não ultrapassar fronteiras de personagens só porque os IDs colidem.
            if row is None or row['description']!=label:
                break
            levels.append({'level':level,'id':config_id,'values':parsed[config_id]['values']})
        groups.append({'entity_id':entity_id,'base_id':base,'name':label,'levels':levels})
    groups.sort(key=lambda item:item['base_id'])
    hashes={HERO_TABLE:hashlib.sha256(herobytes).hexdigest(), ENTITY_TABLE:hashlib.sha256(entitybytes).hexdigest()}
    summary={'phase':29,'version':'1.0.1811','source_sha256':hashes,
             'hero_records':len(heroes),'entity_records':len(entities),
             'group_count':len(groups),'missing_entity_config_count':len(missing),
             'groups_with_multiple_levels':sum(len(g['levels'])>1 for g in groups),
             'total_level_entries':sum(len(g['levels']) for g in groups),
             'slots':list(SLOTS),'confirmed_example':{
                 'entity_id':210000,'base_config_id':210001,
                 'level_1_0x38':parsed[210001]['values']['0x38'],
                 'level_2_0x38':parsed[220001]['values']['0x38'],
                 'level_3_0x38':parsed[230001]['values']['0x38']},
             'status':('Os 8 campos são associados por ordem textual; o código ARM64 '
                       'confirma leitura em 0x38..0x54 e destino dos primeiros 7 em Hero. '
                       'Não há prova independente da semântica HP/ataque/defesa/velocidade.'),
             'limits':'Sequências são cortadas quando muda o nome na tabela. Aliases de entidade podem compartilhar uma configuração; nem todo modo usa a mesma progressão. Nenhum atributo de combate é alterado.'}
    if summary['confirmed_example']['level_1_0x38']!=195 or summary['confirmed_example']['level_2_0x38']!=200:
        raise ValueError('sentinelas do bárbaro divergentes')
    return summary,{'groups':groups,'slots':list(SLOTS)}


def lua_export(catalog:dict)->str:
    out=['-- Dados de heróis extraídos do APK do usuário. NÃO publicar no GitHub.', 'return {', '  slots={'+','.join(lua_string(s) for s in catalog['slots'])+'},','  groups={']
    for g in catalog['groups']:
        out.append('    {name='+lua_string(str(g['base_id'])+' '+g['name'])+',entity_id='+str(g['entity_id'])+',base_id='+str(g['base_id'])+',levels={')
        for row in g['levels']:
            vals=','.join('['+lua_string(s)+']='+str(row['values'][s]) for s in SLOTS)
            out.append('      {level='+str(row['level'])+',id='+str(row['id'])+',values={'+vals+'}},')
        out.append('    }},')
    out.extend(['  },','}',''])
    return '\n'.join(out)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--assets',type=Path,default=ROOT/'assets_original')
    p.add_argument('--cache',type=Path,default=ROOT/'cache/hero_levels.lua')
    p.add_argument('--report',type=Path,default=ROOT/'reports/hero_level_catalog.json')
    opts=p.parse_args()
    summary,catalog=build_tables(opts.assets)
    opts.cache.parent.mkdir(parents=True,exist_ok=True)
    opts.cache.write_text(lua_export(catalog),encoding='utf-8')
    opts.report.parent.mkdir(parents=True,exist_ok=True)
    opts.report.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'F29: {summary["hero_records"]} configurações, {summary["group_count"]} séries, {summary["groups_with_multiple_levels"]} multiníveis')

if __name__=='__main__':main()
