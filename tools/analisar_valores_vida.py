#!/usr/bin/env python3
"""F25: audit pinned ARM64 entity value dispatch and Hero HP bookkeeping.

This is a **static** evidence catalog for the user's BarbarQ 1.0.1811 ELF,
not an executable transplant or a complete combat simulation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = {
    'Entity::getValueByType (contextual)': ('_ZN6Entity14getValueByTypeEN6config5skill9ValueTypeEfPKS_PK6CSkillPKNS1_9OperationE', 0xE45D5C, 352),
    'Entity::getValueByType (const)': ('_ZNK6Entity14getValueByTypeEN6config5skill9ValueTypeEfPKNS1_9OperationE', 0xE49AFC, 368),
    'Hero::addHurtFromEnemy': ('_ZN4Hero16addHurtFromEnemyEiib', 0xE57678, 356),
}
# ARM64 virtual addresses of observed instructions; keep operands restricted enough
# that a different binary/control flow is rejected instead of silently assumed.
CHECKS = {
    'Entity::getValueByType (contextual)': (
        (0xE45D80, 'cmp', ('w8', '#0x3e7')),
        (0xE45D9C, 'ldr', ('x4', '[x9, #0x70]')),
        (0xE45DC0, 'ldp', ('x20', 'x19')),
        (0xE45DD0, 'fdiv', ('s0', 's0', 's1')),
        (0xE45DD4, 'cmp', ('w8', '#0x3eb')),
        (0xE45DEC, 'cmp', ('w8', '#0x3ea')),
        (0xE45E10, 'ldr', ('w8', '[x2, #0x14]')),
        (0xE45E14, 'cmp', ('w9', '#0x3')),
        (0xE45E3C, 'fadd', ('s0', 's0', 's1')),
        (0xE45E80, 'fsub', ('s0', 's0', 's1')),
        (0xE45E88, 'fmul', ('s0', 's0', 's1')),
        (0xE45E90, 'fcmp', ('s1', '#0.0')),
        (0xE45E98, 'fdiv', ('s0', 's0', 's1')),
    ),
    'Entity::getValueByType (const)': (
        (0xE49B1C, 'fdiv', ('s8', 's0', 's9')),
        (0xE49B20, 'cmp', ('w1', '#0x64')),
        (0xE49B28, 'sub', ('w8', 'w1', '#0x4')),
        (0xE49BA4, 'sub', ('w8', 'w1', '#0x65')),
        (0xE49BA8, 'cmp', ('w8', '#0x14')),
        (0xE49BB4, 'ldr', ('s0', '[x8, #0xec]')),
        (0xE49BC8, 'cmp', ('w8', '#0x3')),
        (0xE49BF0, 'fadd', ('s8', 's8', 's0')),
        (0xE49BF8, 'fsub', ('s8', 's8', 's0')),
        (0xE49C00, 'fmul', ('s8', 's8', 's0')),
        (0xE49C08, 'fcmp', ('s0', '#0.0')),
        (0xE49C10, 'fdiv', ('s8', 's8', 's0')),
        (0xE49C64, 'fmov', ('s8', '#-1.00000000')),
    ),
    'Hero::addHurtFromEnemy': (
        (0xE57690, 'mov', ('w19', 'w3')),
        (0xE57694, 'mov', ('w22', 'w2')),
        (0xE576AC, 'ldr', ('w23', '[x20, #0x314]')),
        (0xE576B4, 'cmp', ('w23', '#0x1')),
        (0xE576BC, 'subs', ('w8', 'w23', 'w21')),
        (0xE576C0, 'b.le', ('0xe576cc',)),
        (0xE576C4, 'str', ('w8', '[x20, #0x314]')),
        (0xE576D0, 'str', ('wzr', '[x20, #0x314]')),
        (0xE576D4, 'str', ('w22', '[x20, #0x370]')),
        (0xE576E4, 'mov', ('w21', 'w23')),
        (0xE57710, 'add', ('w8', 'w8', 'w21')),
        (0xE57714, 'str', ('w8', '[x0]')),
        (0xE57720, 'bl', ('findEntityByKey',)),
        (0xE57760, 'add', ('w8', 'w8', 'w21')),
        (0xE57764, 'str', ('w8', '[x0, #0x4]')),
        (0xE5779C, 'bl', ('LogicEventSet',)),
        (0xE577A0, 'tbz', ('w19', '#0x0')),
        (0xE577B0, 'bl', ('breakCombo',)),
    ),
}
INSN = re.compile(r'^[ \t]*([0-9a-f]+):[ \t]+[0-9a-f]{8}[ \t]+([a-z][a-z0-9_.]*)[ \t]*(.*)$', re.I | re.M)
SYMBOL = re.compile(r'^\s*\d+:\s*([0-9a-f]+)\s+(\d+)\s+FUNC\s+\w+\s+DEFAULT\s+\d+\s+(\S+)', re.M)


def command(*args: str) -> str:
    return subprocess.run(args, capture_output=True, check=True, text=True, timeout=45).stdout


def instructions(text: str) -> dict[int, tuple[str, str]]:
    return {int(addr, 16): (op.lower(), operands.strip()) for addr, op, operands in INSN.findall(text)}


def check_instructions(label: str, decoded: dict[int, tuple[str, str]]) -> None:
    _, start, size = FUNCTIONS[label]
    required = set(range(start, start + size, 4))
    if set(decoded) != required:
        raise ValueError(f'F25: desmontagem incompleta para {label}')
    for address, opcode, operands in CHECKS[label]:
        actual_op, actual_args = decoded.get(address, ('', ''))
        if opcode != actual_op or not all(s in actual_args for s in operands):
            raise ValueError(f'F25: instrução divergente {label} 0x{address:x}: {actual_op} {actual_args}')


def audit(library: Path, manifest: Path) -> dict:
    data = json.loads(manifest.read_text(encoding='utf-8'))
    reference = next(item['sha256'] for item in data['libraries'] if item['name'] == 'libcocos2dcpp.so')
    with library.open('rb') as fd:
        digest = hashlib.file_digest(fd, 'sha256').hexdigest()
    if digest != reference:
        raise ValueError('F25: SHA-256 incompatível com a biblioteca original 1.0.1811')
    symbols = {(name, int(address, 16), int(size)) for address, size, name in
               SYMBOL.findall(command('readelf', '-Ws', str(library)))}
    findings = []
    for label, (symbol, start, size) in FUNCTIONS.items():
        if (symbol, start, size) not in symbols:
            raise ValueError(f'F25: símbolo original ausente: {label}')
        decoded = instructions(command('llvm-objdump', '-d',
                    f'--start-address=0x{start:x}', f'--stop-address=0x{start+size:x}', str(library)))
        check_instructions(label, decoded)
        findings.append({'name': label, 'symbol': symbol, 'address': f'0x{start:x}',
                         'bytes': size, 'instructions': len(decoded), 'checks': len(CHECKS[label])})
    return {
        'phase': 25, 'apk_version': '1.0.1811', 'library_sha256': digest,
        'functions': findings,
        'total_instructions': sum(f['instructions'] for f in findings),
        'total_checks': sum(f['checks'] for f in findings),
        'hp_observations': {
            'hp_offset': '0x314', 'attacker_key_offset_on_lethal': '0x370',
            'hp_branch': 'Se HP atual >= 1 e (HP - dano) > 0: armazena HP - dano. Caso contrario, se HP >= 1: armazena 0, armazena identificador do agressor, chama callback virtual e limita o dano contabilizado ao HP anterior.',
            'accounting': 'Se existirem registros apropriados, incrementa dano recebido e, quando a entidade atacante for localizada, dano infligido pelo valor efetivamente contabilizado.',
            'events': 'Se atacante existe, emite evento; flag de entrada pode interromper combo, sem comprovar outros efeitos.',
        },
        'value_observations': {
            'ratio': 'A divisão por constante percentual ocorre nas duas variantes; constante 100.0 comprovada separadamente na F24.',
            'contextual_special_types': [1002, 1003],
            'operation_types': [0, 1, 2, 3],
            'operation_zero_divisor': 'Divisão ignorada quando o divisor comparado é zero.',
            'const_entity_stat_range': [101, 120],
        },
        'limits': 'O simulador demonstra somente a subtração de HP para herói vivo e dano inteiro não negativo. Não executa callbacks virtuais, eventos, estatísticas, efeitos, IA ou morte real. A cadeia de 4010020 para GetDamageValue permanece sem prova.',
    }


def lua_catalog(report: dict) -> str:
    parts = ['-- F25: evidências estáticas do ELF original, não executa combate', 'return {',
             '  version="1.0.1811",',
             f'  total_instructions={report["total_instructions"]},',
             f'  total_checks={report["total_checks"]},',
             '  functions={']
    for row in report['functions']:
        parts.append('    {name=%s,address=%s,instructions=%d,checks=%d},' %
                     (json.dumps(row['name']), json.dumps(row['address']), row['instructions'], row['checks']))
    parts += ['  },', '  hp_offset="0x314",', '  last_attacker_offset="0x370",',
              '  supported_scope="modelo isolado de HP; nao altera jogo",', '}']
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--library', type=Path, default=ROOT/'lib/arm64-v8a/libcocos2dcpp.so')
    parser.add_argument('--manifest', type=Path, default=ROOT/'reports/native_arm64.json')
    parser.add_argument('--report', type=Path, default=ROOT/'reports/entity_damage_flow.json')
    parser.add_argument('--lua', type=Path, default=ROOT/'reports/entity_damage_flow.lua')
    args = parser.parse_args()
    report = audit(args.library, args.manifest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.lua.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    args.lua.write_text(lua_catalog(report), encoding='utf-8')
    print('F25: %d funções, %d instruções, %d checkpoints ARM64 verificados' %
          (len(report['functions']), report['total_instructions'], report['total_checks']))

if __name__ == '__main__':
    main()
