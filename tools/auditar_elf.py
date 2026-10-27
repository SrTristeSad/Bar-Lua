#!/usr/bin/env python3
"""Auditoria estática, reproduzível, das bibliotecas ARM64 de um APK local.

Não executa bibliotecas Android e não inclui nem publica seu conteúdo binário.
Requer readelf e c++filt (binutils/LLVM, por exemplo via WSL/MSYS2).
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
from zipfile import ZipFile

CLASSES = (
    'GameScene', 'BattleNet', 'BattleManager', 'BattleFieldController',
    'GameLayer', 'Hero', 'CSkill', 'CSkillEntity', 'CMoveEdge',
    'ViewMoveEdge', 'BattleDataManager', 'UILayer',
)
KEYWORDS = ('frame', 'update', 'process', 'sync', 'move', 'skill', 'attack',
            'damage', 'entity', 'input', 'operate', 'direction', 'hero',
            'create', 'handle', 'stick', 'command', 'send', 'init')
SYMBOL_PATTERN = re.compile(r'^\s*\d+:\s+([0-9a-fA-F]+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)')
MAX_SO_SIZE = 100 * 1024 * 1024

def verify_elf_header(data: bytes) -> None:
    if len(data) < 64 or data[:4] != b'\x7fELF':
        raise ValueError('Não é um ELF válido')
    if data[4] != 2 or data[5] != 1:
        raise ValueError('Esperado ELF64 little-endian')
    if struct.unpack_from('<H', data, 18)[0] != 183:
        raise ValueError('Esperado ARM64/AArch64 (e_machine=183)')

def parse_dynamic_symbols(output: str) -> list[dict]:
    result = []
    for line in output.splitlines():
        match = SYMBOL_PATTERN.match(line)
        if not match:
            continue
        address, size, kind, binding, visibility, section, name = match.groups()
        if name == '' or name.startswith('('):
            continue
        result.append({'address': '0x' + address.lstrip('0').lower() if int(address,16) else '0x0',
                       'size': int(size), 'kind': kind, 'binding': binding,
                       'section': section, 'name': name})
    return result

def parse_needed(output: str) -> list[str]:
    return sorted(set(re.findall(r'\(NEEDED\).*?\[(.*?)\]', output)))

def run_tool(args: list[str], *, stdin: str | None = None) -> str:
    cmd = subprocess.run(args, input=stdin, capture_output=True, text=True,
                         encoding='utf-8', errors='replace', timeout=120, check=True)
    return cmd.stdout

def demangle(symbols: list[str], filt: str) -> dict[str, str]:
    if not symbols:
        return {}
    out = run_tool([filt], stdin='\n'.join(symbols) + '\n').splitlines()
    if len(out) != len(symbols):
        raise ValueError('c++filt não preservou a quantidade de símbolos')
    return dict(zip(symbols, out))

def ranking(signature: str) -> tuple:
    lower = signature.lower()
    score = sum(1 for term in KEYWORDS if term in lower)
    if '::~' in signature or signature.split('::')[0] + '::' + signature.split('::')[0] + '(' in signature:
        score -= 5
    return (-score, signature)

def analyze(apk: Path, readelf: str, filt: str):
    libs = []
    samples = {}
    with ZipFile(apk) as z, tempfile.TemporaryDirectory(prefix='barlua-arm64-') as tmp:
        entries = sorted((i for i in z.infolist() if re.fullmatch(r'lib/arm64-v8a/[^/]+\.so', i.filename)),
                         key=lambda i: i.filename)
        if not entries:
            raise ValueError('APK não contém lib/arm64-v8a/*.so')
        if len(entries) > 30:
            raise ValueError('Quantidade de bibliotecas inesperada')
        for info in entries:
            if info.file_size > MAX_SO_SIZE:
                raise ValueError('Biblioteca maior que limite de segurança')
            data = z.read(info)
            verify_elf_header(data)
            path = Path(tmp) / Path(info.filename).name
            path.write_bytes(data)
            syms = parse_dynamic_symbols(run_tool([readelf, '--dyn-syms', '-W', str(path)]))
            needed = parse_needed(run_tool([readelf, '-d', '-W', str(path)]))
            library = dict(name=path.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                           dynamic_symbol_entries=len(syms), defined_functions=sum(
                               s['kind']=='FUNC' and s['section'] != 'UND' for s in syms),
                           needed=needed)
            libs.append(library)
            if path.name == 'libcocos2dcpp.so':
                selected = []
                for sym in syms:
                    if sym['section'] == 'UND' or sym['kind'] != 'FUNC' or not sym['name'].startswith('_Z'):
                        continue
                    if any(sym['name'].startswith(prefix + str(len(cl)) + cl)
                           for cl in CLASSES for prefix in ('_ZN', '_ZNK')):
                        selected.append(sym)
                unique = list(dict.fromkeys(s['name'] for s in selected))
                decoded = demangle(unique, filt)
                for sym in selected:
                    signature = decoded[sym['name']]
                    for cl in CLASSES:
                        if signature.startswith(cl + '::'):
                            samples.setdefault(cl, []).append({
                                'signature': signature, 'address': sym['address'],
                                'bytes': sym['size'], 'mangled': sym['name']})
                            break
    if not samples:
        raise ValueError('Nenhum símbolo alvo exportado pela biblioteca principal')
    for cl in samples:
        samples[cl].sort(key=lambda e: (ranking(e['signature']), e['address']))
    report = {
        'origin': 'APK fornecido pelo usuário; análise estática de .dynsym',
        'apk_filename': apk.name,
        'apk_sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
        'architecture': 'ELF64 AArch64 little-endian',
        'interpretation': ('Símbolos exportados comprovam a existência das funções com esses nomes; '
                           'não comprovam o comportamento, algoritmo, fórmulas, argumentos em uso ou taxa de atualização.'),
        'libraries': libs,
        'focus_classes': {cl: {'count': len(samples.get(cl, [])),
                               'sample': samples.get(cl, [])[:12]} for cl in CLASSES},
    }
    return report, samples

def lua_escape(s: str) -> str:
    return json.dumps(s, ensure_ascii=True)

def write_reports(outdir: Path, report: dict, samples: dict):
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / 'native_arm64.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (outdir / 'native_symbols.csv').open('w', encoding='utf-8', newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['class','signature','virtual_address','size_bytes','mangled'])
        for cl in CLASSES:
            for rec in samples.get(cl, []):
                writer.writerow([cl,rec['signature'],rec['address'],rec['bytes'],rec['mangled']])
    lua = ['-- Metadados de auditoria estática; não executa bibliotecas nativas.', 'return {']
    for cl in CLASSES:
        entry = report['focus_classes'][cl]
        lua.append('  {name=' + lua_escape(cl) + ', count=' + str(entry['count']) + ', methods={')
        for symbol in entry['sample']:
            lua.append('    {signature=' + lua_escape(symbol['signature']) + ', address=' +
                       lua_escape(symbol['address']) + ', bytes=' + str(symbol['bytes']) + '},')
        lua.append('  }},')
    lua.append('}')
    (outdir / 'native_findings.lua').write_text('\n'.join(lua) + '\n', encoding='utf-8')

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('apk', type=Path, help='Cópia local do APK BarbarQ (nenhum upload ou execução)')
    p.add_argument('--out', type=Path, default=Path('reports'))
    args=p.parse_args()
    readelf=shutil.which('readelf') or shutil.which('llvm-readelf')
    filt=shutil.which('c++filt') or shutil.which('llvm-cxxfilt')
    if not readelf or not filt:
        p.error('readelf e c++filt necessários (Binutils ou LLVM/WSL)')
    report, samples=analyze(args.apk, readelf, filt)
    write_reports(args.out, report, samples)
    print('ELF ARM64:', len(report['libraries']), 'bibliotecas')
    for lib in report['libraries']:
        print(' ', lib['name'], lib['dynamic_symbol_entries'], 'símbolos dinâmicos,',lib['defined_functions'],'funções definidas')
    print('Métodos selecionados:', sum(map(len, samples.values())))
    print('Relatórios:', args.out.resolve())
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
