#!/usr/bin/env python3
"""F22: rastreia IDs exatos em configurações de habilidades do BarbarQ 1.0.1811.

Relações entre registros são CANDIDATAS: coincidência de token numérico não
prova que o campo execute o registro referenciado. O vínculo de botão do
arquivo functionbindskill é a única relação com colunas tipadas neste leitor.
O cache gerado contém descrições originais e NÃO deve ir para o GitHub público.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from catalogar_habilidades import TABLES, collect, lua_string, parse_table

ROOT = Path(__file__).resolve().parents[1]
EXTRA = ('selectcircle', 'selectrect', 'selectnearest', 'functionrepeat', 'functionbuff')
TABLE_SET = TABLES + EXTRA
# Apenas inteiros isolados de 4+ dígitos; 1, 2, 1001, etc. podem ser parâmetros.
TOKEN = re.compile(r'(?<!\S)\d{4,}(?!\S)')
FOCUS = (4010020, 4020020, 4070020, 4080020, 10037, 10052, 10070)
MAX_PREVIEW = 12


def trace(assets: Path, phase21_report: Path) -> tuple[dict, dict]:
    prior = json.loads(phase21_report.read_text(encoding='utf-8'))
    summary21, catalog = collect(assets)
    if summary21['table_sha256'] != prior['table_sha256']:
        raise ValueError('SHA-256 de tabela alterado desde a Fase 21')

    records: dict[int, dict] = {}
    checksums: dict[str, str] = {}
    for table in TABLE_SET:
        raw = (assets / 'configdata' / ('config.skill.' + table + '.txt')).read_bytes()
        checksums[table] = hashlib.sha256(raw).hexdigest()
        for ident, record in parse_table(raw, table).items():
            if ident in records:
                raise ValueError(f'ID presente em mais de uma tabela: {ident}')
            records[ident] = {**record, 'table': table}

    incoming = defaultdict(list)
    outgoing = defaultdict(list)
    per_source = defaultdict(set)
    for ident, record in records.items():
        # Token completo, sem unir números através de separadores ou substrings.
        for match in TOKEN.finditer(record['payload']):
            target = int(match.group())
            if target not in records or target in per_source[ident]:
                continue
            per_source[ident].add(target)
            incoming[target].append(ident)
            outgoing[ident].append(target)

    wanted = set(FOCUS)
    wanted.update(link['skill_id'] for link in catalog['links'])
    entries = {}
    for ident in sorted(wanted):
        record = records.get(ident)
        if record is None:
            raise ValueError(f'ID solicitado não encontrado: {ident}')
        sources = sorted(incoming[ident], key=lambda n: (records[n]['table'], n))
        targets = sorted(outgoing[ident], key=lambda n: (records[n]['table'], n))
        def references(ids):
            return [{'id': ref, 'table': records[ref]['table'],
                     'description': records[ref]['description']} for ref in ids[:MAX_PREVIEW]]
        entries[ident] = {
            'id': ident, 'table': record['table'], 'description': record['description'],
            'incoming_total': len(sources), 'outgoing_total': len(targets),
            'incoming': references(sources), 'outgoing': references(targets),
        }

    # Relações explícitas de botão são verificadas pelo parser F21.
    example = next(link for link in catalog['links'] if link['id'] == 10039)
    if (example['button'], example['skill_id']) != (2, 4010020):
        raise ValueError('Ligação original do bárbaro não reconhecida')
    if sorted(incoming[4010020]) != [10039]:
        raise ValueError('O grafo de referências do botão de ataque mudou')
    if outgoing[4010020]:
        raise ValueError('Configuração 4010020 mudou: investigar novamente a cadeia')
    if not {4070020, 4080020}.issubset(outgoing[10070]):
        raise ValueError('As variantes de animação não estão mais referenciadas')
    if 10052 not in outgoing[4020020]:
        raise ValueError('A referência ao seletor de setor não foi encontrada')

    report = {
        'phase': 22, 'apk_version': '1.0.1811',
        'tables': {t: summary21['tables'][t] if t in summary21['tables'] else
                   sum(1 for row in records.values() if row['table'] == t) for t in TABLE_SET},
        'table_sha256': checksums, 'indexed_records': len(records),
        'unique_reference_pairs': sum(map(len, outgoing.values())),
        'referenced_target_ids': len(incoming),
        'selected_skill_ids': len(wanted),
        'verified_binding': {'binding_id': 10039, 'button_code': 2, 'skill_id': 4010020},
        'example': {
            'skill_id': 4010020, 'incoming_ids': sorted(incoming[4010020]),
            'outgoing_ids': sorted(outgoing[4010020]),
            'sector_selector_id': 10052,
            'selector_mentioned_by_skill_id': 4020020,
            'random_animation_record_id': 10070,
            'random_animation_skill_ids': [4070020, 4080020],
        },
        'limits': ('As arestas são coincidências de tokens inteiros entre tabelas, NÃO vínculos de execução confirmados. '
                   'Apenas o formato dos campos de functionbindskill está interpretado. '
                   'O ID 4010020 não expõe ligações diretas para dano ou seleção de alvos nestas tabelas. '
                   'Não implementar dano, alcance ou cooldown com base neste índice.'),
    }
    return report, entries


def export_lua(entries: dict[int, dict]) -> str:
    lines = ['-- Cache privado gerado de tabelas originais do APK. NÃO publicar.', 'return {']
    for ident, row in sorted(entries.items()):
        lines.append(f' [{ident}] = {{ table={lua_string(row["table"])}, description={lua_string(row["description"])}, '
                     f'incoming_total={row["incoming_total"]}, outgoing_total={row["outgoing_total"]},')
        for direction in ('incoming', 'outgoing'):
            lines.append(f'  {direction}={{')
            for ref in row[direction]:
                lines.append('   {id=%d, table=%s, description=%s},' %
                             (ref['id'], lua_string(ref['table']), lua_string(ref['description'])))
            lines.append('  },')
        lines.append(' },')
    lines += ['}', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assets', type=Path, default=ROOT / 'assets_original')
    parser.add_argument('--previous', type=Path, default=ROOT / 'reports/skill_catalog_summary.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'cache/skill_trace.lua')
    parser.add_argument('--report', type=Path, default=ROOT / 'reports/skill_trace_summary.json')
    args = parser.parse_args()
    report, entries = trace(args.assets, args.previous)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(export_lua(entries), encoding='utf-8')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('F22:', report['indexed_records'], 'registros,', report['unique_reference_pairs'], 'pares numéricos candidatos')


if __name__ == '__main__':
    main()
