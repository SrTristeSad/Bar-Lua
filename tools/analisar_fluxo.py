#!/usr/bin/env python3
"""Bar-Lua F12: catálogo REPRODUZÍVEL de fluxos de controle ARM64 de funções selecionadas.

Examina o arquivo .so do APK fornecido pelo usuário, sem executar código Android.
Extrai somente metadados de fluxo e nomes de alvos; NÃO republica instruções/binários.
Exige llvm-objdump com suporte AArch64. O relatório não reconstrói o algoritmo.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

try:
    from tools.auditar_elf import verify_elf_header
except ModuleNotFoundError:
    from auditar_elf import verify_elf_header

# Assinaturas confirmadas em native_symbols.csv — não representar funções inventadas.
TARGETS = (
    'Hero::setStickDir(int)',
    'Hero::move_update(float)',
    'Hero::update(float)',
    'GameScene::updateStick()',
    'GameScene::updateLogicFrame(float)',
    'GameScene::processPursueFrame(int)',
    'GameScene::checkFrameFrequency(float)',
    'GameScene::afterPursueFrame()',
    'BattleNet::processFrameUpdate(pto::battle::SFrameUpdate*)',
    'CSkill::Update(float)',
)
LINE = re.compile(r'^\s*([0-9a-fA-F]+):\s+[0-9a-fA-F]{8}\s+([A-Za-z][\w.]*)\s*(.*?)\s*$')
TARGET = re.compile(r'\b0x([0-9a-fA-F]+)\s+<([^>]+)>')
MAX_FUNCTION_BYTES = 16384
MAX_SO_BYTES = 100 * 1024 * 1024


def catalog_symbols(path: Path) -> dict[str, dict]:
    with path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    result = {}
    for row in rows:
        if row['signature'] in TARGETS:
            if row['signature'] in result:
                raise ValueError('Símbolo duplicado: ' + row['signature'])
            size = int(row['size_bytes'])
            addr = int(row['virtual_address'], 16)
            if not 4 <= size <= MAX_FUNCTION_BYTES or addr <= 0 or size % 4:
                raise ValueError('Endereço ou tamanho suspeito: ' + row['signature'])
            result[row['signature']] = {**row, 'addr': addr, 'size': size}
    absent = set(TARGETS) - set(result)
    if absent:
        raise ValueError('Funções solicitadas ausentes do catálogo: ' + ', '.join(sorted(absent)))
    return result


def parse_disassembly(output: str, *, start: int, size: int):
    instructions = []
    end = start + size
    for line in output.splitlines():
        match = LINE.match(line)
        if not match:
            continue
        address = int(match.group(1), 16)
        if start <= address < end:
            instructions.append((address, match.group(2).lower(), match.group(3)))
    if not instructions:
        raise ValueError(f'Não foi possível decodificar código em 0x{start:x}')
    # Todas as instruções ARM64 têm 4 bytes; ausência de dados pode esconder chamadas.
    addresses = [item[0] for item in instructions]
    if addresses != list(range(start, end, 4)):
        raise ValueError(f'Desmontagem incompleta ou com endereços inválidos em 0x{start:x}')
    calls = Counter()
    branch_count = 0
    indirect_calls = 0
    returns = 0
    comparisons = 0
    for _, mnemonic, operands in instructions:
        if mnemonic == 'bl':
            m = TARGET.search(operands)
            if not m:
                raise ValueError('Chamada BL sem alvo imediato resolvido: ' + operands)
            # Símbolos externos incluem sufixo @plt.
            label = m.group(2)
            calls[(f'0x{int(m.group(1),16):x}', label)] += 1
        elif mnemonic in ('blr', 'blraa', 'blrab') or mnemonic.startswith('blra'):
            indirect_calls += 1
        if mnemonic == 'b' or mnemonic.startswith('b.') or mnemonic in ('cbz','cbnz','tbz','tbnz','br'):
            branch_count += 1
        if mnemonic.startswith('ret'):
            returns += 1
        if mnemonic in ('cmp', 'cmn', 'fcmp','tst'):
            comparisons += 1
    direct = [{'address': address, 'target': label, 'count': count,
               'external_plt': label.endswith('@plt')}
              for (address, label), count in sorted(calls.items(), key=lambda kv: (-kv[1], kv[0][1]))]
    return {'instruction_count': len(instructions), 'branch_instructions': branch_count,
            'comparisons': comparisons, 'returns': returns,
            'indirect_calls': indirect_calls, 'direct_calls': sum(calls.values()),
            'targets': direct}


def lua_quote(value: str) -> str:
    # JSON quoted UTF-8 strings are legal Lua strings except \u escapes (do not use ASCII escapes).
    return json.dumps(value, ensure_ascii=False)


def report_to_lua(report: dict) -> str:
    out = ['-- Gerado automaticamente a partir de análise ARM64 estática; sem código executável do APK.', 'return {']
    for f in report['functions']:
        out.extend(['  {', f'    name={lua_quote(f["signature"])},',
                    f'    address={lua_quote(f["address"])},',
                    f'    bytes={f["bytes"]}, instructions={f["instruction_count"]},',
                    f'    direct={f["direct_calls"]}, indirect={f["indirect_calls"]},',
                    f'    branches={f["branch_instructions"]}, comparisons={f["comparisons"]},',
                    '    calls={'])
        for target in f['targets']:
            out.append('      {name=%s, address=%s, count=%d, external=%s},' %
                       (lua_quote(target.get('display', target['target'])), lua_quote(target['address']),
                        target['count'], 'true' if target['external_plt'] else 'false'))
        out.extend(['    },', '  },'])
    out.append('}')
    return '\n'.join(out) + '\n'


def analyze(so_data: bytes, catalog: dict[str, dict], objdump: str):
    verify_elf_header(so_data)
    if len(so_data) > MAX_SO_BYTES:
        raise ValueError('ELF maior que limite de segurança')
    with tempfile.TemporaryDirectory(prefix='barlua-f12-') as temp:
        path = Path(temp) / 'cocos.so'
        path.write_bytes(so_data)
        functions = []
        for signature in TARGETS:
            sym = catalog[signature]
            args = [objdump, '-d', f'--start-address=0x{sym["addr"]:x}',
                    f'--stop-address=0x{sym["addr"] + sym["size"]:x}', str(path)]
            proc = subprocess.run(args, text=True, capture_output=True, timeout=35, check=True)
            stats = parse_disassembly(proc.stdout, start=sym['addr'], size=sym['size'])
            functions.append({'signature': signature, 'address': f'0x{sym["addr"]:x}',
                              'bytes': sym['size'], **stats})
    # Demangle nomes C++ para tornar o catálogo legível (mantém o nome ELF original).
    names = sorted({target['target'] for entry in functions for target in entry['targets']})
    if names:
        readable = subprocess.run(['c++filt'], input='\n'.join(names)+'\n', text=True,
                                  capture_output=True, check=True, timeout=30).stdout.splitlines()
        if len(readable) != len(names):
            raise ValueError('c++filt retornou quantidade inconsistente')
        lookup = dict(zip(names, readable))
        for entry in functions:
            for item in entry['targets']:
                item['display'] = lookup[item['target']]
    return {'source': 'ELF AArch64 .text; disassembly static llvm-objdump; direct calls only',
            'sha256_libcocos2dcpp': hashlib.sha256(so_data).hexdigest(),
            'limitations': 'Chamada direta não comprova que foi executada; BLR/vtables e inlining não identificados; parâmetros e algoritmos não recuperados.',
            'functions': functions}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apk', required=True, type=Path)
    p.add_argument('--symbols', default='reports/native_symbols.csv', type=Path)
    p.add_argument('--manifest', default='reports/native_arm64.json', type=Path)
    p.add_argument('--out', default='reports', type=Path)
    p.add_argument('--objdump', default='llvm-objdump')
    a = p.parse_args()
    tool = shutil.which(a.objdump)
    if tool is None:
        p.error('llvm-objdump não encontrado (instale LLVM no Windows/WSL)')
    expected = next(x['sha256'] for x in json.loads(a.manifest.read_text(encoding='utf-8'))['libraries']
                    if x['name'] == 'libcocos2dcpp.so')
    with ZipFile(a.apk) as z:
        info = z.getinfo('lib/arm64-v8a/libcocos2dcpp.so')
        if info.file_size > MAX_SO_BYTES:
            raise ValueError('ELF grande demais')
        data = z.read(info)
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('Hash do ELF não corresponde à Fase 11 (não misture versões do APK)')
    report = analyze(data, catalog_symbols(a.symbols), tool)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out/'native_flow.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (a.out/'native_flow.lua').write_text(report_to_lua(report), encoding='utf-8')
    print('Funções:', len(report['functions']))
    for f in report['functions']:
        print(f['signature'], f['instruction_count'], 'instruções;', f['direct_calls'],
              'chamadas diretas;', f['indirect_calls'], 'indiretas')


if __name__ == '__main__':
    main()