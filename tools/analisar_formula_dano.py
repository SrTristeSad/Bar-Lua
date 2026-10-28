#!/usr/bin/env python3
"""F24: audit of the observed arithmetic core of CDamageFunction::GetDamageValue.

This verifies a specific, hash-pinned Android ARM64 binary. It never executes the
binary and does not claim to emulate complete damage, targeting or combat.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUNCTION = ('_ZN15CDamageFunction14GetDamageValueEPb', 0xe52950, 1328)
RATIO = ('_ZN16LogicWorkshopMgr13DECIMAL_RATIOE', 0x1e9c570, 4)
PTR_RATIO_RELOCATION = 0x260d360
# Addresses of the key operations; registers and operation order checked below.
OPERATIONS = (
    (0xe52998, 'fcmp', ('s0', '#0.0')),
    (0xe5299c, 'b.pl', ()),  # cache: if nonnegative, return existing result
    (0xe52a04, 'bl', ('GetParamValue',)),
    (0xe52a1c, 'bl', ('GetParamValue',)),
    (0xe52a34, 'bl', ('GetParamValue',)),
    (0xe52a4c, 'bl', ('GetParamValue',)),
    (0xe52a68, 'bl', ('GetParamValue',)),
    (0xe52a80, 'bl', ('GetParamValue',)),
    (0xe52a94, 'mov', ('w3', '#0x64')),
    (0xe52a9c, 'bl', ('__NextInt',)),
    (0xe52aa0, 'fcvtzs', ('w23', 's11')),
    (0xe52ab4, 'fdiv', ('s2', 's12', 's1')),
    (0xe52ab8, 'fdiv', ('s0', 's13', 's1')),
    (0xe52abc, 'fdiv', ('s1', 's14', 's1')),
    (0xe52ac4, 'cmp', ('w24', 'w23')),
    (0xe52acc, 'strb', ('w8', '[x20]')),
    (0xe52ad0, 'fsub', ('s2', 's8', 's2')),
    (0xe52ad8, 'fsub', ('s1', 's8', 's1')),
    (0xe52adc, 'fmul', ('s2', 's10', 's2')),
    (0xe52ae0, 'fcsel', ('s0', 's0', 's8', 'le')),
    (0xe52ae4, 'fsub', ('s2', 's9', 's2')),
    (0xe52ae8, 'fmul', ('s0', 's2', 's0')),
    (0xe52aec, 'fmul', ('s0', 's1', 's0')),
    (0xe52af0, 'str', ('s0', '[x19, #0x68]')),
    (0xe52b08, 'cmp', ('w0', '#0x7')),
    (0xe52b14, 'str', ('w8', '[x19, #0x68]')),
    (0xe52d74, 'ldr', ('s0', '[x19, #0x68]')),
    (0xe52d78, 'fmul', ('s0', 's8', 's0')),
    (0xe52d7c, 'str', ('s0', '[x19, #0x68]')),
)
PARAMETER_OFFSETS = (0x38, 0x40, 0x48, 0x58, 0x50, 0x60)
# These offsets are in the configuration structure. They are NOT numeric damage values.
INSN_RE = re.compile(r'^[ \t]*([0-9a-f]+):[ \t]+[0-9a-f]{8}[ \t]+([a-z][a-z0-9_.]*)[ \t]*(.*)$', re.I | re.M)
SYMBOL_RE = re.compile(r'^\s*\d+:\s*([0-9a-f]+)\s+(\d+)\s+(FUNC|OBJECT)\s+\w+\s+DEFAULT\s+\d+\s+(\S+)', re.M)
LOAD_RE = re.compile(r'^\s*LOAD\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+0x[0-9a-f]+\s+0x([0-9a-f]+)', re.M | re.I)


def run(*args: str) -> str:
    return subprocess.run(args, capture_output=True, check=True, text=True, timeout=45).stdout


def parse_instructions(dump: str) -> dict[int, tuple[str, str]]:
    return {int(address, 16): (op.lower(), rest.strip()) for address, op, rest in INSN_RE.findall(dump)}


def verify_operations(instructions: dict[int, tuple[str, str]]) -> None:
    for address, operation, arguments in OPERATIONS:
        op, operands = instructions.get(address, ('', ''))
        if op != operation or not all(arg in operands for arg in arguments):
            raise ValueError(f'F24: instrução esperada não confere em 0x{address:x} ({operation}): {op} {operands}')
    # Confirm inputs are loaded from the six distinct config offsets.
    for address, offset in zip((0xe529f8, 0xe52a10, 0xe52a28, 0xe52a40, 0xe52a58, 0xe52a74), PARAMETER_OFFSETS):
        op, operands = instructions.get(address, ('', ''))
        if op != 'ldr' or f'[x8, #0x{offset:x}]' not in operands:
            raise ValueError(f'F24: parâmetro ausente ou deslocado em 0x{address:x}')
    if instructions.get(0xe52ac8, ('', ''))[0] != 'cset' or 'le' not in instructions[0xe52ac8][1]:
        raise ValueError('F24: condição da probabilidade alterada')


def find_file_offset(virtual_address: int, elf_segments: str) -> int:
    for match in LOAD_RE.finditer(elf_segments):
        offset, addr, length = (int(v, 16) for v in match.groups())
        if addr <= virtual_address < addr + length:
            return offset + virtual_address - addr
    raise ValueError('F24: endereço da constante fora dos segmentos ELF')


def audit(library: Path, manifest: Path) -> dict:
    reference = json.loads(manifest.read_text('utf-8'))
    expected_hash = next(entry['sha256'] for entry in reference['libraries'] if entry['name'] == 'libcocos2dcpp.so')
    with library.open('rb') as f:
        actual_hash = hashlib.file_digest(f, 'sha256').hexdigest()
    if actual_hash != expected_hash:
        raise ValueError('F24: SHA-256 da biblioteca incompatível com BarbarQ 1.0.1811')
    symbols = {(int(a, 16), int(size), kind, name) for a, size, kind, name
               in SYMBOL_RE.findall(run('readelf', '-Ws', str(library)))}
    for name, address, size, kind in ((*FUNCTION, 'FUNC'), (*RATIO, 'OBJECT')):
        if (address, size, kind, name) not in symbols:
            raise ValueError(f'F24: símbolo mudou: {name}')
    relocations = run('readelf', '-Wr', str(library))
    target_reloc = next((line for line in relocations.splitlines()
                         if line.lstrip().lower().startswith(f'{PTR_RATIO_RELOCATION:016x}')), '')
    if RATIO[0] not in target_reloc:
        raise ValueError('F24: referência ao divisor não confirmada')
    image = library.read_bytes()
    ratio_file_offset = find_file_offset(RATIO[1], run('readelf', '-lW', str(library)))
    ratio = struct.unpack_from('<f', image, ratio_file_offset)[0]
    if ratio != 100.0:
        raise ValueError('F24: divisor percentual mudou; recusar interpretação')
    start, size = FUNCTION[1], FUNCTION[2]
    dump = run('llvm-objdump', '-d', f'--start-address=0x{start:x}',
               f'--stop-address=0x{start + size:x}', str(library))
    insns = parse_instructions(dump)
    if set(insns) != set(range(start, start + size, 4)):
        raise ValueError('F24: desmontagem incompleta')
    verify_operations(insns)
    return {
        'phase': 24, 'apk_version': '1.0.1811', 'library_sha256': actual_hash,
        'function': FUNCTION[0], 'address': f'0x{start:x}',
        'function_instructions': len(insns),
        'percent_ratio_symbol': RATIO[0], 'percent_ratio': ratio,
        'parameter_offsets': [f'0x{x:x}' for x in PARAMETER_OFFSETS],
        'parameter_names': ['A', 'B', 'chance_threshold', 'C', 'D_percent', 'E'],
        'arithmetic_core': '(A - B * (1 - C / ratio)) * (roll <= trunc(chance_threshold) ? D_percent / ratio : 1) * (1 - E / ratio)',
        'observed_random_args': {'arg1': 0, 'arg2': 1, 'arg3': 100},
        'verified_operations': len(OPERATIONS),
        'cached_nonnegative_result': True,
        'map_type_seven_special_branch': True,
        'additional_target_modifier': True,
        'limitations': ('Somente o núcleo aritmético de um ramo de GetDamageValue foi reconstituído. '
                        'Não são conhecidos os valores concretos dos parâmetros para a habilidade 4010020, '
                        'a distribuição do RNG, os modificadores de alvo, o arredondamento final nem o vínculo '
                        'com o ataque básico. Não usar para infligir dano em jogo.'),
    }


def export_lua(report: dict) -> str:
    # No game execution: metadata, numeric ratio, documentation only.
    return ('-- Fase 24: fórmula PARCIAL, dados verificados (não simula combate)\n'
            'return {\n'
            '  name="CDamageFunction::GetDamageValue",\n'
            f'  address={json.dumps(report["address"])},\n'
            f'  instructions={report["function_instructions"]},\n'
            f'  ratio={report["percent_ratio"]:g},\n'
            f'  checked={report["verified_operations"]},\n'
            '  input_offsets={"0x38","0x40","0x48","0x58","0x50","0x60"},\n'
            '  limitations="Ramo aritmetico parcial; nao e formula final de dano.",\n'
            '}\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--library', type=Path, default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    p.add_argument('--manifest', type=Path, default=ROOT/'reports/native_arm64.json')
    p.add_argument('--report', type=Path, default=ROOT/'reports/damage_math.json')
    p.add_argument('--lua', type=Path, default=ROOT/'reports/damage_math.lua')
    args = p.parse_args()
    result = audit(args.library, args.manifest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.lua.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    args.lua.write_text(export_lua(result), encoding='utf-8')
    print(f'F24: {result["function_instructions"]} instruções, {result["verified_operations"]} operações verificadas, ratio={result["percent_ratio"]}')

if __name__ == '__main__':
    main()
