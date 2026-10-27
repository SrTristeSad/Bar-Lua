#!/usr/bin/env python3
"""Auditoria estática F13: prova de instruções e constantes ARM64 do movimento.

Uso: python tools/analisar_movimento.py --apk caminho.apk [--out reports]
Sem executar binários Android, sem armazenar bytes de executável no relatório.
Só analisa a versão cujo hash consta no relatório nativo da F11.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile

ELF_FILE = 'lib/arm64-v8a/libcocos2dcpp.so'
EXPECTED = ('GameScene::updateStick()', 'Hero::move_update(float)',
            'Hero::getMoveDirection()', 'Hero::setStickDir(int)', 'Hero::setSpeed(int)')
# Endereços de constantes lidas nas instruções (VAs, não offsets fixos de arquivo).
CONSTANTS = {'speed_divisor': 0x1e98098, 'radian_divisor': 0x1e9d6bc,
             'degrees_multiplier': 0x1e98554}
PATTERNS = {
    'GameScene::updateStick()': (
        r'\bmov\s+w13,\s*#0x5a\b',  # 90
        r'\bmov\s+w14,\s*#0xb4\b',  # 180
        r'\bmov\s+w13,\s*#0x10e\b', # 270
        r'\bsdiv\s+w8,\s*w9,\s*w8\b',
        r'\bfcvtzs\s+w8,\s*s0\b',
        r'\bmov\s+w21,\s*#0x59\b', # 89
        r'\bmov\s+w9,\s*#0x2c\b',   # 44
        r'\bstr\s+w21,\s*\[x20,\s*#0x2c\]',
        r'\bstr\s+w8,\s*\[x20,\s*#0x28\]',
        r'COperateMessage__ThumbnailMove',
        r'BattleNet.*SendCmd',
    ),
    'Hero::move_update(float)': (
        r'\bldr\s+s0,\s*\[x19,\s*#0x328\]',
        r'\bldr\s+s0,\s*\[x19,\s*#0xd8\]',
        r'\bldr\s+s0,\s*\[x19,\s*#0xdc\]',
        r'WildsMathUtils.*cosDeg', r'WildsMathUtils.*sinDeg',
        r'Hero.*getMoveDirection', r'Entity.*move',
    ),
    'Hero::getMoveDirection()': (
        r'\bldr\s+w8,\s*\[x19,\s*#0x320\]',
        r'\bldr\s+w0,\s*\[x19,\s*#0x324\]',
        r'Entity.*GetEntityPositonAngle',
    ),
    'Hero::setStickDir(int)': (r'\bstr\s+w1,\s*\[x0,\s*#0x324\]',),
    'Hero::setSpeed(int)': (r'\bstr\s+w1,\s*\[x0,\s*#0x328\]',),
}


def read_float_va(data: bytes, address: int) -> float:
    """Resolve VA através da tabela ELF64 PT_LOAD, nunca por offset assumido."""
    if data[:6] != b'\x7fELF\x02\x01':
        raise ValueError('ELF64 little-endian esperado')
    phoff = struct.unpack_from('<Q', data, 0x20)[0]
    entry_bytes, n = struct.unpack_from('<HH', data, 0x36)
    if n > 128 or entry_bytes < 56 or phoff + entry_bytes * n > len(data):
        raise ValueError('Tabela ELF inválida')
    for i in range(n):
        kind, flags, offset, va, _, filesz, _, _ = struct.unpack_from('<IIQQQQQQ', data, phoff + i * entry_bytes)
        if kind == 1 and va <= address and address + 4 <= va + filesz:
            filepos = offset + address - va
            if filepos + 4 > len(data):
                raise ValueError('Constante fora dos limites')
            return struct.unpack_from('<f', data, filepos)[0]
    raise ValueError(f'Endereço não mapeado 0x{address:x}')


def verify_asm(signature: str, asm: str) -> list[str]:
    expected = PATTERNS[signature]
    missing = [pattern for pattern in expected if not re.search(pattern, asm)]
    if missing:
        raise ValueError(f'{signature}: evidência ausente: {missing}')
    return list(expected)


def load_symbols(csv_path: Path):
    with csv_path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    found = {r['signature']: r for r in rows if r['signature'] in EXPECTED}
    if len(found) != len(EXPECTED):
        raise ValueError('Símbolos ARM64 necessários ausentes do relatório')
    for signature, row in found.items():
        size, address = int(row['size_bytes']), int(row['virtual_address'], 16)
        if size % 4 or not (4 <= size <= 16384) or address < 0:
            raise ValueError('Região ELF inválida para ' + signature)
    return found


def analyze(apk: Path, symbols: Path, manifest: Path, objdump: str) -> dict:
    expected_hash = next(x['sha256'] for x in json.loads(manifest.read_text(encoding='utf-8'))['libraries']
                         if x['name'] == 'libcocos2dcpp.so')
    with ZipFile(apk) as z:
        entry = z.getinfo(ELF_FILE)
        if entry.file_size > 100 * 1024 * 1024:
            raise ValueError('Biblioteca maior que limite de segurança')
        data = z.read(entry)
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_hash:
        raise ValueError('Hash ELF diferente: análise recusada')
    constants = {name: read_float_va(data, address) for name, address in CONSTANTS.items()}
    if constants['speed_divisor'] != 100.0 or constants['degrees_multiplier'] != 180.0 or not math.isclose(constants['radian_divisor'], math.pi, rel_tol=1e-6):
        raise ValueError('Constantes incompatíveis com análise F13')
    catalog = load_symbols(symbols)
    findings = []
    with tempfile.TemporaryDirectory(prefix='barlua-f13-') as d:
        path = Path(d) / 'original_arm64.so'
        path.write_bytes(data)
        for signature in EXPECTED:
            row = catalog[signature]
            address, size = int(row['virtual_address'], 16), int(row['size_bytes'])
            proc = subprocess.run([objdump, '-d', f'--start-address=0x{address:x}',
                                   f'--stop-address=0x{address+size:x}', str(path)],
                                  capture_output=True, text=True, timeout=35, check=True)
            matched = verify_asm(signature, proc.stdout)
            findings.append({'signature': signature, 'address': f'0x{address:x}',
                             'size_bytes': size, 'patterns_verified': len(matched)})
    return {
        'apk_version': '1.0.1811', 'sha256_libcocos2dcpp': digest,
        'verification': 'instruction patterns matched and PT_LOAD constants decoded; static evidence only',
        'constants': constants,
        'fields': {'hero_speed': '0x328', 'hero_secondary_speed': '0xd8',
                   'hero_facing': '0xdc', 'hero_stick_dir': '0x324',
                   'message_sequence': '0x28', 'message_direction': '0x2c'},
        'observations': [
            'updateStick contains discrete 90/180/270 degree weighted arithmetic and a division by sum',
            'updateStick uses a special direction -1, 0->89, 180->44 and divides other angles in four-degree units',
            'new move message is sent if resulting code differs from last global code',
            'message direction stored at +0x2c, sequence at +0x28; BattleNet sequence advances by two',
            'move_update computes sum of two vector components using cosDeg/sinDeg and speed fields divided by 100',
            'Entity::move invoked with computed components; downstream integration and collisions unknown',
        ],
        'limitations': ['four direction slots not semantically named', 'no full packet schema, transport or server reproduced',
                        'no verified physics/collisions, acceleration, or frame-rate interpretation',
                        'floating point rounding may differ between Lua doubles and ARM64 floats'],
        'functions': findings,
    }


def report_to_lua(report):
    def q(s): return json.dumps(str(s), ensure_ascii=False)
    out = ['-- F13: metadados de engenharia reversa, não binário proprietário.','return {']
    out.append(f'  version={q(report["apk_version"])},')
    for key, value in report['constants'].items():
        out.append(f'  {key}={value:.9g},')
    out.append('  functions={')
    for f in report['functions']:
        out.append('    {name=%s, address=%s, bytes=%s, checks=%s},' % (
            q(f['signature']), q(f['address']), f['size_bytes'], f['patterns_verified']))
    out.extend(['  },', '}'])
    return '\n'.join(out) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--symbols', type=Path, default=Path('reports/native_symbols.csv'))
    parser.add_argument('--manifest', type=Path, default=Path('reports/native_arm64.json'))
    parser.add_argument('--out', type=Path, default=Path('reports'))
    parser.add_argument('--objdump', default='llvm-objdump')
    args = parser.parse_args()
    binary = shutil.which(args.objdump)
    if not binary:
        parser.error('llvm-objdump não encontrado')
    r = analyze(args.apk, args.symbols, args.manifest, binary)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'native_movement.json').write_text(json.dumps(r, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    (args.out / 'native_movement.lua').write_text(report_to_lua(r), encoding='utf-8')
    print('Padrões ARM64 confirmados:', sum(f['patterns_verified'] for f in r['functions']),
          'em', len(r['functions']), 'funções; constantes:', r['constants'])

if __name__ == '__main__':
    main()