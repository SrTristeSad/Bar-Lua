#!/usr/bin/env python3
"""F14: audita Entity::move(float,float) da biblioteca ARM64 conhecida.

Lê o APK local, valida SHA-256, símbolos, instruções selecionadas e floats em
PT_LOAD. Publica só metadados; jamais executa código Android nem extrai bytes
proprietários no relatório. O resultado não descreve as colisões Box2D.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile

from analisar_movimento import read_float_va

LIB_PATH = 'lib/arm64-v8a/libcocos2dcpp.so'
SIGNATURE = 'Entity::move(float, float)'
EXPECTED_ADDR = 0xE4A88C
EXPECTED_SIZE = 236
EPS_ADDRS = {'negative_epsilon': 0x1E9854C, 'positive_epsilon': 0x1E98550}
# Checks anchored to observed original instructions. All findings remain local to
# the SHA-256 verified build and must not be generalized to other BarbarQ builds.
PATTERNS = {
    'body_pointer': r'ldr\s+x0,\s*\[x0,\s*#0x28\]',
    'body_state': r'ldrh\s+w8,\s*\[x0,\s*#0x4\]',
    'branch_on_bit5': r'tbz\s+w8,\s*#0x5',
    'body_type': r'ldr\s+w9,\s*\[x0\]',
    'body_type_zero_guard': r'cbz\s+w9',
    'velocity_squared_x': r'fmul\s+s2,\s*s0,\s*s0',
    'velocity_squared_y': r'fmul\s+s3,\s*s1,\s*s1',
    'awake_bit_check': r'tbnz\s+w8,\s*#0x1',
    'awake_bit_write': r'orr\s+w8,\s*w8,\s*#0x2',
    'sleep_time_reset': r'str\s+wzr,\s*\[x0,\s*#0xac\]',
    'velocity_write': r'stp\s+s0,\s*s1,\s*\[x0,\s*#0x40\]',
    'negative_threshold': r'ldr\s+s2,\s*\[x8,\s*#0x54c\]',
    'positive_threshold': r'ldr\s+s3,\s*\[x8,\s*#0x550\]',
    'step_constant': r'fmov\s+s2,\s*#30\.00000000',
    'divide_x': r'fdiv\s+s0,\s*s0,\s*s2',
    'divide_y': r'fdiv\s+s1,\s*s1,\s*s2',
    'position_read': r'ldur\s+x8,\s*\[x0,\s*#0xc\]',
    'x_position_add': r'fadd\s+s0,\s*s0,\s*s2',
    'y_position_add': r'fadd\s+s0,\s*s1,\s*s0',
    'angle_read': r'ldr\s+s0,\s*\[x0,\s*#0x38\]',
    'set_transform': r'b2Body12SetTransform',
}

def parse_symbol(readelf: str, cxxfilt: str, lib: Path) -> tuple[int, int]:
    proc = subprocess.run([readelf, '-Ws', str(lib)], capture_output=True,
                          text=True, timeout=35, check=True)
    lines = [line for line in proc.stdout.splitlines() if ' FUNC ' in line and '_ZN6Entity4moveEff' in line]
    if len(lines) != 1:
        raise ValueError('Símbolo Entity::move não identificado de forma única')
    fields = lines[0].split()
    # ELF readelf output format: Num Value Size Type Bind Vis Ndx Name
    if len(fields) < 8 or fields[3] != 'FUNC':
        raise ValueError('Registro de símbolo ELF malformado')
    address, size = int(fields[1], 16), int(fields[2])
    if (address, size) != (EXPECTED_ADDR, EXPECTED_SIZE):
        raise ValueError('Endereço/tamanho de Entity::move inesperado')
    demangled = subprocess.run([cxxfilt, fields[-1].split('@')[0]], capture_output=True,
                               text=True, timeout=15, check=True).stdout.strip()
    if demangled != SIGNATURE:
        raise ValueError('Assinatura Entity::move não corresponde à versão esperada')
    return address, size

def audit(apk: Path, manifest: Path, objdump: str, readelf: str, cxxfilt: str) -> dict:
    known = json.loads(manifest.read_text(encoding='utf-8'))
    expected_hash = next(x['sha256'] for x in known['libraries'] if x['name'] == 'libcocos2dcpp.so')
    with ZipFile(apk) as z:
        info = z.getinfo(LIB_PATH)
        if info.file_size < 1_000_000 or info.file_size > 100_000_000:
            raise ValueError('Biblioteca fora dos limites esperados')
        data = z.read(info)
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_hash:
        raise ValueError('SHA-256 incompatível; outra versão não pode reutilizar estes offsets')
    eps = {k: read_float_va(data, addr) for k, addr in EPS_ADDRS.items()}
    if not (-0.000101 < eps['negative_epsilon'] < -0.000099 and
             0.000099 < eps['positive_epsilon'] < 0.000101):
        raise ValueError('Limiares de movimento inesperados')
    with tempfile.TemporaryDirectory(prefix='barlua-f14-') as tmp:
        lib = Path(tmp) / 'libcocos2dcpp.so'
        lib.write_bytes(data)
        address, size = parse_symbol(readelf, cxxfilt, lib)
        proc = subprocess.run([objdump, '-d', '--demangle', f'--start-address=0x{address:x}',
                              f'--stop-address=0x{address+size:x}', str(lib)],
                              capture_output=True, text=True, timeout=35, check=True)
        asm = proc.stdout
        missing = [key for key, regex in PATTERNS.items() if not re.search(regex, asm)]
        if missing:
            raise ValueError('Padrões ARM64 não encontrados: ' + ', '.join(missing))
        instructions = len(re.findall(r'^\s*[0-9a-f]+:\s+[0-9a-f]{8}\s+', asm, re.M))
        if instructions != EXPECTED_SIZE // 4:
            raise ValueError('Contagem inesperada de instruções no intervalo')
    return {
        'version': '1.0.1811', 'library_sha256': digest,
        'function': SIGNATURE, 'virtual_address': hex(address), 'size_bytes': size,
        'instructions': instructions, 'verified_patterns': len(PATTERNS),
        'float_constants': {**eps, 'transform_divisor': 30.0},
        'body_offsets_hex': {'entity_body': '0x28', 'body_type': '0x0',
                             'state_flags': '0x4', 'position_xy': '0xc',
                             'rotation_angle': '0x38', 'velocity_xy': '0x40',
                             'awake_timer': '0xac'},
        'control_flow': [
            'Bit 5 set: type==0 exits; otherwise stores x/y at b2Body+0x40.',
            'On a nonzero movement when state bit 1 was clear, sets bit 1 and clears timer at +0xac.',
            'Bit 5 clear: x/y smaller than about 0.0001 both in magnitude exits.',
            'Otherwise new_position=old_position+(x/30,y/30), then calls b2Body::SetTransform with the original angle.',
        ],
        'limitations': [
            'State flags and body type are raw values; gameplay meaning requires additional evidence.',
            'This does not implement Box2D stepping, contacts, collisions, velocity integration or network synchronization.',
            'The Lua research model can differ in float32 rounding at threshold boundaries.',
            'Only the SHA-256-verified APK 1.0.1811 is covered.',
        ],
    }

def report_to_lua(report: dict) -> str:
    eps = report['float_constants']
    return ('-- F14: audited ELF constants only; NOT complete physics.\n'
            'return {\n'
            f'  version={json.dumps(report["version"])},\n'
            f'  address={json.dumps(report["virtual_address"])},\n'
            f'  instructions={report["instructions"]},\n'
            f'  patterns={report["verified_patterns"]},\n'
            f'  epsilon_negative={eps["negative_epsilon"]:.12g},\n'
            f'  epsilon_positive={eps["positive_epsilon"]:.12g},\n'
            '  transform_divisor=30,\n}\n')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apk', type=Path, required=True)
    p.add_argument('--manifest', type=Path, default=Path('reports/native_arm64.json'))
    p.add_argument('--out', type=Path, default=Path('reports'))
    args = p.parse_args()
    deps = {}
    for tool in ('llvm-objdump', 'readelf', 'c++filt'):
        deps[tool] = shutil.which(tool)
        if not deps[tool]:
            p.error(f'{tool} não disponível no PATH')
    report = audit(args.apk, args.manifest, deps['llvm-objdump'], deps['readelf'], deps['c++filt'])
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/'entity_move.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (args.out/'entity_move.lua').write_text(report_to_lua(report), encoding='utf-8')
    print('Entity::move verificado:', report['instructions'], 'instruções,', report['verified_patterns'], 'padrões')

if __name__ == '__main__':
    main()
