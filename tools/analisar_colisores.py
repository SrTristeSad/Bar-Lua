#!/usr/bin/env python3
"""Bar-Lua F16: verifica inicialização de corpos e fixtures no APK original.

A análise é estática, vinculada ao SHA-256 da libcocos2dcpp.so. Não
executa código nativo, não reconstrói colisões e não publica os binários.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile

MEMBER = 'lib/arm64-v8a/libcocos2dcpp.so'
SIGNATURES = {
    'Entity::InitB2Body(b2Vec2 const&, bool)': (0xE47AC0, 204),
    'Entity::InitCollision(config::hero::CollisionConfig const*)': (0xE47B8C, 984),
}
# Um padrão que não bater é um erro de validação: não inferir a semântica.
PATTERNS = {
    'Entity::InitB2Body(b2Vec2 const&, bool)': {
        'existing_body_guard': r'ldr\s+x0,\s*\[x20,\s*#0x28\]',
        'creates_world_body': r'bl\s+[^\n]*b2World10CreateBody',
        'stores_body': r'str\s+x0,\s*\[x20,\s*#0x28\]',
        'static_override': r'bl\s+[^\n]*b2Body7SetType',
        'converts_xy': r'fdiv\s+s1,\s*s1,\s*s0[\s\S]*?fdiv\s+s0,\s*s2,\s*s0',
        'body_dynamic_type': r'str\s+w8,\s*\[sp,\s*#0x8\]',
    },
    'Entity::InitCollision(config::hero::CollisionConfig const*)': {
        'null_config_guard': r'cbz\s+x1,\s*0xe47f34',
        'shape_type_3': r'cmp\s+w8,\s*#0x3',
        'shape_type_2': r'cmp\s+w8,\s*#0x2',
        'shape_type_1': r'cmp\s+w8,\s*#0x1',
        'circle_fixture': r'bl\s+[^\n]*b2Body13CreateFixture',
        'polygon_vertices': r'bl\s+[^\n]*b2PolygonShape3Set',
        'custom_polygons': r'bl\s+[^\n]*CustomShapeUtils25GenPolygonsForCustomShape',
        'fixed_rotation': r'bl\s+[^\n]*b2Body16SetFixedRotation',
        'assign_user_data': r'str\s+x19,\s*\[x0,\s*#0xb0\]',
        'rectangle_width_read': r'ldr\s+w9,\s*\[x8,\s*#0x8\]',
        'rectangle_height_read': r'ldr\s+w8,\s*\[x8,\s*#0xc\]',
        'custom_shape_scale': r'bl\s+[^\n]*GenPolygonsForCustomShape',
    },
}
INSTRUCTION = re.compile(r'^\s*([\da-f]+):\s+[\da-f]{8}\s+([a-z][\w.]*)\b', re.I | re.M)


def elf_va_float(elf: bytes, va: int) -> float:
    """Read a float from a PT_LOAD mapping, never presume file offset == VA."""
    if elf[:4] != b'\x7fELF' or elf[4] != 2 or elf[5] != 1 or len(elf) < 64:
        raise ValueError('ELF64 little-endian requerido')
    phoff = struct.unpack_from('<Q', elf, 32)[0]
    entsize, count = struct.unpack_from('<HH', elf, 54)
    if entsize < 56 or count > 1024 or phoff + count * entsize > len(elf):
        raise ValueError('Tabela de segmentos ELF invalida')
    for i in range(count):
        kind, flags, offset, vaddr, _, filesz, _, _ = struct.unpack_from('<IIQQQQQQ', elf, phoff + entsize*i)
        if kind == 1 and vaddr <= va and va + 4 <= vaddr + filesz:
            pos = offset + va - vaddr
            if pos + 4 > len(elf):
                raise ValueError('Valor ELF fora do arquivo')
            return struct.unpack_from('<f', elf, pos)[0]
    raise ValueError(f'Constante VA 0x{va:x} nao mapeada')


def symbol_table(so: Path, readelf='readelf', cxxfilt='c++filt') -> dict:
    lines = subprocess.run([readelf, '-Ws', str(so)], check=True, text=True,
                           capture_output=True, timeout=45).stdout.splitlines()
    selected = []
    for line in lines:
        columns = line.split()
        if len(columns) >= 8 and columns[3] == 'FUNC' and columns[6] != 'UND':
            if columns[7].startswith(('_ZN6Entity10InitB2Body', '_ZN6Entity13InitCollision')):
                selected.append((columns[7].split('@')[0], int(columns[1],16), int(columns[2])))
    proc = subprocess.run([cxxfilt], input='\n'.join(x[0] for x in selected)+'\n',
                          check=True, capture_output=True, text=True, timeout=15)
    names = proc.stdout.splitlines()
    if len(names) != len(selected):
        raise ValueError('Falha na identificação de assinaturas C++')
    result = {name:(addr,size) for name,(_,addr,size) in zip(names,selected)}
    if set(result) != set(SIGNATURES):
        raise ValueError(f'Funções não encontradas: {set(SIGNATURES)-set(result)}')
    for name, expected in SIGNATURES.items():
        if result[name] != expected:
            raise ValueError(f'Endereço/tamanho divergente: {name}')
    return result


def audit(so_file: Path, manifest: Path, objdump='llvm-objdump', readelf='readelf', cxxfilt='c++filt') -> dict:
    blob = so_file.read_bytes()
    meta = json.loads(manifest.read_text(encoding='utf-8'))
    expected = next(entry['sha256'] for entry in meta['libraries'] if entry['name'] == 'libcocos2dcpp.so')
    digest = hashlib.sha256(blob).hexdigest()
    if digest != expected:
        raise ValueError('Hash divergente: offsets não se aplicam a esta versão')
    constants = {
        'body_position_divisor': elf_va_float(blob, 0x1E98098),
        'polygon_x_negative_scale': elf_va_float(blob, 0x1E9A098),
        'polygon_x_positive_scale': elf_va_float(blob, 0x1E9A09C),
    }
    if constants != {'body_position_divisor':100.0, 'polygon_x_negative_scale':-0.004999999888241291,
                     'polygon_x_positive_scale':0.004999999888241291}:
        raise ValueError('Constantes inesperadas nos offsets verificados')
    observed = []
    discovered = symbol_table(so_file,readelf,cxxfilt)
    for name in SIGNATURES:
        address,size=discovered[name]
        proc = subprocess.run([objdump,'-d','--demangle',f'--start-address=0x{address:x}',
                              f'--stop-address=0x{address+size:x}',str(so_file)],
                              check=True, text=True, capture_output=True, timeout=45)
        instr = [(int(m[1],16),m[2]) for m in INSTRUCTION.finditer(proc.stdout)]
        if [x[0] for x in instr] != list(range(address,address+size,4)):
            raise ValueError(f'Código ARM64 incompleto: {name}')
        tests = PATTERNS[name]
        absent = [k for k,pattern in tests.items() if not re.search(pattern, proc.stdout)]
        if absent:
            raise ValueError(f'Instruções ausentes em {name}: {absent}')
        observed.append({'name':name,'address':f'0x{address:x}', 'size_bytes':size,
                         'instructions':len(instr),'checks':sorted(tests)})
    return {'phase':16, 'version':'1.0.1811','library_sha256':digest,
            'disclaimer':'Achados de análise estática. Não implementa física nem confirma fidelidade visual.',
            'constants':constants,
            'functions':observed,
            'findings':[
                'InitB2Body evita recriar corpo quando ponteiro existente não é nulo; senão chama b2World::CreateBody.',
                'InitB2Body divide coordenadas iniciais por 100.0 (constante ELF verificada).',
                'InitB2Body possui desvio para b2Body::SetType quando o argumento booleano é verdadeiro.',
                'InitCollision testa códigos 1, 2 e 3, chegando respectivamente a fixture circular, polígono de quatro vértices e geração de polígonos personalizada.',
                'Os caminhos de fixture observados associam a Entity ao userData do corpo e invocam SetFixedRotation.',
                'Os caminhos de configuração e flags são condicionais; a análise não recupera filtros/máscaras e contatos completos.',
            ]}


def export_lua(result:dict) -> str:
    def string(s): return json.dumps(s,ensure_ascii=False)
    lines=['-- F16, metadados estáticos auditados; sem código nativo original.', 'return {']
    for e in result['functions']:
        lines.append('  {name=%s,address=%s,instructions=%d,checks=%d},' %
                     (string(e['name']), string(e['address']), e['instructions'], len(e['checks'])))
    lines.append('}')
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--so',type=Path,default=Path('lib/arm64-v8a/libcocos2dcpp.so'))
    parser.add_argument('--manifest',type=Path,default=Path('reports/native_arm64.json'))
    parser.add_argument('--out',type=Path,default=Path('reports/native_colliders.json'))
    parser.add_argument('--lua',type=Path,default=Path('reports/native_colliders.lua'))
    args=parser.parse_args()
    report=audit(args.so,args.manifest)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.lua.write_text(export_lua(report),encoding='utf-8')
    print(f"F16: {len(report['functions'])} funções, {sum(x['instructions'] for x in report['functions'])} instruções; SHA-256 validado.")

if __name__=='__main__': main()
